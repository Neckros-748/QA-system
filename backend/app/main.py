from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.common.graph.nlp.utils.word_chunk import WordChunk
from app.docs.handler import DocumentHandler
from app.application import Application


STATUS_QUEUE: str   = "Ожидание"
STATUS_EDIT: str    = "Редактирование"
STATUS_PROCESS: str = "Обработка"
STATUS_DONE: str    = "Обработан"

STATUS_ORDER = [STATUS_QUEUE, STATUS_EDIT, STATUS_PROCESS, STATUS_DONE]


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
			"id":         str(uuid.uuid4()),
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

@app.post("/api/documents/{doc_id}/process")
def process_document(doc_id: str):
	doc = get_document(doc_id)
	if not doc:
		return JSONResponse(status_code=404, content={"detail": "Document not found"})

	current_status = doc["status"]

	# Если уже обработан
	if current_status == STATUS_DONE:
		return JSONResponse(
			status_code=400,
			content={"detail": "Документ уже обработан"}
		)

	# --- Переход в Редактирование ---
	if current_status == STATUS_QUEUE:
		doc["status"] = STATUS_EDIT

		application.annotator.preprocessing_document(
			application.data, report_file = application.temp_json_1,
		)
		application.data = {}

		application.annotator.update_flags(
			"sct_h0:1", merge = True,
		)

		return {
			"document": to_response(doc),
			"message": "Документ переведён в режим редактирования",
		}

	# --- Переход в Обработку / Обработан (синхронно) ---
	if current_status == STATUS_EDIT:
		application.annotator.clear(
			report_file=application.temp_json_2,
		)

		# Обработку (индексация и т.п.)
		try:
			doc["status"] = STATUS_PROCESS

			word_chunks: Dict[str, List[WordChunk]] = (
				application.annotator.processing_document(
					report_file=application.temp_json_3,
				))
			application.annotator.postprocessing_document()
		except Exception as e:
			return JSONResponse(
				status_code=500,
				content={"detail": f"Ошибка обработки: {str(e)}"}
			)

		doc["status"] = STATUS_DONE

		application.storage.documents = [
			to_response(doc)
			for doc in application.storage.documents
			if doc["status"] == STATUS_DONE
		]
		application.storage.save()

		return {
			"document": to_response(doc),
			"message": "Документ успешно обработан",
		}

	return JSONResponse(
		status_code=400,
		content={"detail": f"Неизвестный статус: {current_status}"}
	)

@app.post("/api/documents/content/update-flags")
def update_document_flags(target_id: str, include: bool):

	doc = application.annotator.handler.doc
	if not doc:
		return JSONResponse(
			status_code=404,
			content={"detail": "В обработке нет документов"}
		)

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

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
	doc = get_document(doc_id)
	if not doc:
		return JSONResponse(status_code=404, content={"detail": "Document not found"})

	application.storage.documents = [
		doc for doc in application.storage.documents
		if doc["status"] == STATUS_DONE
	]
	application.data = {}

	handler: DocumentHandler = application.annotator.get_handler()
	handler.clear()

	return {"message": "Документ удален"}


