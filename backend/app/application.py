from pathlib import Path
from typing import Any

from app.common.annotation.annotator import Annotator
from app.common.llm.llm_client import OpenAIClient
from app.storage.storage import Storage
from app.config import Config


class Application:
	def __init__(self):
		# Временные данные (Документы)
		self.temp_json_1: str            = "doc-step-1.json"
		self.temp_json_2: str            = "doc-step-2.json"
		self.temp_json_3: str            = "doc-step-3.json"
		self.data:        dict[str, Any] = {}

		# Пути до папок
		self.path_to_app:  Path = Path(__file__).resolve().parent
		self.path_to_data: Path = (self.path_to_app / ".." / "data").resolve()

		# Конфигурация
		config: Config      = Config()
		config.path_to_data = self.path_to_data
		config.storage_path = self.path_to_data / "storage"



		# Хранилище данных
		self.storage: Storage = Storage(
			config,
		)

		# Языковая модель
		self.llm_client: OpenAIClient = OpenAIClient()


		# Работа с документами
		self.annotator: Annotator = Annotator(
			self.path_to_data,
			storage = self.storage,
			config  = Config(),
		)
