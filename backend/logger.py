from loguru import logger
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger.remove()
logger.add(LOG_DIR / "app.log", rotation="5 MB", retention=5, enqueue=True, level="INFO")
