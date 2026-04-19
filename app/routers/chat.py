import os
import json
from datetime import date
from fastapi import APIRouter, Depends, HTTPException

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent

from app.schemas import ChatRequest, ChatResponse, ToolCallInfo, ChatMessage
from app.database import get_service_client
from app.auth_utils import get_current_user
from app.agent_tools import build_tools

router = APIRouter()

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=os.environ.get("OPENAI_API_KEY", ""),
)

SYSTEM_TEMPLATE = """You are a nutrition logging assistant for the user's personal macro tracker.

User's daily goals: {cal}kcal, {pro}g protein, {carb}g carbs, {fat}g fat.
Today's date: {today}.
Food library (saved favorites): {library}
Today's log so far: {log}

You have tools to log/modify/remove food entries, manage the food library, and update goals.

Guidelines:
- When the user describes food they ate, call `log_food` (one call per distinct item).
- Prefer nutrition values from the library when a close match exists; otherwise estimate from general knowledge.
- For past-date operations, first call `list_log_entries` with that date to get ids.
- Only call `update_goals` when the user explicitly asks to change their goals.
- Be brief and specific. Do not repeat raw tool output verbatim; summarize.

Image handling:
- The user may attach images of food (meals, snacks, packaging) or nutrition labels.
- For a food photo: identify each distinct item, estimate a reasonable portion size, and estimate macros per item using general nutrition knowledge.
- For a nutrition label: read the serving size and macros directly from the label; use those exact values (scale by qty if the user indicates multiple servings).
- If the user's intent is clear ("log this", "I ate this for lunch", "save this for later") act immediately: call `log_food` for each item, or `add_food_to_library` to save a reusable entry.
- If intent is ambiguous (just an image with no context), briefly summarize what you see and your macro estimate, then ask whether to log it (and for which meal) or save it to the library.
- If the image isn't food-related, say so and don't call any tools."""


def _to_lc(m: ChatMessage):
    role = (m.role or "").lower()
    if role in ("user", "human"):
        return HumanMessage(content=m.content)
    return AIMessage(content=m.content)


def _load_context(sb, user_id: str):
    goals_res = sb.table("goals").select("*").eq("user_id", user_id).execute()
    goals = goals_res.data[0] if goals_res.data else {"cal": 2000, "pro": 160, "carb": 180, "fat": 71}

    lib = sb.table("food_library").select(
        "name, cal, pro, carb, fat, unit"
    ).eq("user_id", user_id).execute().data

    log = (
        sb.table("food_log")
        .select("id, name, meal, cal, pro, carb, fat, qty")
        .eq("user_id", user_id)
        .eq("log_date", str(date.today()))
        .order("created_at")
        .execute()
        .data
    )
    return goals, lib, log


def _stringify_args(tool_input):
    if isinstance(tool_input, dict):
        return tool_input
    return {"input": str(tool_input)}


@router.post("/", response_model=ChatResponse)
def chat(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    sb = get_service_client()
    user_id = current_user["user_id"]

    goals, library, today_log = _load_context(sb, user_id)
    system_prompt = SYSTEM_TEMPLATE.format(
        cal=goals["cal"], pro=goals["pro"], carb=goals["carb"], fat=goals["fat"],
        today=str(date.today()),
        library=json.dumps(library),
        log=json.dumps(today_log),
    )

    ctx = {"mutated": False}
    tools = build_tools(sb, user_id, ctx)

    agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)

    messages = [_to_lc(m) for m in body.history]

    # Build the current user turn. If images are attached, send a multimodal
    # HumanMessage so GPT-4o can actually see them.
    if body.images:
        parts: list = []
        text = (body.message or "").strip()
        # The model handles empty text fine, but include a neutral hint so
        # the tool-calling agent still gets a clear instruction.
        parts.append({
            "type": "text",
            "text": text or "Please analyze the attached image(s).",
        })
        for url in body.images:
            if not url:
                continue
            parts.append({
                "type": "image_url",
                "image_url": {"url": url},
            })
        messages.append(HumanMessage(content=parts))
    else:
        messages.append(HumanMessage(content=body.message))

    try:
        result = agent.invoke(
            {"messages": messages},
            config={"recursion_limit": 16},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent failed: {e}")

    out_messages = result.get("messages", [])

    # Pair each AIMessage tool_call with its ToolMessage observation by id.
    tool_results: dict[str, str] = {
        m.tool_call_id: str(m.content)
        for m in out_messages
        if isinstance(m, ToolMessage)
    }
    tool_calls: list[ToolCallInfo] = []
    for m in out_messages:
        if isinstance(m, AIMessage):
            for tc in (m.tool_calls or []):
                tool_calls.append(ToolCallInfo(
                    name=tc["name"],
                    args=_stringify_args(tc.get("args", {})),
                    result=tool_results.get(tc.get("id", ""), ""),
                ))

    reply = ""
    for m in reversed(out_messages):
        if isinstance(m, AIMessage) and m.content:
            reply = m.content if isinstance(m.content, str) else str(m.content)
            break

    return ChatResponse(
        reply=reply,
        mutated=ctx["mutated"],
        tool_calls=tool_calls,
    )
