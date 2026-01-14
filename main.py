# app/main.py
from fastapi import FastAPI
# REMOVED: StaticFiles import is no longer needed

# Import only the active features
from app.routers import dates, ai, dashboard

app = FastAPI(title="Anniversary App")

# REMOVED: app.mount("/photos"...) -> This was causing your crash

# Plug in the active features
app.include_router(dates.router)
app.include_router(ai.router)
app.include_router(dashboard.router)

@app.get("/")
def root():
    return {"message": "System Online. Happy Anniversary!"}