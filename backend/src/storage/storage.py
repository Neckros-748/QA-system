# from backend.src.common.annotation.annotator import Annotator
from backend.src.storage.database.storage import Storage


class AppStorage:
	def __init__(self):
		self.storage: Storage = Storage()



	# def set_annotator(
	# 		self,
	# 		annotator: Annotator,
	# ):
	# 	self.storage.set_annotator(annotator)


	# -------------------------
	# Search document
	# -------------------------



# 	def request(
# 			self,
# 			word_chunks: List[WordChunk],
# 			embedding:   np.ndarray,
# 			top_k:       int = 10,
# 	):
# 		# ======================================================================
# 		# Шаг 1: Графовый поиск
# 		# ======================================================================
#
# 		result: List[Dict[str, Any]] = self.graph.request(word_chunks)
#
# 		contains: Dict[str, Any] = {}
# 		for chunk in result:
# 			for key, value in chunk["contains"].items():
# 				if key in contains:
# 					self._append_unique(contains[key], value)
# 				else:
# 					contains[key] = value
#
# 		for key, value in contains.items():
# 			self.database.set_active(key, value, True)
#
# 		res = self.database.search(embedding, active_only=True)
# 		self.database.clear_active()
#
# 		# ======================================================================
# 		# Шаг 2: Embedding + BM25
# 		# ======================================================================
#
# 		return res





# 		self.graph    = GraphStorage()
# 		self.database = PostgresStore()
# 		# cur.execute("SET ivfflat.probes = 10;")
# 		# embedding   vector(384),
#  # "data/graph/graph_view.html"
#
# 		self.lock = threading.RLock()
#
#
# 	# -------------------------
# 	# Upsert document (Insert / Update)
# 	# -------------------------
#
# 	def upsert(
# 			self,
# 			data:        Dict[str, Any],
# 			word_chunks: Dict[str, List[WordChunk]],
# 			embeddings:  Dict[str, np.ndarray],
# 	):
# 		self.graph.upsert(data, word_chunks)
# 		self.database.upsert(data, embeddings, False)
#
#
# 	# -------------------------
# 	# Delete document
# 	# -------------------------
#
#
#
# 	@staticmethod
# 	def _append_unique(
# 			target: List[str],
# 			value:  List[str] | str,
# 	) -> None:
# 		if isinstance(value, list):
# 			for v in value:
# 				if v not in target:
# 					target.append(v)
# 		elif isinstance(value, str):
# 			if value not in target:
# 				target.append(value)
#
#
#
# 	# g = app.storage.graph.search(word_chunks)
#
# 	# embedding: np.ndarray = app.annotator.encoder.process(query)
# 	#
# 	# res = app.storage.database.search(embedding, active_only=False)
#
# # if title or content:
# # 	embeddings[cur.get("id") + "|" + "title"] = self.encoder.process(title)
# # 	embeddings[cur.get("id") + "|" + "content"] = self.encoder.process(content)
#
#
# # id - документ
# # документ - структуру
# # word_chunk - документ / фрагмент документа
# # embedding - документ / фрагмент документа
# #
# #
# #
#
#
# #
# # app.graph.draw_graph()

