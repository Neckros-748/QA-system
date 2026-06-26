from typing import List

from spacy.tokens import Doc

from app.common.graph.nlp.extractors.noun_chunks import NounChunkExtractor
from app.common.graph.nlp.extractors.noun_subchunks import NounSubchunkExtractor
from app.common.graph.nlp.utils.noun_chunk import NounChunk


class NLPUtils:

	@staticmethod
	def merge_terms(doc: Doc) -> Doc:
		with doc.retokenize() as retokenizer:
			i = 0
			while i < len(doc) - 2:
				t1, t2, t3 = doc[i], doc[i + 1], doc[i + 2]

				if (
						t2.text == "-"
						and t1.is_alpha
						and t3.is_alpha
						and t1.whitespace_ == ""
				):
					span = doc[i: i + 3]
					retokenizer.merge(span)
					i += 1
				else:
					i += 1
		return doc

	@staticmethod
	def extract_noun_chunks(doc: Doc, include_subchunks: bool = False) -> List[NounChunk]:
		chunks: List[NounChunk] = NounChunkExtractor(doc).extract()
		subchunks: List[NounChunk] = []

		if include_subchunks:
			for chunk in chunks:
				subchunks.extend(
					NounSubchunkExtractor(chunk, True).extract()
				)
			chunks.extend(subchunks)

		chunks.sort(key=lambda c: (c.source.start, -(c.source.end - c.source.start)))
		return chunks

	@staticmethod
	def extract_noun_subchunks(chunk: NounChunk, include_single_tokens: bool = True) -> List[NounChunk]:
		chunks: List[NounChunk] = NounSubchunkExtractor(chunk, include_single_tokens).extract()
		chunks.sort(key=lambda c: (c.source.start, -(c.source.end - c.source.start)))
		return chunks
