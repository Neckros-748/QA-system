# import networkx as nx
# from typing import List, Optional
# from spacy.tokens import Doc, Span



# # import spacy
# # from spacy import displacy
# # from spacy.tokens import Doc, Span, Token
# # import networkx as nx
#
# from config import settings
#
#
# def build_content_graph(doc: dict):
#
# 	G = nx.DiGraph()
#
# 	def _build_section(section: dict):
# 		for sec in section.get("sections", []):
# 			_build_section(sec)
#
# 		for par in section.get("paragraphs", []):
# 			_build_paragraph(par)
#
# 	def _build_paragraph(paragraph: dict):
# 		text = paragraph["src_text"]
# 		doc  = paragraph["proc_text"]
#
# 		chunks: List[NounChunk] = process_text(doc)
#
#
# 		# for ch in chunks:
# 		# 	_add_chunk_node(doc_id, paragraph["id"], ch)
# 		#
# 		# for ch in chunks:
# 		# 	_add_chunk_edge(doc_id, paragraph["id"], ch, chunks)
#
# 		# list_clusters = []
# 		#
# 		# # Обработка содержимого документа с помощью обработки естественного языка
# 		# content = get_document_content(self.documents_folder, document)
# 		# doc = self.nlp(content)
# 		#
# 		# # Обход предложений в документе и создание кластеров
# 		# for i, sent in enumerate(doc.sents):
# 		# 	clusters, list_conn = create_clusters(doc, i, sent)
# 		# 	clusters = self.__process_data_auto_allocation__(clusters, list_conn)
# 		# 	list_clusters += clusters
# 		#
# 		# return doc, list_clusters




# 	# def _add_chunk_node(doc_id: str, parent_id: str, chunk: NounChunk):
# 	# 	id = get_chunk_id(doc_id, parent_id, chunk)
# 	#
# 	# 	if id in G:
# 	# 		print("node ===", id, chunk)
# 	# 	else:
# 	# 		G.add_node(
# 	# 			id,
# 	# 			label=f"{id} :: {chunk.span.text}",
# 	# 			type=f"CHUNK::T{chunk.c_type}",
# 	# 			level=chunk.c_level,
# 	# 		)
# 	#
# 	# def _add_chunk_edge(doc_id: str, parent_id: str, chunk: NounChunk, chunks: List[NounChunk]):
# 	# 	if chunk.c_type == 1:
# 	# 		parent_chunk  = None
# 	# 		best_span_len = None
# 	#
# 	#
# 	# 		for other in chunks:
# 	# 			if other is chunk or other.c_type != 1:
# 	# 				continue
# 	#
# 	# 			# проверка вложенности
# 	# 			if (other.span.start <= chunk.span.start and
# 	# 					other.span.end >= chunk.span.end):
# 	#
# 	# 				span_len = other.span.end - other.span.start
# 	#
# 	# 				# выбираем минимального родителя
# 	# 				if best_span_len is None or span_len < best_span_len:
# 	# 					best_span_len = span_len
# 	# 					parent_chunk = other
# 	#
# 	# 		chunk_id  = get_chunk_id(doc_id, parent_id, chunk)
# 	# 		if parent_chunk:
# 	# 			parent_id = get_chunk_id(doc_id, parent_id, parent_chunk)
# 	#
# 	# 			G.add_edge(
# 	# 				parent_id,
# 	# 				chunk_id,
# 	# 				type="chunk"  # связь между noun_chunk
# 	# 			)
# 	#
# 	# 		else:
# 	# 			# опционально: привязка к paragraph
# 	# 			G.add_edge(
# 	# 				parent_id,
# 	# 				chunk_id,
# 	# 				type="root_chunk"
# 	# 			)
# 	#
# 	#
# 	# 		pass
# 	# 	else:
# 	# 		if chunk.parent is None:
# 	# 			return
# 	# 		parent_id = get_chunk_id(doc_id, parent_id, chunk.parent)
# 	# 		chunk_id  = get_chunk_id(doc_id, parent_id, chunk)
# 	# 		G.add_edge(
# 	# 			parent_id,
# 	# 			chunk_id,
# 	# 			type="sub" # SUBCHUNK
# 	# 		)
#
# 	for sec in doc.get("sections", []):
# 		_build_section(sec)
#
# 	return G
#
#
# # paragraph["src_text"] = text
# # paragraph["proc_text"] = doc
#
# def get_chunk_id(doc_id: str, parent_id: str, chunk: NounChunk) -> str:
# 	return f"{doc_id}::[{chunk.span.text}, {chunk.span.start}:{chunk.span.end}]-T{chunk.c_type}-L{chunk.c_level}"
# 	# return f"{doc_id}::{parent_id}::[{chunk.span.text}, {chunk.span.start}:{chunk.span.end}]-T{chunk.c_type}-L{chunk.c_level}"




# def process_text(doc: Doc) -> List[NounChunk]:
# 	chunks: List[NounChunk] = NLPUtils.noun_chunks(doc, True)
#
# 	# print(doc)
# 	return chunks









#		 terms = set()
#
#
#			 terms.add(ent.text.lower())
#
#		 # 2. Существительные + noun chunks
#		 for chunk in doc.noun_chunks:
#			 terms.add(chunk.text.lower())
#
#		 # fallback: отдельные существительные
#		 for token in doc:
#			 if token.pos_ in ["NOUN", "PROPN"]:
#				 terms.add(token.lemma_.lower())
#
#		 return list(terms)
#
#	 # --------------------------
#	 # 🔹 Добавление узла
#	 # --------------------------
#	 def add_node(self, term, doc_id, sentence_id, text):
#		 if not self.graph.has_node(term):
#			 self.graph.add_node(term, occurrences=[])
#
#		 self.graph.nodes[term]["occurrences"].append({
#			 "doc_id": doc_id,
#			 "sentence_id": sentence_id,
#			 "text": text
#		 })
#
#		 self.node_index[term].append((doc_id, sentence_id))
#
#	 # --------------------------
#	 # 🔹 Добавление документа
#	 # --------------------------
#	 def add_document(self, document):
#		 doc_id = document["id"]
#
#		 prev_terms = None
#
#		 for section in document["sections"]:
#			 for paragraph in section["paragraphs"]:
#				 for sentence in paragraph["sentences"]:
#
#					 sent_id = sentence["id"]
#					 text = sentence["text"]
#
#					 terms = self.extract_terms(text)
#
#					 # 1. Добавляем узлы
#					 for term in terms:
#						 self.add_node(term, doc_id, sent_id, text)
#
#					 # 2. Связи внутри предложения
#					 for t1 in terms:
#						 for t2 in terms:
#							 if t1 != t2:
#								 self.graph.add_edge(
#									 t1, t2,
#									 type="co_occurrence"
#								 )
#
#					 # 3. Связи между предложениями
#					 if prev_terms:
#						 for t1 in prev_terms:
#							 for t2 in terms:
#								 self.graph.add_edge(
#									 t1, t2,
#									 type="next_sentence"
#								 )
#
#					 # 4. Простая обработка сокращений
#					 if "–" in text:
#						 parts = text.split("–")
#						 if len(parts) == 2:
#							 abbr = parts[0].strip().lower()
#							 full = parts[1].strip(" ;").lower()
#
#							 self.graph.add_edge(
#								 abbr, full,
#								 type="definition"
#							 )
#
#					 prev_terms = terms
#
#	 # --------------------------
#	 # 🔍 Поиск по графу
#	 # --------------------------
#	 def search(self, query, top_k=5):
#		 query_terms = self.extract_terms(query)
#
#		 scores = defaultdict(int)
#
#		 for q in query_terms:
#			 if q in self.graph:
#				 # ближайшие соседи
#				 neighbors = self.graph.neighbors(q)
#
#				 for n in neighbors:
#					 for occ in self.graph.nodes[n]["occurrences"]:
#						 key = (occ["doc_id"], occ["sentence_id"], occ["text"])
#						 scores[key] += 1
#
#		 # сортировка
#		 ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
#
#		 return [r[0] for r in ranked[:top_k]]
#
#	 # --------------------------
#	 # 🔍 Расширенный поиск (с обходом графа)
#	 # --------------------------
#	 def search_with_graph_walk(self, query, depth=2):
#		 query_terms = self.extract_terms(query)
#
#		 visited = set()
#		 frontier = set(query_terms)
#
#		 for _ in range(depth):
#			 next_frontier = set()
#
#			 for node in frontier:
#				 if node in self.graph:
#					 for neighbor in self.graph.neighbors(node):
#						 if neighbor not in visited:
#							 next_frontier.add(neighbor)
#
#			 visited.update(frontier)
#			 frontier = next_frontier
#
#		 results = []
#
#		 for node in visited:
#			 if node in self.graph:
#				 results.extend(self.graph.nodes[node]["occurrences"])
#
#		 return results





# annotated_text

# import json
# import spacy
# from spacy import displacy
# from spacy.tokens import Span
#
# from spacy.symbols import NOUN, PROPN, PRON, ADP, ADJ, PUNCT, PART
# from spacy.symbols import VERB
# from enum import Enum



# def pipeline(text):
# 	# https://dns.comss.one/dns-query
# 	# spacy.explain
#
# 	doc = nlp(text)
#
# 	# displacy.serve(doc, style="dep")
#
# 	displacy.serve(doc, style="ent")
#
# 	# sentence_spans = list(doc.sents)
# 	# displacy.serve(sentence_spans, style="dep")
#
# 	print("Pipeline:", nlp.pipe_names)
# 	for token in doc:
# 		if token.pos_ != "SPACE" and token.tag_ != "SPACE":
# 			print(f"{token.text:<20} | {token.lemma_:<20} | {token.tag_:<10} | {token.dep_:<10} | {token.shape_:<10} | {token.is_alpha} {token.is_stop}")
#
# 			print(f"Морфология:			{token.pos_:<10} | {token.morph}")
# 			# token.morph.get("PronType")
# 		else:
# 			print()
#
# 	# for chunk in doc.noun_chunks:
# 	# 	print(chunk.text, chunk.root.text, chunk.root.dep_, chunk.root.head.text)
#
# 	for token in doc:
# 		if token.pos_ != "SPACE" and token.tag_ != "SPACE":
# 			print(f"{token.text:<20} | {token.dep_:<10} | {token.head.text:<20} | {token.pos_:<10} | "
# 				  f"{[child if child.pos_ != 'SPACE' and child.tag_ != 'SPACE' else '*' for child in token.children]}")
# 		else:
# 			print()
#
#
# 	# verbs = set()
# 	# for possible_subject in doc:
# 	# 	if (possible_subject.dep == doc.vocab.strings["nsubj"] or possible_subject.dep == doc.vocab.strings["nsubj:pass"]) and possible_subject.head.pos == VERB:
# 	# 		verbs.add(possible_subject.head)
# 	# print(verbs)
#
# 	# verbs = []
# 	# for possible_verb in doc:
# 	# 	if possible_verb.pos == VERB:
# 	# 		for possible_subject in possible_verb.children:
# 	# 			if possible_subject.dep == doc.vocab.strings["nsubj"] or possible_subject.dep == doc.vocab.strings["nsubj:pass"]:
# 	# 				verbs.append(possible_verb)
# 	# 				break
# 	# print(verbs)
#
# 	# root = [token for token in doc if token.head == token][0]
# 	# subject = list(root.lefts)[0]
# 	# for descendant in subject.subtree:
# 	# 	assert subject is descendant or subject.is_ancestor(descendant)
# 	# 	print(descendant.text, descendant.dep_, descendant.n_lefts,
# 	# 		  descendant.n_rights,
# 	# 		  [ancestor.text for ancestor in descendant.ancestors])
#
# 	# span = doc[doc[2].left_edge.i: doc[2].right_edge.i + 1]
# 	# with doc.retokenize() as retokenizer:
# 	# 	retokenizer.merge(span)
# 	# for token in doc:
# 	# 	print(token.text, token.pos_, token.dep_, token.head.text)
#
# 	# for ent in doc.ents:
# 	# 	print(ent.text, ent.start_char, ent.end_char, ent.label_)
#
# 	# # document level
# 	# ents = [(e.text, e.start_char, e.end_char, e.label_) for e in doc.ents]
# 	# print(ents)
# 	#
# 	# # token level
# 	# ent_san = [doc[0].text, doc[0].ent_iob_, doc[0].ent_type_]
# 	# ent_francisco = [doc[1].text, doc[1].ent_iob_, doc[1].ent_type_]
# 	# print(ent_san)  # ['San', 'B', 'GPE']
# 	# print(ent_francisco)  # ['Francisco', 'I', 'GPE']
#
# 	ents = [(e.text, e.start_char, e.end_char, e.label_) for e in doc.ents]
# 	print('Before', ents)
# 	# The model didn't recognize "fb" as an entity :(
#
# 	# Create a span for the new entity
# 	fb_ent = Span(doc, 0, 1, label="ORG")
# 	orig_ents = list(doc.ents)
#
# 	# Option 1: Modify the provided entity spans, leaving the rest unmodified
# 	doc.set_ents([fb_ent], default="unmodified")
#
# 	# Option 2: Assign a complete list of ents to doc.ents
# 	doc.ents = orig_ents + [fb_ent]
#
# 	ents = [(e.text, e.start, e.end, e.label_) for e in doc.ents]
# 	print('After', ents)
#
# pipeline(text)










# def extract_terms(text):
# 	for sent in doc.sents:
# 		terms = []
# 		for chunk in create_clusters_token(doc):
# 			terms.append(chunk)
#
# 		print(terms)



# class Token:
# 	def __init__(self, elem):
# 		self.index	 = elem.i
# 		self.text	  = elem.text
# 		self.lemma	 = elem.lemma_
# 		self.con_index = elem.head.i
# 		self.con_dep   = elem.dep_
#
# 	def __repr__(self):
# 		return f"{self.text}"
#
# class Cluster:
# 	def __init__(self):
# 		self.tokens  = []
#
# 	def __repr__(self):
# 		return f"{self.tokens}"
#
# 	def append(self, token):
# 		self.tokens.append(token)
#
# 	def insert(self, token):
# 		self.tokens.append(token)
# 		self.tokens.sort(key=lambda x: x.index)
#
# 	def remove(self, token):
# 		if token in self.tokens:
# 			self.tokens.remove(token)



# def create_clusters_token(obj):
# 	doc = obj.doc
#
# 	labels_layer_1 = ["nsubj", "dobj", "nsubjpass", "pcomp", "pobj", "dative", "appos", "attr", "ROOT"]
# 	np_deps_layer_1 = [doc.vocab.strings.add(label) for label in labels_layer_1]
#
# 	labels_layer_2 = ["amod", "nmod", "obl", "obj"]
# 	np_deps_layer_2 = [doc.vocab.strings.add(label) for label in labels_layer_2]
#
# 	conj = doc.vocab.strings.add("conj")
#
# 	seen = set()  # Множество для отслеживания уже обработанных токенов
#
#
#
# 	# Проходим по каждому слову в предложении
# 	for i, word in enumerate(doc):
# 		# Пропускаем слова, которые не являются существительными или местоимениями, или уже были обработаны
# 		if word.pos not in (NOUN, PROPN, PRON) or word.i in seen:
# 			continue
#
# 		cluster = Cluster()
# 		# cluster.append(Token(word))
#
# 		if word.dep in np_deps_layer_1: # and word.pos not in (NOUN, PROPN): # word.dep in np_deps_layer_1 or word.dep in np_deps_layer_2:
# 			if any(w.i in seen for w in word.subtree):
# 				continue
#
# 			# if word.dep in np_deps_layer_1:
# 			seen.update(j for j in range(word.left_edge.i, word.i + 1))
# 			# yield word.left_edge.i, word.i + 1, np_label
#
# 			for j in range(word.left_edge.i, word.i + 1):
# 				cluster.append(Token(doc[j]))
# 			yield cluster
#
# 		elif word.dep == conj:
#
# 			print(word.i)
#
# 	#			 head = word.head
# 	#			 while head.dep == conj and head.head.i < head.i:
# 	#				 head = head.head
# 	#			 # If the head is an NP, and we're coordinated to it, we're an NP
# 	#			 if head.dep in np_deps:
# 	#				 if any(w.i in seen for w in word.subtree):
# 	#					 continue
# 	#				 seen.update(j for j in range(word.left_edge.i, word.i + 1))
# 	#				 yield word.left_edge.i, word.i + 1, np_label
#
# 	#		 if word.dep in np_deps_layer_2:
# 	#			 if word.i == word.left_edge.i:
# 	#				 if len(list(word.head.children)) == 1:
# 	#					 seen.update(j for j in range(word.head.i, word.i + 1))
# 	#					 for j in range(word.head.i, word.i + 1):
# 	#						 cluster.append(Token(doc[j]))
# 	#				 else:
# 	#					 seen.update(j for j in range(word.i, word.i + 1))
# 	#					 for j in range(word.i, word.i + 1):
# 	#						 cluster.append(Token(doc[j]))
# 	#			 else:
# 	#				 seen.update(j for j in range(word.left_edge.i, word.i + 1))
# 	#				 for j in range(word.left_edge.i, word.i + 1):
# 	#					 cluster.append(Token(doc[j]))
#
#
#
#
# #	 # Если это не кластер, который мы ожидали, мы его пропускаем
# #	 else:
# #		 # Этап: разрешение равнозначных связей - выполнено
# #		 pass
# #
# #	 list_clusters.append(cluster)
# #
# # return list_clusters
#
#
#
# def remove_subsets_clusters(clusters):
# 	"""
# 	Функция для удаления подмножества кластеров из списка кластеров.
#
# 	Parameters:
# 	- clusters (list): Список кластеров, где каждый кластер представляет собой
# 	объект, имеющий атрибут 'index', содержащий индексы токенов кластера.
#
# 	Returns:
# 	- clusters_res (list): Список кластеров без подмножеств других кластеров.
# 	"""
# 	list_clusters = []
#
# 	for i, cluster_iter in enumerate(clusters):
# 		is_subset = False
# 		for j, cluster_ in enumerate(clusters):
# 			if i != j and set(cluster_iter.index).issubset(set(cluster_.index)):
# 				is_subset = True
# 				break
# 		if not is_subset:
# 			list_clusters.append(cluster_iter)
# 	return list_clusters


# def noun_chunks(obj):
#	 """
#	 Detect base noun phrases from a dependency parse. Works on both Doc and Span.
#	 """
#	 labels = [
#		 "nsubj",
#		 "dobj",
#		 "nsubjpass",
#		 "pcomp",
#		 "pobj",
#		 "dative",
#		 "appos",
#		 "attr",
#		 "ROOT",
#	 ]
#	 doc = obj.doc  # Ensure works on both Doc and Span.
#	 np_deps = [doc.vocab.strings.add(label) for label in labels]
#	 conj = doc.vocab.strings.add("conj")
#	 np_label = doc.vocab.strings.add("NP")
#	 seen = set()
#	 for i, word in enumerate(obj):
#		 if word.pos not in (NOUN, PROPN, PRON):
#			 continue
#		 # Prevent nested chunks from being produced
#		 if word.i in seen:
#			 continue
#		 if word.dep in np_deps or True: #and word.pos not in (NOUN, PROPN):
#			 if any(w.i in seen for w in word.subtree):
#				 continue
#			 seen.update(j for j in range(word.left_edge.i, word.i + 1))
#			 yield word.left_edge.i, word.i + 1, np_label
#		 elif word.dep == conj:
#			 head = word.head
#			 while head.dep == conj and head.head.i < head.i:
#				 head = head.head
#			 # If the head is an NP, and we're coordinated to it, we're an NP
#			 if head.dep in np_deps:
#				 if any(w.i in seen for w in word.subtree):
#					 continue
#				 seen.update(j for j in range(word.left_edge.i, word.i + 1))
#				 yield word.left_edge.i, word.i + 1, np_label








# from sentence_transformers import SentenceTransformer
#
# model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# with open("../data/doc-1.json", "r", encoding='utf-8') as my_file:
#	 file_json = my_file.read()
#
# file_data = json.loads(file_json)
# print(file_data)
