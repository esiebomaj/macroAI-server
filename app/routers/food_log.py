from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import date
from app.schemas import LogEntry, LogEntryResponse
from app.database import get_service_client
from app.auth_utils import get_current_user

router = APIRouter()


@router.get("/", response_model=List[LogEntryResponse])
def get_log(log_date: Optional[date] = None, current_user: dict = Depends(get_current_user)):
    sb = get_service_client()
    target_date = str(log_date or date.today())
    result = (
        sb.table("food_log")
        .select("*")
        .eq("user_id", current_user["user_id"])
        .eq("log_date", target_date)
        .order("created_at")
        .execute()
    )
    return result.data


@router.get("/history")
def get_history(current_user: dict = Depends(get_current_user)):
    """Returns daily calorie/macro totals grouped by date."""
    sb = get_service_client()
    result = (
        sb.table("food_log")
        .select("log_date, cal, pro, carb, fat")
        .eq("user_id", current_user["user_id"])
        .order("log_date", desc=True)
        .limit(500)
        .execute()
    )

    history = {}
    for row in result.data:
        d = row["log_date"]
        if d not in history:
            history[d] = {"cal": 0, "pro": 0, "carb": 0, "fat": 0}
        history[d]["cal"] += row["cal"]
        history[d]["pro"] += row["pro"]
        history[d]["carb"] += row["carb"]
        history[d]["fat"] += row["fat"]

    return {d: {k: round(v, 1) for k, v in totals.items()} for d, totals in history.items()}


@router.post("/", response_model=LogEntryResponse, status_code=201)
def add_log_entry(body: LogEntry, current_user: dict = Depends(get_current_user)):
    sb = get_service_client()
    result = sb.table("food_log").insert({
        **body.model_dump(),
        "user_id": current_user["user_id"],
        "log_date": str(body.log_date or date.today())
    }).execute()
    return result.data[0]


@router.delete("/{entry_id}", status_code=204)
def delete_log_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    sb = get_service_client()
    existing = sb.table("food_log").select("id").eq("id", entry_id).eq("user_id", current_user["user_id"]).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Log entry not found")
    sb.table("food_log").delete().eq("id", entry_id).execute()
