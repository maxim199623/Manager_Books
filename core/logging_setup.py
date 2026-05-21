import logging
import json
import logging.config
from pathlib import Path

from icecream import ic, install

def setup_logging(*, config_path: str = "logging_config.json", debug: bool = False) -> None:
    install()
    Path("logs").mkdir(exist_ok=True)
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    logging.config.dictConfig(config)

    if debug:
        ic.enable()
        ic.configureOutput(outputFunction=logging.getLogger("app").debug)
    else:
        ic.disable()