"""
Точка входа для хостингов (Bothost и др.: обычно `python main.py` из корня репозитория).

В stderr сразу пишется статус — если логирование Python недоступно, ошибку всё равно видно.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _stderr(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def main_cli() -> None:
    _stderr(f"[wixyeez] repo_root={_REPO_ROOT}")
    _stderr(f"[wixyeez] cwd={Path.cwd()}")
    try:
        import asyncio

        from bot.main import main as bot_main

        asyncio.run(bot_main())
    except BaseException:
        _stderr("[wixyeez] FATAL — трассировка ниже:")
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise


if __name__ == "__main__":
    main_cli()
