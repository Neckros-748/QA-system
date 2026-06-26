


		# self.database = PostgresStore()
		# self.graph    = GraphStorage()

		# self._lock = threading.RLock()
		#
		# self._global_index = None
		# self._global_dirty = True
		#
		# self._candidate_cache: OrderedDict[str, object] = OrderedDict()


	# # -------------------------
	# # Search document
	# # -------------------------
	#
	# def request(
	# 		self,
	# 		word_chunks: List[WordChunk],
	# 		embedding:   np.ndarray,
	# 		top_k:       int = 10,
	# ) -> Dict[str, Any]:
	#
	# 	# ======================================================================
	# 	# Шаг 1: Графовый поиск
	# 	# ======================================================================
	#
	# 	result: List[Dict[str, Any]] = self.graph.request(word_chunks)
	#
	# 	contains: Dict[str, Any] = {}
	# 	for chunk in result:
	# 		for key, value in chunk["contains"].items():
	# 			if key in contains:
	# 				__append_unique__(contains[key], value)
	# 			else:
	# 				contains[key] = value
	#
	# 	for key, value in contains.items():
	# 		self.database.set_active(key, value, True)
	#
	# 	# ======================================================================
	# 	# Шаг 2: Embedding + BM25
	# 	# ======================================================================
	#
	# 	res = self.database.search(embedding, active_only=True, limit=top_k)
	# 	self.database.clear_active()
	#
	# 	# ======================================================================
	# 	# Шаг 3: Дополнение результатов
	# 	# ======================================================================
	#
	# 	def _update_data(node: Dict[str, Any]):
	# 		node_id: str = f"({data.get('id')}:{node.get('id')})"
	#
	# 		if node_id in result:
	# 			if node.get('id').startswith("sct"):
	# 				result[node_id]["text"] = node["title"] + "\n"
	# 				for p in node.get("paragraphs", []):
	# 					result[node_id]["text"] += p["text"] + "\n"
	# 			elif node.get('id').startswith("prg"):
	# 				result[node_id]["text"] = node["text"]
	#
	# 		# Paragraph
	# 		for p in node.get("paragraphs", []):
	# 			_update_data(p)
	#
	# 		# Section
	# 		for s in node.get("sections", []):
	# 			_update_data(s)
	#
	# 	result: Dict[str, Any] = {}
	# 	for r in res:
	# 		result[f"({r[0]}:{r[1]})"] = {
	# 			"document": r[0],
	# 			"target":   r[1],
	# 			"score":    r[2],
	# 		}
	#
	# 	data = FileIO.read(self.file_path)
	# 	_update_data(data)
	#
	# 	return result
	#
	#
	# # -------------------------
	# # Search data
	# # -------------------------
	#
	# # def request_nodes(self) -> Dict[str, Any]:
	# # 	result: Dict[str, Any] = self.graph.get_all_nodes()
	# #
	# # 	# for node in self.graph.get_nodes():
	# #
	# #
	# #
	# #
	# #
	# #
	# #
	# #
	# # 	return result
	#
	# # -------------------------
	# # Upsert document (Insert / Update)
	# # -------------------------
	#

	#
	#
	# # ==========================================================================
	# # Вспомогательные методы
	# # ==========================================================================
	#
	# # def add_texts(self, ids: Sequence[str]) -> None:
	# # 	"""Добавляет тексты в список поиска."""
	# #
	# # 	self.storage.set_active(ids, active=True)
	# # 	self._mark_dirty()
	# # 	self._clear_candidate_cache()
	#
	#
	#
	# # def _mark_dirty(self) -> None:
	# # 	with self._lock:
	# # 		self._global_dirty = True
	# #
	# # def _clear_candidate_cache(self) -> None:
	# # 	with self._lock:
	# # 		self._candidate_cache.clear()
	#
	#
	#
	# 	# # ======================================================================
	# 	# # Шаг 1: Графовый поиск
	# 	# # ======================================================================
	# 	#
	# 	# result: List[Dict[str, Any]] = self.graph.request(word_chunks)
	# 	#
	# 	# contains: Dict[str, Any] = {}
	# 	# for chunk in result:
	# 	# 	for key, value in chunk["contains"].items():
	# 	# 		if key in contains:
	# 	# 			__append_unique__(contains[key], value)
	# 	# 		else:
	# 	# 			contains[key] = value
	# 	#
	# 	# for key, value in contains.items():
	# 	# 	self.database.set_active(key, value, True)
	# 	#
	# 	# res = self.database.search(embedding, active_only=True)
	# 	# self.database.clear_active()
	# 	#
	# 	# # ======================================================================
	# 	# # Шаг 2: Embedding + BM25
	# 	# # ======================================================================
