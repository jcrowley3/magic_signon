from fastapi import APIRouter
from app.routers.v1.auth_router import router as auth_router
from app.routers.v1.user_router import router as user_router
from app.routers.v1.user_service_router import router as user_service_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["Auth"])
api_router.include_router(user_router, tags=["User"])
api_router.include_router(user_service_router, tags=["User Service"])


@api_router.get("/health", status_code=418)
def health_check():
    return {"Message": "magic_signon_api is up and running"}
