from __future__ import annotations

import uuid
from typing import Any, Dict, List, cast, Tuple

from fastapi import FastAPI, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# import numpy as np
from app.common.graph.nlp.utils.word_chunk import WordChunk
from app.docs.handler import DocumentHandler
from app.application import Application


STATUS_QUEUE: str   = "В очереди"
STATUS_PRE: str     = "Предобработка"
STATUS_PROCESS: str = "Обработка"
STATUS_POST: str    = "Постобработка"
STATUS_DONE: str    = "Обработан"

STATUS_ORDER = [STATUS_QUEUE, STATUS_PRE, STATUS_PROCESS, STATUS_POST, STATUS_DONE]


# ==============================================================================
# Приложение
# ==============================================================================

app         = FastAPI(title="QA-system", version="1.0.0")
application = Application()

app.add_middleware(
	CORSMiddleware,
	allow_origins     = ["http://localhost:5173"],
	allow_credentials = True,
	allow_methods     = ["*"],
	allow_headers     = ["*"],
)


# ==============================================================================
# Вспомогательные методы
# ==============================================================================

def get_document(doc_id: str) -> dict[str, Any] | None:
	for doc in application.storage.documents:
		if str(doc["id"]) == str(doc_id):
			return doc
	return None

def to_response(doc: dict[str, Any]) -> dict[str, Any]:
	return {
		"id":         doc["id"],
		"name":       doc["name"],
		"type":       doc["type"],
		"size":       doc["size"],
		"created_at": doc["created_at"],
		"status":     doc["status"],
	}

def search_match(doc: dict[str, Any], query: str) -> bool:
	if not query:
		return True

	q = query.lower()
	values = [
		str(doc.get("id", "")),
		doc.get("name", ""),
		doc.get("type", ""),
		doc.get("size", ""),
		doc.get("created_at", ""),
		doc.get("status", ""),
	]
	return any(q in str(value).lower() for value in values)


# ==============================================================================
# API
# ==============================================================================

@app.get("/api/documents")
def list_documents(search: str = ""):
	documents = [to_response(doc) for doc in application.storage.documents if search_match(doc, search)]
	return {
		"documents": documents,
	}

@app.post("/api/documents")
async def upload_document(file: UploadFile = File(...)):
	content = await file.read()
	if not file.filename.endswith('.docx'):
		return JSONResponse(
			status_code = 400,
			content     = {"detail": f"Разрешенные расширения: DOCX"}
		)
	try:
		from io import BytesIO
		from docx import Document
		from docx.document import Document as DocxDocument

		# Создание документа
		application.data = {
			"id":         uuid.uuid4(),
			"name":       file.filename,
			"type":       DocumentHandler.file_type(file.filename),
			"size":       DocumentHandler.format_size(len(content)),
			"created_at": DocumentHandler.now_str(),
			"status":     STATUS_QUEUE,
			"document":   Document(BytesIO(content)),
		}

		# Запись в список документов
		application.storage.documents = [
			doc for doc in application.storage.documents
			if doc["status"] == STATUS_DONE
		]
		application.storage.documents.insert(
			0, application.data
		)

		# Очистка временных данных
		handler: DocumentHandler = application.annotator.get_handler()
		handler.clear()

		return {
			"document": to_response(application.data),
		}
	except Exception as e:
		return JSONResponse(
			status_code = 400,
			content     = {"detail": f"Ошибка парсинга DOCX: {str(e)}"}
		)





@app.post("/api/documents/{doc_id}/process")
def process_document(doc_id: int | str):
	doc: dict[str, Any] | None = get_document(doc_id)

	if not doc:
		return JSONResponse(
			status_code = 404,
			content     = {"detail": "Document not found"}
		)

	current_status: str = doc["status"]
	if current_status == STATUS_DONE:
		return JSONResponse(
			status_code = 404,
			content     = {"detail": "The document has already been processed"}
		)
	elif current_status == STATUS_QUEUE:
		index = STATUS_ORDER.index(current_status)
		index = min(index + 1, len(STATUS_ORDER) - 1)
		doc["status"] = STATUS_ORDER[index]
	elif current_status == STATUS_PRE:
		index = STATUS_ORDER.index(current_status)
		index = min(index + 1, len(STATUS_ORDER) - 1)
		doc["status"] = STATUS_ORDER[index]
	elif current_status == STATUS_PROCESS:
		index = STATUS_ORDER.index(current_status)
		index = min(index + 1, len(STATUS_ORDER) - 1)
		doc["status"] = STATUS_ORDER[index]
	elif current_status == STATUS_POST:
		index = STATUS_ORDER.index(current_status)
		index = min(index + 1, len(STATUS_ORDER) - 1)
		doc["status"] = STATUS_ORDER[index]

	if current_status == STATUS_DONE:
		application.data = {}
	elif doc["status"] == STATUS_PRE:
		# ======================================================================
		# Шаг 1: Предобработка документа
		#
		# Документ преобразуется в локальное представление.
		# Итоговый документ сохраняется в json-файл.
		# ======================================================================

		data: Dict[str, Any] = application.annotator.preprocessing_document(
			application.data,
			report_file = application.temp_json_1,
		)

		# ======================================================================
		# Шаг 2: Очистка документа и управление содержимым
		#
		# Документ очищается пользователем от излишних параграфов и разделов.
		# Итоговый документ сохраняется в json-файл.
		# ======================================================================

		application.annotator.update_flags(
			"sct_h0:1",
			merge = True,
		)

	elif doc["status"] == STATUS_PROCESS:
		# ======================================================================
		# Шаг 2: Очистка документа и управление содержимым
		#
		# Документ очищается пользователем от излишних параграфов и разделов.
		# Итоговый документ сохраняется в json-файл.
		# ======================================================================

		application.annotator.clear(
			report_file=application.temp_json_2,
		)

		# ==============================================================================
		# Шаг 3: Разметка документа
		#
		# Из текста выделяются:
		# - WordChunk - для последующего формирования графа.
		# ==============================================================================

		word_chunks: Dict[str, List[WordChunk]] = application.annotator.processing_document(
			report_file=application.temp_json_3,
		)

	elif doc["status"] == STATUS_POST:

		# ==============================================================================
		# Шаг 3: Индексация и заполнение хранилища
		#
		# Внесение данных в хранилище данных:
		# - Графовый индекс, Лексический индекс, Векторный индекс
		# ==============================================================================

		application.annotator.postprocessing_document()

	elif doc["status"] == STATUS_DONE:

		query: str = "Чем отличается оказание помощи в России от других стран?"


		print(query)

		print(
			application.storage.request(
				query,
				application.annotator.processing_request(
					query
				),
			)
		)

		application.storage.lexical_index.save()


	return {
		"document": to_response(doc),
		"message": f"Статус документа изменен на: {doc['status']}",
	}



@app.get("/api/documents/content")
def get_document_content():
	doc = application.annotator.handler.doc
	if not doc:
		return JSONResponse(
			status_code=404,
			content={"detail": "В обработке нет документов"}
		)

	return {
		"content": doc
	}

@app.post("/api/documents/content/update-flags")
def update_document_flags(target_id: str, include: bool):

	doc = application.annotator.handler.doc
	if not doc:
		return JSONResponse(
			status_code=404,
			content={"detail": "В обработке нет документов"}
		)

	# if doc["status"] not in [STATUS_PRE]:
	# 	return JSONResponse(
	# 		status_code=400,
	# 		content={"detail": "Документ не в предобработке"}
	# 	)

	count = application.annotator.update_flags(
		target_id=target_id,
		include=not include,
		merge=False,
		clear=False,
		report_file="",
	)

	if count == 0:
		return JSONResponse(
			status_code=404,
			content={"detail": f"Element with id {target_id} not found"}
		)

	return {
		"success": True,
		"count":   count
	}









# @app.delete("/api/documents/{doc_id}")
# def delete_document(doc_id: int | str):
# 	doc = get_document(doc_id)
# 	if not doc:
# 		return JSONResponse(status_code=404, content={"detail": "Document not found"})
#
# 	application.storage.documents = [item for item in application.storage.documents if item["id"] != doc_id]
# 	# temp_storage.pop(doc_id, None)
#
# 	return {"message": "Документ удален"}
#
#
#
# @app.get("/api/storages")
# def get_storages():
# 	return {"items": storages}
#
#
# @app.get("/api/dictionary")
# def get_dictionary():
# 	return {"items": dictionary_items}
#
#
# @app.get("/api/knowledge-graph")
# def get_knowledge_graph():
# 	return knowledge_graph







#
#
#
# # ==============================================================================
# # Запрос к хранилищу
# # ==============================================================================
#
# # # Запрос в виде текста на естественном языке
# # #
# # # Чем отличается оказание помощи в России от других стран?
# # # Какие уровни доказательности используются в клинических рекомендациях по переломам проксимального отдела бедренной кости и чем они отличаются друг от друга?
# # #
# # query: str = "Чем отличается оказание помощи в России от других стран?"
# #
# # # Обработка запроса (Аннотатор)
# # query                 = app.annotator.request_preprocessing(query)
# # word_chunk, embedding = app.annotator.request_processing(query)
# #
# # # Обработка запроса (Запрос к хранилищу)
# # result = app.storage.request(word_chunk, embedding, top_k=10)
# #
# # for w in result:
# # 	print(w)
# # 	print(result[w])
# # 	print(result[w]["text"])
#
# '''
# 	prompt_template = """
# 	Ниже представлен контекст (выдержки из документов). Используй этот контекст для ответа на вопрос. Ответ должен быть по существу.
#
# 	ВОПРОС:
# 	{question}
#
# 	КОНТЕКСТ:
# 	{context}
#
# 	ОТВЕТ (коротко, по существу):
# 	"""
#
# 	answer = app.llm_client.generate(
# 		user_prompt = prompt_template,
# 		user_text   = {
# 			"question": query,
# 			"context": result,
# 		},
# 		max_tokens = 512,
# 	)
#
# 	# Вывод результатов
# 	print(f"""
# 	================================================================================
# 	Вывод результатов
# 	================================================================================
#
# 	Успешность запроса: {"Успешно" if answer["success"] else "Завершено с ошибкой"}
# 	Время запроса:      {answer["time"]} с
# 	Токены:             {answer["usage"]["prompt_tokens"]} : {answer["usage"]["completion_tokens"]} : {answer["usage"]["total_tokens"]}
#
# 	Вопрос:
# 	{query}
#
# 	Ответ:
# 	{answer["response"]}
#
# 	Ошибка:
# 	{answer["error"]}
#
# 	""")
# '''
#
#
#
#
#
#
# """
# ########################################################################################################################
# """
#
# # Запрос в виде текста на естественном языке
# #
# # Чем отличается оказание помощи в России от других стран?
# # Какие уровни доказательности используются в клинических рекомендациях по переломам проксимального отдела бедренной кости и чем они отличаются друг от друга?
# #
# query: str = "Чем отличается оказание помощи в России от других стран?"
#
# # Обработка запроса (Аннотатор)
# query                 = app.annotator.request_preprocessing(query)
# word_chunk, embedding = app.annotator.request_processing(query)
#
# for w in word_chunk:
# 	print(w.norm)
#
# # что
# # отличаться
# # оказание помощь
# # оказание
# # помощь
# # россия
# # других страна
# # страна
#
#
#
# # Обработка запроса (Запрос все узлов)
#
# # class ChunkType(IntEnum):
# # 	NULL  = -1 (Ошибка)
# # 	NONE  = 0 (Слово связка) (Маловероятно термин или значение) (Имеет LexType)
# #
# # 	# Структурные
# # 	TYPE_1 = 1 (сущность самого верхнего уровня) (высокая вероятность термина) (2 и более слова) (LexType.NONE: 0)
# # 	TYPE_2 = 2 (сущность верхнего уровня) (высокая вероятность термина, синоним) (2 и более слова) (LexType.NONE: 0)
# # 	TYPE_3 = 3 (сущность нижнего уровня) (нет доченрих элементов) (1 слово) (Имеет LexType)
#
# # class LexType(IntEnum):
# # 	NULL  = -1 (Ошибка)
# # 	NONE  = 0
# #
# # 	# Базовые (лексические)
# # 	NOUN  = 1 (Термин, Может быть значение)
# # 	VERB  = 2
# # 	ADJ   = 3
# # 	ADV   = 4
# # 	NUM   = 5
# # 	OTHER = 6
#
# # Запрос всех сущностей (терминов, значений, связей и тд)
# """
# клинический применение рекомендация
# {
# 'label': 'клинический применение рекомендация',
# 'type': (
# 	'TERM',                 - не нужен
# 	<ChunkType.TYPE_1: 1>,  - может понадобиться
# 	<LexType.NONE: 0>,      - может понадобиться
# 	0                       - уровень, не нужен (0 - ChunkType.TYPE_1; 1, 2, 3 - ChunkType.TYPE_2)
# ),
# 'in': { Входящие связи (Если имеет связи типа link - то это термин)
# 	'link': ['травматология'], - значение термина
# 	'parent': ['клинический применение', 'применение рекомендация', 'применение', 'рекомендация'], - дочерние элементы (их значения, тоже значения термина)
# 	'contains': [] - всегда пусто
# },
# 'out': { Исходящие связи (Если имеет связи типа link - то это значение)
# 	'link': [], - чьим значение является
# 	'parent': [], - родительский элемент (возможно их значения, тоже значения термина)
# 	'contains': [] - всегда пусто
# },
# 'documents': {
# 	'документ (индекс)': ['prg_1_[sct_h1:3] - абзац документа', 'sct_h1:3 - параграф документа']}
# }
#
#
#
# перелом
# {'label': 'перелом', 'type': ('TERM', <ChunkType.TYPE_3: 3>, <LexType.NOUN: 1>, 1),
# 'in': {'link': ['чрезвертельные', 'область тазобедренный сустав бду', 'метафизарных зона', 'распространяться', 'отделять'], 'parent': [], 'contains': []},
# 'out': {
# 	'link': ['принцип обследование', 'межвертельный', 'вертела', 'делиться', 'распространяться', 'подразделять'],
# 	'parent': ['перелом проксимальный отдел бедренный кость', 'перелом шейка бедренный кость', 'характер самого перелом', 'лечение больных перелом головка бедренный кость', 'причина такой перелом', 'такой тип перелом', 'низкоэнергетический перелом бк', 'риск возникновение перелом', 'перелом проксимальный отдел контралатеральный бк', 'перелом шбк', 'чрезвертельными перелом', 'подвертельными перелом', 'изолированный перелом большой вертел', 'перелом шейка бедро', 'чрезвертельный перелом', 'подвертельный перелом', 'линия перелом', 'локализация линия перелом', 'внесуставной перелом', 'внекапсульные перелом', 'перелом вертельный область бк', 'систематизация перелом головка бедренный кость', '4 тип перелом', 'перелом головка бк', 'перелом вертлужной впадина'],
# 	'contains': []
# },
# 'documents': {
# '100a9870-e619-402a-b3a4-1d6fd5fc4a34': ['prg_5_[sct_h1:3]', 'prg_8_[sct_h1:3]', 'prg_10_[sct_h1:3]', 'sct_h1:3', 'prg_1_[sct_h2:3_2]', 'prg_3_[sct_h2:3_2]', 'sct_h2:3_2', 'prg_1_[sct_h2:3_3]', 'sct_h2:3_3', 'prg_2_[sct_h2:3_4]', 'prg_3_[sct_h2:3_4]', 'sct_h2:3_4', 'prg_1_[sct_h2:3_5]', 'prg_2_[sct_h2:3_5]', 'prg_3_[sct_h2:3_5]', 'prg_4_[sct_h2:3_5]', 'prg_5_[sct_h2:3_5]', 'sct_h2:3_5', 'prg_1_[sct_h2:3_6]', 'prg_2_[sct_h2:3_6]', 'prg_3_[sct_h2:3_6]', 'prg_4_[sct_h2:3_6]', 'prg_5_[sct_h2:3_6]', 'prg_6_[sct_h2:3_6]', 'sct_h2:3_6', 'prg_1_[sct_h1:4]', 'prg_2_[sct_h1:4]', 'sct_h1:4', 'prg_1_[sct_h2:4_1]', 'prg_2_[sct_h2:4_1]', 'prg_3_[sct_h2:4_1]', 'prg_4_[sct_h2:4_1]', 'prg_5_[sct_h2:4_1]', 'sct_h2:4_1']}}
#
# """
#
# # result: Dict[str, Any] = app.storage.graph.get_all_nodes()
#
#
# # scope: Optional[
# # 	Union[
# # 		List[str],              - список, идентификаторы документа ()
# # 		Dict[str, List[str]]    - словарь
# #                                   ключ - идентификатор документа
# # 	]] = None,
# # include_parents: bool = False, - не уверен что рабоет
#
# # result: Dict[str, Any] = app.storage.graph.get_all_nodes(
# # 	scope = [
# # 		"1-1-1"
# # 	],
# # 	include_parents = False,
# # )
#
# result: Dict[str, Any] = app.storage.graph.get_all_nodes(
# 	scope = {
# 		"1-1-1": ["sct_h1:3", "sct_h1:4"],
# 		"2-2-2": [] # весь документ
# 	},
# 	include_parents = False,
# )
#
# # get_terms             - получить термины
# # get_values            - получить значения
# # _select_by_predicate  - получить узлы по условию
#
#
# # result: Dict[str, Any] = app.storage.graph.get_all_nodes(
# # 	scope = ["1-1-1"]
# # )
#
# # result: Dict[str, Any] = app.storage.graph.get_all_nodes(
# # 	scope = {"1-1-1": ["sct_h1:3", "sct_h1:4"]}
# # )
#
# # result: Dict[str, Any] = app.storage.graph.get_all_nodes(
# # 	# scope = {"1-1-1": ["sct_h1:3", "sct_h1:4"]},
# # 	# include_parents = True
# # )
#
#
# for w in result:
# 	print(w)
# 	print(result[w])
#
# """
# ########################################################################################################################
# """
#
# html = app.storage.graph.to_html()
#
# with open("graph.html", "w", encoding="utf-8") as f:
# 	f.write(html)
#
# # КАСТЫЛЬ (Очистка базы данных, необходимо перед завершением программы)
# app.storage.database.clear()


# # ---------------------------
# # Documents
# # ---------------------------
# @app.get("/documents")
# def get_documents():
#     return list(documents.values())
#
#
# @app.get("/documents/{doc_id}")
# def get_document(doc_id: str):
#     doc = documents.get(doc_id)
#     if not doc:
#         raise HTTPException(status_code=404, detail="Document not found")
#
#     # позже сюда добавим реальную обработку
#     return {
#         **doc,
#         "extra": {
#             "chunks": 0,
#             "tokens": 0,
#             "status_detail": "ok",
#         },
#     }
#
#
# @app.post("/documents/upload")
# async def upload_documents(files: List[UploadFile] = File(...)):
#     created = []
#
#     for file in files:
#         doc_id = str(uuid.uuid4())
#
#         doc = {
#             "id": doc_id,
#             "name": file.filename,
#             "type": file.filename.split(".")[-1].upper() if "." in file.filename else "FILE",
#             "size": f"{round(len(await file.read()) / 1024, 1)} KB",
#             "status": "В очереди",
#             "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
#         }
#
#         documents[doc_id] = doc
#         created.append(doc)
#
#     return {"created": created}
#
#
# @app.delete("/documents/{doc_id}")
# def delete_document(doc_id: str):
#     if doc_id not in documents:
#         raise HTTPException(status_code=404, detail="Document not found")
#
#     del documents[doc_id]
#     return {"status": "deleted", "id": doc_id}
#
#
# # ---------------------------
# # Terms
# # ---------------------------
# @app.get("/terms")
# def get_terms():
#     return terms
#
#
# # ---------------------------
# # Fragments
# # ---------------------------
# @app.get("/fragments")
# def get_fragments():
#     return fragments
#
#
# # ---------------------------
# # Storages
# # ---------------------------
# @app.get("/storages")
# def get_storages():
#     return storages
#
#
# # ---------------------------
# # Root
# # ---------------------------
# @app.get("/")
# def root():
#     return {"status": "QA backend running"}






#
#
