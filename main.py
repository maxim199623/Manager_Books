import logging
from core.logging_setup import setup_logging

logger = logging.getLogger(__name__)

def apply_logger():
    setup_logging(debug=True)
    ic()
    logger.info("логгер запущен")


if __name__ == "__main__":
    apply_logger()



