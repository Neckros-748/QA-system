import json
import os
from typing import Union, Dict, Any


class FileIO:

	# ---------- READ ----------

	@staticmethod
	def read_txt(file_path: str, encoding: str = "utf-8") -> str:
		try:
			with open(file_path, "r", encoding=encoding) as f:
				return f.read()
		except Exception as e:
			raise RuntimeError(f"Ошибка чтения TXT: {file_path} | {e}")

	@staticmethod
	def read_json(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
		try:
			with open(file_path, "r", encoding=encoding) as f:
				return json.load(f)
		except json.JSONDecodeError as e:
			raise ValueError(f"Некорректный JSON: {file_path} | {e}")
		except Exception as e:
			raise RuntimeError(f"Ошибка чтения JSON: {file_path} | {e}")

	@staticmethod
	def read(file_path: str) -> Union[str, Dict[str, Any]]:
		if file_path.lower().endswith(".txt"):
			return FileIO.read_txt(file_path)
		elif file_path.lower().endswith(".json"):
			return FileIO.read_json(file_path)
		else:
			raise ValueError(f"Неподдерживаемый формат: {file_path}")

	# ---------- WRITE ----------

	@staticmethod
	def write_txt(file_path: str, data: str, encoding: str = "utf-8") -> None:
		try:
			with open(file_path, "w", encoding=encoding) as f:
				f.write(data)
		except Exception as e:
			raise RuntimeError(f"Ошибка записи TXT: {file_path} | {e}")

	@staticmethod
	def write_json(
			file_path: str,
			data: Dict[str, Any],
			encoding: str = "utf-8",
			indent: int = "\t",
			ensure_ascii: bool = False
	) -> None:
		try:
			with open(file_path, "w", encoding=encoding) as f:
				json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
		except Exception as e:
			raise RuntimeError(f"Ошибка записи JSON: {file_path} | {e}")

	@staticmethod
	def write(file_path: str, data: Union[str, Dict[str, Any]]) -> None:
		os.makedirs(os.path.dirname(file_path), exist_ok=True)
		if isinstance(data, str):
			FileIO.write_txt(file_path, data)
		elif isinstance(data, dict):
			FileIO.write_json(file_path, data)
		else:
			raise ValueError(f"Неподдерживаемый тип данных: {type(data)}")
