import json
import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from icecream import ic

from core.logging_setup import setup_logging


APP_DEBUG_LOGGERS = ("app", "app.api", "app.auth", "app.ws", "app.epub")
TEST_TMP_DIR = Path("tests/core/.tmp_logging_setup")


def _reset_logging_state() -> None:
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    root_logger.setLevel(logging.WARNING)

    for logger_obj in list(logging.root.manager.loggerDict.values()):
        if not isinstance(logger_obj, logging.Logger):
            continue

        for handler in logger_obj.handlers[:]:
            logger_obj.removeHandler(handler)
            handler.close()

        logger_obj.filters.clear()
        logger_obj.setLevel(logging.NOTSET)
        logger_obj.propagate = True
        logger_obj.disabled = False


@pytest.fixture(autouse=True)
def reset_logging_state():
    _reset_logging_state()
    yield
    _reset_logging_state()


def _write_logging_config(config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "simple": {"format": "%(levelname)s:%(name)s:%(message)s"}
                },
                "handlers": {
                    "app_file": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "filename": "logs/app.log",
                        "maxBytes": 1024,
                        "backupCount": 1,
                        "encoding": "utf-8",
                        "formatter": "simple",
                    },
                    "console": {
                        "class": "logging.StreamHandler",
                        "formatter": "simple",
                    }
                },
                "loggers": {
                    name: (
                        {
                            "level": "INFO",
                            "handlers": ["app_file", "console"],
                            "propagate": False,
                        }
                        if name == "app"
                        else {
                            "level": "INFO",
                            "handlers": ["console"],
                            "propagate": False,
                        }
                    )
                    for name in APP_DEBUG_LOGGERS
                },
                "root": {"level": "WARNING", "handlers": ["console"]},
            }
        ),
        encoding="utf-8",
    )


def _run_from_test_tmp_dir(callback) -> None:
    TEST_TMP_DIR.mkdir(parents=True, exist_ok=True)
    current_dir = Path.cwd()
    os.chdir(TEST_TMP_DIR)
    try:
        callback()
    finally:
        os.chdir(current_dir)


def test_setup_logging_promotes_app_namespaces_to_debug_in_debug_mode():
    config_path = TEST_TMP_DIR / "logging.json"
    _write_logging_config(config_path)
    resolved_config_path = str(config_path.resolve())

    _run_from_test_tmp_dir(
        lambda: setup_logging(config_path=resolved_config_path, debug=True)
    )

    for logger_name in APP_DEBUG_LOGGERS:
        assert logging.getLogger(logger_name).level == logging.DEBUG


def test_setup_logging_uses_temp_config_for_app_and_app_ws_in_normal_mode():
    config_path = TEST_TMP_DIR / "logging.json"
    _write_logging_config(config_path)
    resolved_config_path = str(config_path.resolve())

    _run_from_test_tmp_dir(
        lambda: setup_logging(config_path=resolved_config_path, debug=False)
    )

    assert logging.getLogger("app").level == logging.INFO
    assert logging.getLogger("app.ws").level == logging.INFO


def test_setup_logging_resolves_relative_config_independently_from_current_cwd():
    base_dir = (TEST_TMP_DIR / "relative_root").resolve()
    fake_core_dir = base_dir / "core"
    other_cwd = (TEST_TMP_DIR / "other_cwd").resolve()
    config_path = base_dir / "logging.json"

    fake_core_dir.mkdir(parents=True, exist_ok=True)
    other_cwd.mkdir(parents=True, exist_ok=True)
    _write_logging_config(config_path)

    current_dir = Path.cwd()
    os.chdir(other_cwd)
    try:
        with patch("core.logging_setup.__file__", str(fake_core_dir / "logging_setup.py")):
            setup_logging(config_path="logging.json", debug=False)
    finally:
        os.chdir(current_dir)

    assert logging.getLogger("app").level == logging.INFO
    assert (base_dir / "logs").exists()
    assert any(
        getattr(handler, "baseFilename", None) == str((base_dir / "logs" / "app.log").resolve())
        for handler in logging.getLogger("app").handlers
    )


def test_repository_logging_config_uses_stable_namespaces_and_warning_for_external_loggers():
    config = json.loads(Path("logging_config.json").read_text(encoding="utf-8"))
    loggers = config["loggers"]

    for logger_name in APP_DEBUG_LOGGERS:
        assert logger_name in loggers

    assert loggers["httpx"]["level"] == "WARNING"
    assert loggers["httpcore"]["level"] == "WARNING"
    assert loggers["flet"]["level"] == "WARNING"
    assert config["root"]["level"] == "WARNING"


def test_setup_logging_disables_icecream_in_normal_mode():
    config_path = TEST_TMP_DIR / "logging.json"
    _write_logging_config(config_path)
    resolved_config_path = str(config_path.resolve())
    ic.enable()

    _run_from_test_tmp_dir(
        lambda: setup_logging(config_path=resolved_config_path, debug=False)
    )

    assert ic.enabled is False
