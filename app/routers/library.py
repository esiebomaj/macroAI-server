from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas import FoodItem, FoodItemResponse
from app.database import get_service_client
from app.auth_utils import get_current_user

router = APIRouter()


@router.get("/", response_model=List[FoodItemResponse])
def get_library(current_user: dict = Depends(get_current_user)):
    sb = get_service_client()
    result = sb.table("food_library").select("*").eq("user_id", current_user["user_id"]).order("name").execute()
    return result.data


@router.post("/", response_model=FoodItemResponse, status_code=201)
def add_food(body: FoodItem, current_user: dict = Depends(get_current_user)):
    sb = get_service_client()
    result = sb.table("food_library").insert({
        **body.model_dump(),
        "user_id": current_user["user_id"]
    }).execute()
    return result.data[0]


@router.put("/{food_id}", response_model=FoodItemResponse)
def update_food(food_id: str, body: FoodItem, current_user: dict = Depends(get_current_user)):
    sb = get_service_client()
    existing = sb.table("food_library").select("id").eq("id", food_id).eq("user_id", current_user["user_id"]).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Food item not found")
    result = sb.table("food_library").update(body.model_dump()).eq("id", food_id).execute()
    return result.data[0]


@router.delete("/{food_id}", status_code=204)
def delete_food(food_id: str, current_user: dict = Depends(get_current_user)):
    sb = get_service_client()
    existing = sb.table("food_library").select("id").eq("id", food_id).eq("user_id", current_user["user_id"]).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Food item not found")
    sb.table("food_library").delete().eq("id", food_id).execute()
