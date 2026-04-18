from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date

# Auth
class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str

# Goals
class GoalsUpdate(BaseModel):
    cal: int
    pro: float
    carb: float
    fat: float
    weight: Optional[float] = None
    goal_weight: Optional[float] = None

class GoalsResponse(GoalsUpdate):
    user_id: str

# Food Library
class FoodItem(BaseModel):
    name: str
    cal: float
    pro: float
    carb: float
    fat: float
    unit: str = "per serving"

class FoodItemResponse(FoodItem):
    id: str
    user_id: str

# Food Log
class LogEntry(BaseModel):
    name: str
    meal: str  # Breakfast | Lunch | Dinner | Snack
    cal: float
    pro: float
    carb: float
    fat: float
    qty: float = 1
    log_date: Optional[date] = None  # defaults to today server-side

class LogEntryResponse(LogEntry):
    id: str
    user_id: str

# Chat
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    reply: str
    logged_entries: List[LogEntryResponse] = []
