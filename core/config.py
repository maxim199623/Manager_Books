import logging
from configparser import ConfigParser
from pathlib import Path
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class APISetting(BaseModel):
    address: str
    port:str

class AppSetting(BaseModel):
    API: APISetting

class Settings:
    def __init__(self, path: str | Path = "config.ini"):
        self.path = Path(path)
        self._parser = ConfigParser()
        self._settings: AppSetting | None = None
        self._check_settings()

    def _check_settings(self):
        """Проверка существования файла"""
        if not self.path.exists():
            logger.warning(f"Файл {self.path} не существует создаем новый")
            # создаём дефолтные настройки и сразу пишем файл
            self._settings = self._create_default_settings()
            self._write_parser_from_settings()
            self._save_to_disk()

        # читаем существующий файл
        self._parser.read(self.path, encoding="utf-8")
        self._settings = self._load_from_parser()


    def _load_from_parser(self) -> AppSetting:
        """Загрузка настроек"""
        if "API" not in self._parser:
            raise KeyError("Section [API] is required in config.ini")
        api_settings = self._parser["API"]
        address = api_settings.get("address", "127.0.0.1")
        port = api_settings.get("port", "1408")

        api_config = APISetting(address=address, port=port)
        return  AppSetting(API=api_config)

    def _create_default_settings(self):
        """Стандартные настройки, если файла нет."""
        api_config = APISetting(address="127.0.0.1", port="1408")

        return AppSetting(API=api_config)


    @property
    def settings(self) -> AppSetting:
        """Актуальные настройки (Pydantic-модель)."""
        return self._settings

    @property
    def api(self) -> APISetting:
        """Актуальные настройки (Pydantic-модель)."""
        return self._settings.API

    def _write_parser_from_settings(self):
        """Пересобрать self._parser из текущих Pydantic-настроек."""
        self._parser = ConfigParser()
        # [API]
        self._parser["API"] = {
            "address": self.api.address,
            "port":  self.api.port,
        }

    def _save_to_disk(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            self._parser.write(f)

    def all_config(self):
        return self._settings

    def api_config(self):
        return self._settings.API





