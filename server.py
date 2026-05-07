"""HTTP-сервис для сайта Wixyeez UC Shop и API создания платежей PayCore."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from shared.catalog import (  # noqa: E402
    OTHER_GAMES,
    PUBG_UC_PRODUCTS,
    TELEGRAM_GOODS,
    VPN_SERVICE,
    Product,
    get_product,
)
from shared.config import get_settings  # noqa: E402
from shared.paycore import (  # noqa: E402
    PayCoreNotConfiguredError,
    PayCoreRequestError,
    create_payment_invoice,
)

WEB_DIR = ROOT / "web"
BRAND = "Wixyeez UC Shop"


def _product_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "amount": p.amount,
        "currency": p.currency,
        "account_label": p.game_id_label,
    }


def build_api_router() -> APIRouter:
    r = APIRouter()

    @r.get("/meta")
    async def api_meta() -> dict:
        s = get_settings()
        bot = s.telegram_bot_username.strip().lstrip("@")
        return {"brand": BRAND, "telegram_bot_username": bot}

    @r.get("/catalog")
    async def api_catalog() -> dict:
        def rows(items: list[Product]) -> list[dict]:
            return [_product_dict(x) for x in items]

        return {
            "pubg": rows(PUBG_UC_PRODUCTS),
            "telegram": rows(TELEGRAM_GOODS),
            "games": rows(OTHER_GAMES),
            "vpn": rows(VPN_SERVICE),
        }

    class InvoiceBody(BaseModel):
        product_id: str = Field(min_length=2, max_length=80)
        account: str = Field(min_length=3, max_length=200)

    @r.post("/create-invoice")
    async def api_create_invoice(body: InvoiceBody) -> dict:
        product = get_product(body.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        if product.amount <= 0:
            raise HTTPException(status_code=400, detail="Товар недоступен для заказа")
        settings = get_settings()
        curr = settings.paycore_currency or product.currency or "RUB"
        desc = (
            f"{BRAND} | {product.title} | {product.game_id_label}: {body.account[:120]}"
        )

        try:
            inv = await create_payment_invoice(
                settings,
                amount=product.amount,
                currency=curr,
                description=desc,
            )
        except PayCoreNotConfiguredError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        except PayCoreRequestError as e:
            raise HTTPException(status_code=502, detail=str(e)) from e

        checkout = inv.get("hpp_url")
        if not checkout or not isinstance(checkout, str):
            raise HTTPException(
                status_code=502,
                detail=f"Нет ссылки оплаты в ответе: {inv!r}",
            )
        ref = inv.get("reference_id", "")
        return {
            "checkout_url": checkout,
            "reference_id": ref,
            "amount": product.amount,
            "currency": curr,
        }

    return r


def create_app() -> FastAPI:
    app = FastAPI(title=BRAND, version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(build_api_router(), prefix="/api")
    app.mount(
        "/",
        StaticFiles(directory=str(WEB_DIR), html=True),
        name="web",
    )
    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
    )


if __name__ == "__main__":
    main()
