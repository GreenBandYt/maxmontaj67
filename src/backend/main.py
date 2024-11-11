import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/application.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Пример записи в лог
logger.info("Приложение запущено")
