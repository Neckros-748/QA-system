from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.common.graph.nlp.utils.word_chunk import WordChunk
from app.docs.handler import DocumentHandler
from app.application import Application

from app import dialog

import time

import os
_tree_instance = None
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TREE_FILE_PATH = os.path.join(BASE_DIR, "dialog/dialog_tree.pkl")

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

@app.get("/api/knowledge-graph")
def get_knowledge_graph():
	return application.storage.graph_index.get_graph_data()



from pydantic import BaseModel

class ChatRequest(BaseModel):
	question: str

@app.post("/api/chat")
def chat(request: ChatRequest):
	query = request.question
	if not query:
		return JSONResponse(status_code=400, content={"detail": "Вопрос не может быть пустым"})

	try:
		# 1. Обработка запроса
		word_chunks = application.annotator.request_processing(query)

		# 2. Поиск по хранилищу
		context = application.storage.request(query, word_chunks)

		# 3. Генерация ответа через LLM
		prompt_template = """
		Ниже представлен контекст (выдержки из документов). Используй этот контекст для ответа на вопрос. Ответ должен быть по существу.

		ВОПРОС:
		{question}

		КОНТЕКСТ:
		{context}

		ОТВЕТ (коротко, по существу):
		"""

		answer_data = application.llm_client.generate(
			user_prompt=prompt_template,
			user_text={
				"question": query,
				"context": context,
			},
			max_tokens=1024,
		)

		return {
			"answer":  answer_data.get("response"),
			"context": context,
			"success": answer_data.get("success", False),
			"error":   answer_data.get("error"),
		}
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={"detail": f"Ошибка обработки запроса: {str(e)}"}
		)


# Дерево диалога

# Получить дерево диалога
@app.get("/api/dialog-tree")
async def get_dialog_tree():
	try:
		tree = get_tree()

		# Проверка на None
		if tree is None:
			tree = dialog.create_empty_dialog_tree()
			_tree_instance = tree
			save_tree()

		# Проверка наличия root
		if not hasattr(tree, 'root') or tree.root is None:
			tree = dialog.create_empty_dialog_tree()
			_tree_instance = tree
			save_tree()

		tree_dict = dialog.tree_to_dict(tree)
		info = dialog.get_tree_info(tree)

		return {
			"success": True,
			"tree": tree_dict,
			"info": info
		}
	except Exception as e:
		print(f"[ERROR] Ошибка получения дерева: {e}")
		empty_tree = dialog.create_empty_dialog_tree()
		return {
			"success": True,
			"tree": dialog.tree_to_dict(empty_tree),
			"info": {"exists": True, "scenes_count": 1, "max_depth": 0},
			"warning": str(e)
		}


# Получить данные сцены
@app.get("/api/dialog-tree/scene/{scene_name}")
async def get_scene(scene_name: str):
	try:
		tree = get_tree()

		# Проверка на None
		if tree is None:
			return {
				"success": False,
				"error": "Дерево не загружено"
			}

		scene = dialog.find_scene_by_name(tree, scene_name)
		if not scene:
			return {
				"success": False,
				"error": f"Сцена '{scene_name}' не найдена"
			}

		return {
			"success": True,
			"scene": dialog.scene_to_dict(scene)
		}
	except Exception as e:
		print(f"[ERROR] Ошибка получения сцены: {e}")
		return {
			"success": False,
			"error": str(e)
		}


# Обновить сцену
@app.put("/api/dialog-tree/scene/{scene_name}")
async def update_scene(scene_name: str, data: dict):
	try:
		tree = get_tree()

		# Проверка на None
		if tree is None:
			return {
				"success": False,
				"error": "Дерево не загружено"
			}

		success = dialog.update_scene_in_tree(tree, scene_name, data)
		if not success:
			return {
				"success": False,
				"error": f"Сцена '{scene_name}' не найдена"
			}

		# Сохраняем изменения
		save_tree()

		# Возвращаем обновленную сцену
		scene = dialog.find_scene_by_name(tree, scene_name)
		return {
			"success": True,
			"scene": dialog.scene_to_dict(scene) if scene else None
		}
	except Exception as e:
		print(f"[ERROR] Ошибка обновления сцены: {e}")
		return {
			"success": False,
			"error": str(e)
		}


@app.delete("/api/dialog-tree/scene/{scene_name}")
async def delete_scene(scene_name: str):
	try:
		if scene_name == "root":
			return {
				"success": False,
				"error": "Нельзя удалить корневую сцену"
			}

		tree = get_tree()

		# Проверка на None
		if tree is None:
			return {
				"success": False,
				"error": "Дерево не загружено"
			}

		success = dialog.delete_scene_by_name(tree, scene_name)
		if not success:
			return {
				"success": False,
				"error": f"Сцена '{scene_name}' не найдена"
			}

		# Сохраняем изменения
		save_tree()

		return {
			"success": True
		}
	except Exception as e:
		print(f"[ERROR] Ошибка удаления сцены: {e}")
		return {
			"success": False,
			"error": str(e)
		}


@app.post("/api/dialog-tree/create-default")
async def create_default_tree():
	try:
		global _tree_instance
		_tree_instance = dialog.create_simple_dialog_tree()
		_tree_instance.set_height_tree()
		save_tree()

		tree_dict = dialog.tree_to_dict(_tree_instance)
		return {
			"success": True,
			"message": "Дерево с примерами создано",
			"tree": tree_dict
		}
	except Exception as e:
		print(f"[ERROR] Ошибка создания дерева с примерами: {e}")
		return {
			"success": False,
			"error": str(e)
		}


@app.get("/api/dialog-tree/info")
async def get_tree_info_endpoint():
	try:
		tree = get_tree()
		if tree is None:
			return {
				"success": True,
				"info": {
					"exists": False,
					"scenes_count": 0,
					"max_depth": 0
				}
			}

		info = dialog.get_tree_info(tree)
		return {
			"success": True,
			"info": info
		}
	except Exception as e:
		print(f"[ERROR] Ошибка получения информации: {e}")
		return {
			"success": False,
			"error": str(e)
		}

'''
def get_tree():
    global _tree_instance
    if _tree_instance is None:
        _tree_instance = dialog.load_or_create_dialog_tree(TREE_FILE_PATH)
    return _tree_instance
'''
def get_tree():

    global _tree_instance
    '''
    if _tree_instance is None:
        # Пробуем загрузить из файла
        _tree_instance = dialog.load_dialog_tree_safe(TREE_FILE_PATH)
        if _tree_instance is None:
            # Если файла нет - создаём из функции
            _tree_instance = dialog.create_fracture_dialog_tree()
            dialog.save_dialog_tree_safe(_tree_instance, TREE_FILE_PATH)
            print("[INFO] Дерево диалога создано из функции create_fracture_dialog_tree()")
        else:
            print("[INFO] Дерево диалога загружено из файла")
    '''
    _tree_instance = dialog.create_fracture_dialog_tree()
    return _tree_instance


def save_tree():
    tree = get_tree()
    if tree is None:
        return False
    return dialog.save_dialog_tree_safe(tree, TREE_FILE_PATH)


@app.post("/api/dialog-tree/scene/{parent_name}")
async def create_scene(parent_name: str, data: dict):
	try:
		tree = get_tree()

		if tree is None:
			global _tree_instance
			tree = dialog.create_empty_dialog_tree()
			_tree_instance = tree

		scene_name = dialog.create_scene_in_tree(tree, parent_name, data)
		if not scene_name:
			return {
				"success": False,
				"error": f"Не удалось создать сцену в '{parent_name}'"
			}

		save_tree()

		scene = dialog.find_scene_by_name(tree, scene_name)
		return {
			"success": True,
			"scene": dialog.scene_to_dict(scene) if scene else None
		}
	except Exception as e:
		print(f"[ERROR] Ошибка создания сцены: {e}")
		return {
			"success": False,
			"error": str(e)
		}

# Глобальные настройки диалога
_dialog_settings = {
	"max_context_messages": 10,
	"fixed_first_messages": 3
}


@app.get("/api/dialog-settings")
async def get_dialog_settings():
	try:
		return {
			"success": True,
			"settings": _dialog_settings
		}
	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@app.put("/api/dialog-settings")
async def update_dialog_settings(data: dict):
	global _dialog_settings
	try:
		if "max_context_messages" in data:
			_dialog_settings["max_context_messages"] = max(1, int(data["max_context_messages"]))
		if "fixed_first_messages" in data:
			_dialog_settings["fixed_first_messages"] = max(0, int(data["fixed_first_messages"]))

		return {
			"success": True,
			"settings": _dialog_settings
		}
	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}

@app.post("/api/chat/dialog-tree")
async def chat_with_dialog_tree(request: dict):
	"""
    Чат с использованием дерева диалога
    """
	start_time = time.time()
	try:
		question = request.get("question", "")

		if not question:
			return JSONResponse(
				status_code=400,
				content={"detail": "Вопрос не может быть пустым"}
			)

		# Получаем дерево
		tree = get_tree()
		if tree is None:
			tree = dialog.create_empty_dialog_tree()
			global _tree_instance
			_tree_instance = tree

		# Получаем storage из application
		storage = application.storage

		# Вызываем функцию new_dialog из dialog.py
		result = dialog.new_dialog(
			question=question,
			storage=storage,
			dialog_tree=tree,
			app=application,
			previous_intents=None
		)

		# Проверяем результат
		if not result:
			return {
				"success": False,
				"error": "Не удалось получить ответ от дерева диалога"
			}

		# Обрабатываем результат в зависимости от того, что возвращает new_dialog
		# Если new_dialog возвращает список
		if isinstance(result, list):
			answer = result[0] if len(result) > 0 else "Не удалось получить ответ"
			scene_name = result[1] if len(result) > 1 else "root"
			intent_values = result[2] if len(result) > 2 else []
			scene_intents = result[3] if len(result) > 3 else []
			all_intents = result[5] if len(result) > 5 else []
		else:
			# Если возвращает строку или словарь
			answer = str(result)
			scene_name = "root"
			all_intents = []

		elapsed_time = time.time() - start_time
		elapsed_ms = round(elapsed_time * 1000, 2)  # в миллисекундах
		print(f"[TIMING] Ответ на вопрос '{question[:50]}...' | {elapsed_ms} мс")

		return {
			"success": True,
			"answer": answer,
			"scene": scene_name,
			"intents": all_intents,
			"context": None
		}

	except Exception as e:
		print(f"[ERROR] Ошибка в чате с деревом: {e}")
		import traceback
		traceback.print_exc()
		return JSONResponse(
			status_code=500,
			content={"detail": f"Ошибка обработки запроса: {str(e)}"}
		)


def print_graph_to_console():
	"""Вывод графа в консоль"""
	print("\n" + "=" * 80)
	print("📊 ГРАФ ЗНАНИЙ")
	print("=" * 80)

	try:
		graph = dialog.get_graph_from_storage(application.storage)
		if graph is None:
			print("❌ Граф не найден")
			return

		all_nodes = graph.get_all_nodes()
		print(f"📈 Всего узлов: {len(all_nodes)}")
		print("-" * 80)

		# Выводим все узлы
		for node_id, node_data in all_nodes.items():
			print(f"\n🔹 {node_id}")
			print(f"   Тип: {node_data.get('type', [])}")

			# Документы
			docs = node_data.get('documents', {})
			if docs:
				print(f"   Документы: {list(docs.keys())}")

			# Связи
			for rel_type in ['in', 'out']:
				if rel_type in node_data:
					print(f"   {rel_type.upper()}:")
					for rel_key, rel_values in node_data[rel_type].items():
						if isinstance(rel_values, list):
							print(f"      {rel_key}: {rel_values}")
						else:
							print(f"      {rel_key}: {rel_values}")

		print("\n" + "=" * 80)
		print("✅ Вывод графа завершен")
		print("=" * 80)

	except Exception as e:
		print(f"❌ Ошибка: {e}")


# Вызов функции (можно разместить в нужном месте)
#print_graph_to_console()