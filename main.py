import logging
import os

from core.web import app
from loguru import logger

if __name__ == "__main__":
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        logger.success(f'Запущен локальный сервер: http://127.0.0.1:8000/')

    app.run(port=8000, debug=True)
