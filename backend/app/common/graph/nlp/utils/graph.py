from app.common.graph.nlp.utils.text_chunk import TextChunk


def is_connected(chunk: TextChunk) -> bool:
	if len(chunk.tokens) == 1:
		return True
	ids   = {t.i for t in chunk.tokens}
	graph = {t.i: set() for t in chunk.tokens}
	for t in chunk.tokens:
		h = t.head_i
		if h in ids and h != t.i:
			graph[t.i].add(h)
			graph[h].add(t.i)
	stack = [next(iter(graph))]
	seen = set(stack)
	while stack:
		cur = stack.pop()
		for nb in graph[cur]:
			if nb not in seen:
				seen.add(nb)
				stack.append(nb)
	return len(seen) == len(chunk.tokens)

def has_internal_head(chunk: TextChunk) -> bool:
	if len(chunk.tokens) == 1:
		return True
	return any(t.i == t.head_i or t.head_i in chunk.index for t in chunk.tokens)
