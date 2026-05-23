import logging
import json
import logging.config
from pathlib import Path
import sys

from icecream import ic, install

def _resolve_config_path(config_path: str) -> tuple[Path, Path]:
    path = Path(config_path)
    if path.is_absolute():
        return path, path.parent

    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parent.parent

    return base_dir / path, base_dir

def setup_logging(*, config_path: str = "logging_config.json", debug: bool = False) -> None:
    install()
    resolved_config_path, logs_base_dir = _resolve_config_path(config_path)
    (logs_base_dir / "logs").mkdir(exist_ok=True)
    with open(resolved_config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    for handler_config in config.get("handlers", {}).values():
        filename = handler_config.get("filename")
        if filename and not Path(filename).is_absolute():
            handler_config["filename"] = str((logs_base_dir / filename).resolve())

    if debug:
        for logger_name in ("app", "app.api", "app.auth", "app.ws", "app.epub"):
            config.setdefault("loggers", {}).setdefault(logger_name, {})["level"] = "DEBUG"

    logging.config.dictConfig(config)

    if debug:
        ic.enable()
        ic.configureOutput(outputFunction=logging.getLogger("app").debug)
    else:
        ic.disable()
