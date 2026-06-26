from typing import List, Tuple, Set

from spacy.tokens import Token

from app.common.graph.nlp.utils.text_chunk import TokenSnapshot


def is_valid_token(token: Token | TokenSnapshot) -> bool:
	if token.is_punct:
		return False
	if isinstance(token, Token):
		if token.dep_ in {"amod", "nmod"}:
			if token.pos_ == "ADJ" and "Cmp" in token.morph.get("Degree", []):
				return False
			if token.pos_ == "ADV":
				return False
	else:
		if token.is_punct:
			return False
		if token.dep in {"amod", "nmod"}:
			if token.pos == "ADJ" and "Cmp" in token.morph.get("Degree", []):
				return False
			if token.pos == "ADV":
				return False
	return True

def split_chunk_ids(token_ids: Set[int]) -> List[Tuple[int, int]]:
	token_ids = sorted(token_ids)
	if not token_ids:
		return []
	spans = []
	start = prev = token_ids[0]
	for i in token_ids[1:]:
		if i == prev + 1:
			prev = i
		else:
			spans.append((start, prev + 1))
			start = prev = i
	spans.append((start, prev + 1))
	return spans
