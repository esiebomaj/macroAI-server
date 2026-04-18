import os
import json
import re
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from app.schemas import ChatRequest, ChatResponse, LogEntryResponse
from app.database import get_service_client
from app.auth_utils import get_current_user

router = APIRouter()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

SYSTEM_TEMPLATE = """You are a nutrition logging assistant. User's daily goals: {cal}kcal, {pro}g protein, {carb}g carbs, {fat}g fat.
Food library: {library}.
Today's log: {log}.
If the user wants to log food, append a JSON block at the END of your message:
```log
[{{"name":"Food","meal":"Breakfast|Lunch|Dinner|Snack","cal":100,"pro":10,"carb":5,"fat":3,"qty":1}}]
```
Answer intake/progress questions from the log data. Be brief and specific. Estimate from knowledge if food isn't in library."""


@router.post("/", response_model=ChatResponse)
def chat(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    sb = get_service_client()

    goals = sb.table("goals").select("*").eq("user_id", user_id).execute()
    g = goals.data[0] if goals.data else {"cal": 2000, "pro": 160, "carb": 180, "fat": 71}

    lib = sb.table("food_library").select("name, cal, pro, carb, fat, unit").eq("user_id", user_id).execute()

    log = (
        sb.table("food_log")
        .select("name, meal, cal, pro, carb, fat, qty")
        .eq("user_id", user_id)
        .eq("log_date", str(date.today()))
        .execute()
    )

    system_prompt = SYSTEM_TEMPLATE.format(
        cal=g["cal"], pro=g["pro"], carb=g["carb"], fat=g["fat"],
        library=json.dumps(lib.data),
        log=json.dumps(log.data),
    )

    messages = [{"role": m.role, "content": m.content} for m in body.history]
    messages.append({"role": "user", "content": body.message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1000,
            messages=[{"role": "system", "content": system_prompt}, *messages],
        )
        reply = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")

    match = re.search(r"```log\n([\s\S]*?)\n```", reply)
    display_reply = re.sub(r"```log[\s\S]*?```", "", reply).strip()

    logged_entries = []
    if match:
        try:
            entries = json.loads(match.group(1))
            for e in entries:
                qty = e.get("qty", 1)
                row = sb.table("food_log").insert({
                    "user_id": user_id,
                    "name": e["name"],
                    "meal": e.get("meal", "Snack"),
                    "cal": round(e["cal"] * qty),
                    "pro": round(e["pro"] * qty, 1),
                    "carb": round(e["carb"] * qty, 1),
                    "fat": round(e["fat"] * qty, 1),
                    "qty": qty,
                    "log_date": str(date.today()),
                }).execute()
                logged_entries.append(row.data[0])
        except (json.JSONDecodeError, KeyError) as err:
            pass

    return ChatResponse(
        reply=display_reply or "Done! Logged those items for you.",
        logged_entries=logged_entries,
    )
