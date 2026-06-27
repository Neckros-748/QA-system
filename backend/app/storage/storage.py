from pathlib import Path
from typing import Dict, List, Any, Optional

from app.common.graph.nlp.utils.word_chunk import WordChunk
from app.common.graph.graph_index import GraphIndex
from app.common.lexical.lexical_index import LexIndex
from app.common.vector.vector_index import VecIndex
from app.docs.file.file_utils import FileIO
from app.config import Config


class Storage:
	def __init__(
			self,
			config: Config,
	):
		# Список документов
		self.documents: list[dict[str, Any]] = []
		self.config:    Config               = config

		# Графовый индекс (Всегда включен)
		self.graph_index: GraphIndex = GraphIndex(config)

		# Лексический индекс
		self.lex_index: Optional[LexIndex] = None
		if self.config.use_lex_index:
			self.lex_index: Optional[LexIndex] = LexIndex(config)
			self.lex_index.load()

		# Векторный индекс
		self.vec_index: Optional[VecIndex] = None
		if self.config.use_vec_index:
			self.vec_index: Optional[VecIndex] = VecIndex(config)
			self.vec_index.load()

		# Загружаем список документов
		self.load()

	# ==========================================================================
	# Сохранение / Загрузка документов
	# ==========================================================================

	def save(self, path: Optional[Path] = None) -> None:
		save_path = path or Path(self.config.storage_path).parent / "documents.json"

		data_to_save = { "documents": self.documents, "version": 1, }
		FileIO.write_json(str(save_path), data_to_save, indent=2)

	def load(self, path: Optional[Path] = None) -> None:
		load_path = path or Path(self.config.storage_path).parent / "documents.json"
		if load_path is None or not load_path.exists():
			return
		try:
			data = FileIO.read_json(str(load_path))
			self.documents = data.get("documents", [])
		except Exception as e:
			print(f"Ошибка загрузки документов: {e}")
			self.documents = []

	def save_data(
			self,
			data:     Dict[str, Any],
			metadata: Dict[str, Any],
	):
		FileIO.write(
			Path(self.config.storage_path).parent / "storage" / f"{metadata['id']}.json",
			data
		)

	def load_data(
			self,
	):

		pass

	# ==========================================================================
	# Upsert document (Insert / Update)
	# ==========================================================================

	def upsert(
			self,
			data:        Dict[str, Any],
			word_chunks: Dict[str, List[WordChunk]],
	):
		self.graph_index.upsert(
			data, word_chunks
		)
		if "sections" in data:
			data_meta = {
				"id":         data["id"],
				"title":      data["title"],
				"created_at": data["created_at"],
			}
			self._upsert_section(
				data_meta, data
			)

		self.save_data(data, self.documents[0])

	def _upsert_section(
			self,
			data_meta: Dict[str, Any],
			section:   Dict[str, Any],
	):
		paragraphs = section.get("paragraphs", [])
		if paragraphs:
			self._upsert_paragraph(
				data_meta, section, paragraphs,
			)

		sections = section.get("sections", [])
		if sections:
			for it in sections:
				self._upsert_section(data_meta, it)

	def _upsert_paragraph(
			self,
			data_meta:  Dict[str, Any],
			section:    Dict[str, Any],
			paragraphs: List[Dict[str, Any]],
	):
		texts: List[str] = [
			p.get("text", "") for p in paragraphs
		]

		title:   str = section.get("title", "")
		content: str = "\n".join(texts)

		# ======================================================================
		# Выделение параграфов
		# ======================================================================

		texts: List[Dict[str, Any]] = []
		if title or content:
			if section["id"] != "sct_h0:1":
				texts.append({
					"doc_id": data_meta["id"],
					"id":     section["id"],
					"text":   f"{title}\n{content}".strip(),
				})

			for p in paragraphs:
				texts.append({
					"doc_id": data_meta["id"],
					"id":     section["id"],
					"text":   p["text"],
				})

		if texts:
			if self.config.use_lex_index:
				self.lex_index.add_texts(texts, text_field="text")
				self.lex_index.save()
			if self.config.use_vec_index:
				self.vec_index.add_texts(texts, text_field="text")
				self.vec_index.save()

	@staticmethod
	def normalize_scores(scores: List[float]) -> List[float]:
		if not scores:
			return []
		min_s = min(scores)
		max_s = max(scores)
		if max_s == min_s:
			return [0.5] * len(scores)
		return [
			(s - min_s) / (max_s - min_s)
			for s in scores
		]

	def request(
			self,
			query:       str,
			word_chunks: List[WordChunk],
			weights:     Optional[Dict[str, float]] = None,
	        top_k:       int                        = 10,
	) -> List[Dict[str, Any]]:
		if weights is None:
			weights = {'graph': 0.2, 'lex': 0.4, 'vec': 0.4}

		total = sum(weights.values())
		if total == 0:
			total = 1
		w = {k: v / total for k, v in weights.items()}

		graph_results = self.graph_index.search(word_chunks, top_k=top_k * 2)
		lex_results   = self.lex_index.search(query, top_k=top_k * 2) if self.lex_index else []
		vec_results   = self.vec_index.search(self.vec_index.process(query), top_k=top_k * 2) if self.vec_index else []
		combined      = {}

		def add_results(results, index_name):
			for item in results:
				fid = item.get('id')
				if not fid:
					continue
				doc_id = item.get('metadata', {}).get('doc_id')
				if not doc_id:
					continue
				score = item.get('score', 0)
				key = f"{doc_id}:{fid}"
				if key not in combined:
					combined[key] = {
						'doc_id': doc_id,
						'id': fid,
						'scores': {
							'graph': 0,
							'lex':   0,
							'vec':   0,
						}
					}
				combined[key]['scores'][index_name] = score

		add_results(graph_results, 'graph')
		if lex_results:
			add_results(lex_results, 'lex')
		if vec_results:
			add_results(vec_results, 'vec')

		if not combined:
			return []

		index_scores = {name: [] for name in weights.keys()}
		for data in combined.values():
			for name in weights.keys():
				index_scores[name].append(data['scores'].get(name, 0))

		normalized = {}
		for name, scores in index_scores.items():
			normalized[name] = self.normalize_scores(scores)

		final_results = []
		for i, (key, data) in enumerate(combined.items()):
			final_score = 0.0
			for name in weights.keys():
				final_score += w[name] * normalized[name][i]
			final_results.append({
				'doc_id': data['doc_id'],
				'id':     data['id'],
				'score':  final_score,
				'scores': {
					'graph': data['scores']['graph'],
					'lex':   data['scores']['lex'],
					'vec':   data['scores']['vec'],
				},
			})

		final_results.sort(key=lambda x: x['score'], reverse=True)
		return final_results[:top_k]

	# def request(
	# 		self,
	# 		query:       str,
	# 		word_chunks: List[WordChunk],
	# 		top_k:       int = 10,
	# ):
	# 	return {
	# 		"graph_index": self.graph_index.search(word_chunks, top_k=top_k),
	# 		"lex_index":   self.lex_index.search(query, top_k=top_k) if self.config.use_lex_index else None,
	# 		"vec_index":   self.vec_index.search(self.vec_index.process(query), top_k=top_k) if self.config.use_vec_index else None,
	# 	}




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
