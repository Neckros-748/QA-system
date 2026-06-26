from pathlib import Path
from typing import List, Dict, Any

from app.docs.file.file_utils import FileIO


def __append_unique__(
		target: List[str],
		value:  List[str] | str,
) -> None:
	if isinstance(value, list):
		for v in value:
			if v not in target:
				target.append(v)
	elif isinstance(value, str):
		if value not in target:
			target.append(value)

def __report_progress__(
		data:         Dict[str, Any],
		path_to_data: Path | str,
		report_file:  Path | str,
):
	FileIO.write(
		str(
			path_to_data / "storage" / "temp" / report_file
		),
		data)