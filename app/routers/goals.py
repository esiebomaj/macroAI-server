from fastapi import APIRouter, Depends
from app.schemas import GoalsUpdate, GoalsResponse
from app.database import get_service_client
from app.auth_utils import get_current_user

router = APIRouter()


@router.get("/", response_model=GoalsResponse)
def get_goals(current_user: dict = Depends(get_current_user)):
    sb = get_service_client()
    result = sb.table("goals").select("*").eq("user_id", current_user["user_id"]).execute()
    if not result.data:
        return GoalsResponse(user_id=current_user["user_id"], cal=2000, pro=160, carb=180, fat=71)
    return {**result.data[0], "user_id": current_user["user_id"]}


@router.put("/", response_model=GoalsResponse)
def update_goals(body: GoalsUpdate, current_user: dict = Depends(get_current_user)):
    sb = get_service_client()
    user_id = current_user["user_id"]
    data = {**body.model_dump(), "user_id": user_id}

    existing = sb.table("goals").select("id").eq("user_id", user_id).execute()
    if existing.data:
        result = sb.table("goals").update(data).eq("user_id", user_id).execute()
    else:
        result = sb.table("goals").insert(data).execute()

    return {**result.data[0], "user_id": user_id}
