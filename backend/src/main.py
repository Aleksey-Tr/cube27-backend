import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth_router import router as auth_router
from routes.companies_router import router as companies_router
from routes.meter_router import router as meter_router
from routes.premises_router import router as premises_router
from routes.users_router import router as users_router

app = FastAPI(title="Cube27 Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(companies_router)
app.include_router(premises_router)
app.include_router(meter_router)


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
