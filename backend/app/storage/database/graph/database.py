# class Direction(Enum):
# 	NONE = 0
# 	UP   = 1
# 	DOWN = 2

# def _short_value(v: Any) -> Any:
# 	if v is None or isinstance(v, (str, int, float, bool)):
# 		return v
# 	if isinstance(v, Enum):
# 		return v.name
# 	if isinstance(v, nx.Graph):
# 		return {
# 			"graph_type": v.__class__.__name__,
# 			"nodes": v.number_of_nodes(),
# 			"edges": v.number_of_edges(),
# 		}
# 	if isinstance(v, dict):
# 		return {str(k): _short_value(val) for k, val in v.items()}
# 	if isinstance(v, (list, tuple, set)):
# 		return [_short_value(x) for x in v]
# 	if hasattr(v, "__dict__"):
# 		return _short_value(vars(v))
# 	return str(v)












# @staticmethod
# def _fragment_matches(fragment_id: str, section_id: str) -> bool:
# 	if not section_id:
# 		return True
#
# 	return (
# 		fragment_id == section_id
# 		or section_id in fragment_id
# 		or f"[{section_id}]" in fragment_id
# 	)
#
# @classmethod
# def _documents_in_scope(
# 		cls,
# 		documents: Dict[str, List[str]],
# 		document_id: Optional[str] = None,
# 		section_id: Optional[str] = None,
# ) -> Dict[str, List[str]]:
# 	result: Dict[str, List[str]] = {}
#
# 	for doc_id, fragments in (documents or {}).items():
# 		if document_id is not None and doc_id != document_id:
# 			continue
#
# 		if not isinstance(fragments, list):
# 			fragments = [fragments]
#
# 		if section_id is None:
# 			result[doc_id] = list(dict.fromkeys(fragments))
# 			continue
#
# 		matched = [
# 			fragment_id
# 			for fragment_id in fragments
# 			if cls._fragment_matches(fragment_id, section_id)
# 		]
#
# 		if matched:
# 			result[doc_id] = list(dict.fromkeys(matched))
#
# 	return result
#
# def _scope_nodes(
# 		self,
# 		all_nodes: Dict[str, Dict[str, Any]],
# 		document_id: Optional[str] = None,
# 		section_id: Optional[str] = None,
# ) -> Dict[str, Dict[str, Any]]:
# 	result: Dict[str, Dict[str, Any]] = {}
#
# 	for node_id, info in all_nodes.items():
# 		documents = self._documents_in_scope(
# 			info.get("documents", {}),
# 			document_id=document_id,
# 			section_id=section_id,
# 		)
#
# 		if documents:
# 			item = {
# 				**info,
# 				"documents": documents,
# 			}
# 			result[node_id] = item
#
# 	return result
#
# def _parent_component(
# 		self,
# 		seed_ids: Set[str],
# 		all_nodes: Dict[str, Dict[str, Any]],
# 		scope_ids: Set[str],
# ) -> Set[str]:
# 	"""
# 	Расширение по parent-связям в обе стороны:
# 	in.parent + out.parent
# 	"""
# 	result = set(seed_ids)
# 	stack = list(seed_ids)
#
# 	while stack:
# 		node_id = stack.pop()
# 		info = all_nodes.get(node_id)
# 		if not info:
# 			continue
#
# 		related = set(info["in"]["parent"]) | set(info["out"]["parent"])
#
# 		for nxt in related:
# 			if nxt in scope_ids and nxt not in result:
# 				result.add(nxt)
# 				stack.append(nxt)
#
# 	return result
#
# def _neighbor_nodes(
# 		self,
# 		seed_ids: Set[str],
# 		all_nodes: Dict[str, Dict[str, Any]],
# 		scope_ids: Set[str],
# ) -> Set[str]:
# 	"""
# 	Соседи по link-связям:
# 	in.link + out.link
# 	"""
# 	result = set(seed_ids)
#
# 	for node_id in list(seed_ids):
# 		info = all_nodes.get(node_id)
# 		if not info:
# 			continue
#
# 		related = set(info["in"]["link"]) | set(info["out"]["link"])
#
# 		for nxt in related:
# 			if nxt in scope_ids:
# 				result.add(nxt)
#
# 	return result
#
# def _select_by_predicate(
# 		self,
# 		predicate,
# 		document_id: Optional[str] = None,
# 		section_id: Optional[str] = None,
# 		include_parents: bool = False,
# ) -> Dict[str, Dict[str, Any]]:
# 	all_nodes = self.get_all_nodes()
# 	scoped_nodes = self._scope_nodes(
# 		all_nodes,
# 		document_id=document_id,
# 		section_id=section_id,
# 	)
#
# 	scope_ids = set(scoped_nodes.keys())
# 	seed_ids = {
# 		node_id
# 		for node_id, info in scoped_nodes.items()
# 		if predicate(node_id, info)
# 	}
#
# 	if include_parents:
# 		seed_ids = self._parent_component(seed_ids, all_nodes, scope_ids)
#
# 	return {node_id: scoped_nodes[node_id] for node_id in seed_ids}


