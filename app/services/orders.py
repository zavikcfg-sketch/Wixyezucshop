from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.db import get_connection

ORDER_STATUS_NEW = "NEW"
ORDER_STATUS_PAID = "PAID"
ORDER_STATUS_DONE = "DONE"
ORDER_STATUS_CANCELED = "CANCELED"
ALLOWED_STATUSES = {ORDER_STATUS_NEW, ORDER_STATUS_PAID, ORDER_STATUS_DONE, ORDER_STATUS_CANCELED}


@dataclass(frozen=True)
class OrderCreateDTO:
    user_id: int
    username: str
    full_name: str
    game: str
    details: str


class OrderService:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def create(self, data: OrderCreateDTO) -> int:
        with get_connection(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO orders (user_id, username, full_name, game, details, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (data.user_id, data.username, data.full_name, data.game, data.details, ORDER_STATUS_NEW),
            )
            return int(cur.lastrowid)

    def get_by_id(self, order_id: int):
        with get_connection(self.db_path) as conn:
            return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    def list_recent(self, limit: int = 20):
        with get_connection(self.db_path) as conn:
            return conn.execute(
                "SELECT * FROM orders ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

    def list_by_user(self, user_id: int, limit: int = 10):
        with get_connection(self.db_path) as conn:
            return conn.execute(
                """
                SELECT id, game, status, created_at
                FROM orders
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

    def set_status(self, order_id: int, status: str) -> bool:
        if status not in ALLOWED_STATUSES:
            return False
        with get_connection(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status, order_id),
            )
            return cur.rowcount > 0
