from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, food_log, library, goals, chat

app = FastAPI(title="Macro Tracker API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(food_log.router, prefix="/log", tags=["food-log"])
app.include_router(library.router, prefix="/library", tags=["library"])
app.include_router(goals.router, prefix="/goals", tags=["goals"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Macro Tracker API running"}
