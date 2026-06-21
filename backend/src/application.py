from pathlib import Path

from backend.src.common.annotation.annotator import Annotator
from backend.src.common.annotation.llm.llm_client import OpenAIClient
from backend.src.config import AnnotatorConfig
from backend.src.storage.database.storage import Storage


class Application:
	def __init__(self):
		# Временные данные (Документы)
		self.temp_document: str = "Федеральные клинические рекомендации Переломы проксимального отдела (Корректировка - 1).docx"
		self.temp_json_1: str   = "doc-step-1.json"
		self.temp_json_2: str   = "doc-step-2.json"
		self.temp_json_3: str   = "doc-step-3.json"

		# Пути до папок
		self.path_to_app: Path  = Path(__file__).resolve().parent
		self.path_to_data: Path = (self.path_to_app / ".." / ".." / "data").resolve()

		# Языковая модель
		self.llm_client: OpenAIClient = OpenAIClient()

		# Хранилище данных
		self.storage: Storage = Storage(
			str(
				self.path_to_data / "storage" / "temp" / self.temp_json_3
			)
		)


		# Работа с документами
		self.annotator: Annotator = Annotator(
			self.path_to_data,
			client  = None,
			storage = None,
			config  = AnnotatorConfig(),
		)





		self.annotator.set_client(self.llm_client)
		self.annotator.set_storage(self.storage)
