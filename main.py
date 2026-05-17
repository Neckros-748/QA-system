from typing import Dict, List, Any, cast, Tuple

import numpy as np

from backend.src.docs.file.file_utils import FileIO
from backend.src.common.annotation.nlp.utils.word_chunk import WordChunk
from backend.src.application import Application

app = Application()



# ==============================================================================
# Шаг 1.1: Считывание документа (docx)
#
# Документ считывается и преобразуется в локальное представление.
# Итоговый документ сохраняется в json-файл.
# ==============================================================================

data: Dict[str, Any] = app.annotator.document_preprocessing(
	str(
		app.path_to_data / "documents" / app.temp_document
	),
	report_file = app.temp_json_1,
)


# ==============================================================================
# Шаг 1.2: Очистка документа и управление содержимым
#
# Документ очищается пользователем от излишних параграфов и разделов.
# Итоговый документ сохраняется в json-файл.
# ==============================================================================

# Обязательно
app.annotator.update_flags(
	"sct_h0:1",
	merge = True,
)

# Необязательно (Удаление лишних частей)
app.annotator.update_flags(
	[
		"prg_1_[sct_h0:1]",  "prg_3_[sct_h0:1]",  "prg_4_[sct_h0:1]",
		"prg_6_[sct_h0:1]",  "prg_7_[sct_h0:1]",  "prg_8_[sct_h0:1]",
		"prg_10_[sct_h0:1]", "prg_11_[sct_h0:1]", "prg_12_[sct_h0:1]",
		"prg_13_[sct_h0:1]", "prg_14_[sct_h0:1]",
		"sct_h1:1", "sct_h1:2",
	],
	include = False,
)

# Обязательно
app.annotator.clean(
	report_file = app.temp_json_2,
)


# ==============================================================================
# Шаг 2: Гибридное аннотирование документа
#
# Из текста выделяются:
# - WordChunk - для последующего формирования графа.
# - Embedding - для последующего формирования кластера векторов.
# ==============================================================================

word_chunks, embeddings = cast(
    Tuple[
	    Dict[str, List[WordChunk]],
	    Dict[str, np.ndarray],
    ],
    app.annotator.document_processing(
		report_file = app.temp_json_3,
    )
)


# ==============================================================================
# Шаг 3: Заполнение хранилища
#
# Внесение данных в хранилище данных:
# - Графовое хранилище
# - Векторное хранилище
# ==============================================================================

app.annotator.document_postprocessing()



# ==============================================================================
# Запрос к хранилищу
# ==============================================================================

# Запрос в виде текста на естественном языке
query: str = "Чем отличается оказание помощи в России от других стран?"
# "Какие уровни доказательности используются в клинических рекомендациях по переломам проксимального отдела бедренной кости и чем они отличаются друг от друга?"

# Обработка запроса (Аннотатор)
query                 = app.annotator.request_preprocessing(query)
word_chunk, embedding = app.annotator.request_processing(query)

# Обработка запроса (Запрос к хранилищу)
result = app.storage.request(word_chunk, embedding, top_k=10)

# Вывод результатов
for w in result:
	print(w)
	print(result[w])
	print(result[w]["text"])

# КАСТЫЛЬ (Очистка базы данных, необходимо перед завершением программы)
app.storage.database.clear()



