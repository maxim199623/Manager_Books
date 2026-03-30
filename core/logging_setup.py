import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from icecream import ic, install

def setup_logging(*, debug: bool = False, log_file: str | Path = "logs/app.log") -> None:
    install()
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )

    root_logger.addHandler(file_handler)

    if debug:
        ic.enable()
        ic.configureOutput(outputFunction=root_logger.debug)
    else:
        ic.disable()