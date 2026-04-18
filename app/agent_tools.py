"""LangChain tool definitions for the chat agent.

Tools are built per-request via ``build_tools(sb, user_id, ctx)`` so that
``user_id`` is captured in a closure and never exposed to the model.
``ctx`` is a mutable dict the router uses to detect whether any state-changing
tool ran (so the frontend can refetch).
"""
from datetime import date
from typing import Optional, List

from langchain_core.tools import tool, BaseTool


MEAL_VALUES = ("Breakfast", "Lunch", "Dinner", "Snack")


def _today() -> str:
    return str(date.today())


def build_tools(sb, user_id: str, ctx: dict) -> List[BaseTool]:
    """Return the full list of LangChain tools bound to this user and context."""

    def _own_log_entry(entry_id: str):
        existing = (
            sb.table("food_log")
            .select("id")
            .eq("id", entry_id)
            .eq("user_id", user_id)
            .execute()
        )
        return bool(existing.data)

    def _own_library_item(food_id: str):
        existing = (
            sb.table("food_library")
            .select("id")
            .eq("id", food_id)
            .eq("user_id", user_id)
            .execute()
        )
        return bool(existing.data)

    @tool
    def log_food(
        name: str,
        meal: str,
        cal: float,
        pro: float,
        carb: float,
        fat: float,
        qty: float = 1,
        log_date: Optional[str] = None,
    ) -> str:
        """Log a food item to the user's daily food log.

        Args:
            name: Food name.
            meal: One of "Breakfast", "Lunch", "Dinner", "Snack".
            cal: Calories for ONE serving (will be multiplied by qty).
            pro: Grams of protein per serving.
            carb: Grams of carbs per serving.
            fat: Grams of fat per serving.
            qty: Number of servings (default 1).
            log_date: ISO date (YYYY-MM-DD). Defaults to today.
        """
        if meal not in MEAL_VALUES:
            return f"Error: meal must be one of {MEAL_VALUES}, got {meal!r}."
        row = sb.table("food_log").insert({
            "user_id": user_id,
            "name": name,
            "meal": meal,
            "cal": round(cal * qty),
            "pro": round(pro * qty, 1),
            "carb": round(carb * qty, 1),
            "fat": round(fat * qty, 1),
            "qty": qty,
            "log_date": log_date or _today(),
        }).execute().data[0]
        ctx["mutated"] = True
        return f"Logged {name} x{qty} (id={row['id']}, {row['cal']}kcal)."

    @tool
    def remove_logged_food(entry_id: str) -> str:
        """Delete a single food log entry by its id."""
        if not _own_log_entry(entry_id):
            return f"Error: log entry {entry_id} not found."
        sb.table("food_log").delete().eq("id", entry_id).execute()
        ctx["mutated"] = True
        return f"Deleted log entry {entry_id}."

    @tool
    def modify_logged_food(
        entry_id: str,
        name: Optional[str] = None,
        meal: Optional[str] = None,
        cal: Optional[float] = None,
        pro: Optional[float] = None,
        carb: Optional[float] = None,
        fat: Optional[float] = None,
        qty: Optional[float] = None,
        log_date: Optional[str] = None,
    ) -> str:
        """Update fields on an existing food log entry. Only provided fields change."""
        if not _own_log_entry(entry_id):
            return f"Error: log entry {entry_id} not found."
        if meal is not None and meal not in MEAL_VALUES:
            return f"Error: meal must be one of {MEAL_VALUES}, got {meal!r}."
        patch = {
            k: v for k, v in {
                "name": name, "meal": meal, "cal": cal, "pro": pro,
                "carb": carb, "fat": fat, "qty": qty, "log_date": log_date,
            }.items() if v is not None
        }
        if not patch:
            return "Error: no fields provided to update."
        row = sb.table("food_log").update(patch).eq("id", entry_id).execute().data[0]
        ctx["mutated"] = True
        return f"Updated log entry {entry_id}: {patch}."

    @tool
    def add_food_to_library(
        name: str,
        cal: float,
        pro: float,
        carb: float,
        fat: float,
        unit: str = "per serving",
    ) -> str:
        """Add a new item to the user's reusable food library."""
        row = sb.table("food_library").insert({
            "user_id": user_id,
            "name": name,
            "cal": cal,
            "pro": pro,
            "carb": carb,
            "fat": fat,
            "unit": unit,
        }).execute().data[0]
        ctx["mutated"] = True
        return f"Added {name} to library (id={row['id']})."

    @tool
    def remove_food_from_library(food_id: str) -> str:
        """Delete a food from the user's reusable food library by id."""
        if not _own_library_item(food_id):
            return f"Error: library item {food_id} not found."
        sb.table("food_library").delete().eq("id", food_id).execute()
        ctx["mutated"] = True
        return f"Removed library item {food_id}."

    @tool
    def modify_food_in_library(
        food_id: str,
        name: Optional[str] = None,
        cal: Optional[float] = None,
        pro: Optional[float] = None,
        carb: Optional[float] = None,
        fat: Optional[float] = None,
        unit: Optional[str] = None,
    ) -> str:
        """Update fields on an existing library item. Only provided fields change."""
        if not _own_library_item(food_id):
            return f"Error: library item {food_id} not found."
        patch = {
            k: v for k, v in {
                "name": name, "cal": cal, "pro": pro,
                "carb": carb, "fat": fat, "unit": unit,
            }.items() if v is not None
        }
        if not patch:
            return "Error: no fields provided to update."
        sb.table("food_library").update(patch).eq("id", food_id).execute()
        ctx["mutated"] = True
        return f"Updated library item {food_id}: {patch}."

    @tool
    def update_goals(
        cal: int,
        pro: float,
        carb: float,
        fat: float,
        weight: Optional[float] = None,
        goal_weight: Optional[float] = None,
    ) -> str:
        """Upsert the user's daily nutrition goals (and optional weight metrics)."""
        data = {
            "user_id": user_id,
            "cal": cal,
            "pro": pro,
            "carb": carb,
            "fat": fat,
            "weight": weight,
            "goal_weight": goal_weight,
        }
        existing = sb.table("goals").select("id").eq("user_id", user_id).execute()
        if existing.data:
            sb.table("goals").update(data).eq("user_id", user_id).execute()
        else:
            sb.table("goals").insert(data).execute()
        ctx["mutated"] = True
        return f"Goals updated: {cal}kcal, {pro}g P, {carb}g C, {fat}g F."

    @tool
    def list_log_entries(log_date: Optional[str] = None) -> str:
        """List the user's food log entries for a given date (ISO YYYY-MM-DD).

        Defaults to today. Use this to look up entry ids before calling
        ``remove_logged_food`` or ``modify_logged_food`` for past dates.
        """
        target = log_date or _today()
        rows = (
            sb.table("food_log")
            .select("id, name, meal, cal, pro, carb, fat, qty")
            .eq("user_id", user_id)
            .eq("log_date", target)
            .order("created_at")
            .execute()
            .data
        )
        if not rows:
            return f"No log entries for {target}."
        lines = [
            f"- {r['id']}: {r['name']} x{r['qty']} ({r['meal']}) — "
            f"{r['cal']}kcal {r['pro']}P/{r['carb']}C/{r['fat']}F"
            for r in rows
        ]
        return f"Log for {target}:\n" + "\n".join(lines)

    return [
        log_food,
        remove_logged_food,
        modify_logged_food,
        add_food_to_library,
        remove_food_from_library,
        modify_food_in_library,
        update_goals,
        list_log_entries,
    ]
