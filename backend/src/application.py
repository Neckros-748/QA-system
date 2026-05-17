from pathlib import Path

from backend.src.common.annotation.annotator import Annotator
from backend.src.storage.database.storage import Storage
from backend.src.storage.storage import AppStorage


class Application:
	def __init__(self):
		# Временные данные (Документы)
		self.temp_document: str = "Федеральные клинические рекомендации Переломы проксимального отдела (Корректировка - 1).docx"
		self.temp_json_1: str   = "doc-step-1-1.json"
		self.temp_json_2: str   = "doc-step-1-2.json"
		self.temp_json_3: str   = "doc-step-2.json"

		# Пути до папок
		self.path_to_app: Path  = Path(__file__).resolve().parent
		self.path_to_data: Path = (self.path_to_app / ".." / ".." / "data").resolve()

		# Работа с документами
		self.annotator = Annotator(
			self.path_to_data
		)

		# Хранилище данных
		self.storage = Storage(
			str(
				self.path_to_data / "storage" / "temp" / self.temp_json_3
			)
		)


		self.annotator.set_storage(self.storage)
		# self.storage.set_annotator(self.annotator)