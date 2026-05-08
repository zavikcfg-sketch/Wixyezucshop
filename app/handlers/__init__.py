from aiogram import Dispatcher

from app.handlers.admin import router as admin_router
from app.handlers.user import router as user_router
from app.handlers.webapp import router as webapp_router


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(webapp_router)
    dp.include_router(admin_router)
    dp.include_router(user_router)
