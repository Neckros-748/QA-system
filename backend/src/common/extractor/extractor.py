from typing import Iterable, List

import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span, Token
from spacy import displacy

from backend.src.common.annotation.nlp.nlp_utils import NLPUtils
from backend.src.config import AnnotatorConfig


class ExtractorWrapper:
	def __init__(
			self,
			config: AnnotatorConfig,
	) -> None:
		self.config: AnnotatorConfig = config

		self.model: Language = spacy.load(
			config.model_name["extractor"],
			disable = self.config.disable if self.config.disable else []
		)

	def process(
			self,
			text: str,
	) -> Doc:
		doc = self.model(
			text
		)
		return NLPUtils.merge_terms(doc)

	def pipe(
			self,
			texts: List[str],
	) -> Iterable[Doc]:
		docs =  self.model.pipe(
			texts,
			batch_size = self.config.batch_size,
			n_process  = self.config.n_process,
		)
		for doc in docs:
			yield NLPUtils.merge_terms(doc)
