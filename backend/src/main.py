import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes.auth_router import router as auth_router
from routes.companies_router import router as companies_router
from routes.meter_router import router as meter_router
from routes.premises_router import router as premises_router
from routes.users_router import router as users_router
from validation_errors import translate_validation_error

app = FastAPI(title="Cube27 Backend API")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors: dict[str, str] = {}
    for error in exc.errors():
        location = error["loc"]
        if location and location[0] in {"body", "query", "path", "header", "cookie"}:
            field_location = location[1:]
        else:
            field_location = location
        field = ".".join(str(part) for part in field_location) or "body"
        message = translate_validation_error(error)
        if field in errors:
            errors[field] = f"{errors[field]}; {message}"
        else:
            errors[field] = message

    return JSONResponse(
        status_code=422,
        content=errors,
    )


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
