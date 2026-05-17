from __future__ import annotations

import math
import json
import time
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
import requests

# import nltk
# from nltk.tokenize import word_tokenize
# from rank_bm25 import BM25Okapi
# import spacy
from openai import OpenAI, AsyncOpenAI

from backend.src.config import settings


class LLMClient:
	def __init__(self):
		self.client = OpenAI(
			api_key  = settings.LLM_API_KEY,
			base_url = settings.LLM_BASE_URL,
		)

	def generate(
			self,
			system_prompt: str,
			user_prompt: str,
			max_tokens: int = 256,
			temperature: float = 0.3,
			top_p: float = 0.95
	) -> Dict[str, Any]:
		try:
			response = {
				"model": settings.LLM_MODEL,
				"messages": [
					# system, user, assistant
					{
						"role":    "system",
						"content": system_prompt
					},
					{
						"role":    "user",
						"content": user_prompt
					},
				],
				"max_tokens":  max_tokens,
				"temperature": temperature,
				"top_p":       top_p,
				"extra_body": {
					"enable_thinking": False
				},
			}

			response = self.client.chat.completions.create(
				**response,
			)
		except Exception as e:
			raise

		t_start = time.time()

		resp = response.choices[0].message.content

		t_end = time.time()

		return {}



		# 	content = response.choices[0].message.content
		# 	elapsed = time.time() - t0
		# 	usage = response.usage
		# 	logger.info(
		# 		f"LLM response: {elapsed:.1f}s, "
		# 		f"tokens in={usage.prompt_tokens} out={usage.completion_tokens}, "
		# 		f"finish={response.choices[0].finish_reason}, "
		# 		f"response_len={len(content or '')}"
		# 	)
		# 	return content
		#
		# def generate(
		# 		self,
		# 		prompt: str,
		# 		*,
		# 		system_prompt: Optional[str] = None,
		# 		force_json: bool = False,
		# 		max_tokens: int = 4000,
		# 		temperature: float = 0.0,
		# 		**kwargs,
		# ) -> str:
		# 	sys_prompt = system_prompt or (
		# 		"You are a deterministic formal parser. "
		# 		"Return STRICTLY valid JSON. Do NOT output any text outside JSON."
		# 		if force_json else
		# 		"You are a domain expert."
		# 	)
		# 	return self._call(
		# 		system_prompt=sys_prompt,
		# 		user_content=prompt,
		# 		max_tokens=max_tokens,
		# 		temperature=temperature,
		# 	)
		#
		# def extract_json(
		# 		self,
		# 		prompt: str,
		# 		*,
		# 		system_prompt: Optional[str] = None,
		# 		force_json: bool = True,
		# 		max_tokens: int = 4000,
		# 		temperature: float = 0.0,
		# 		**kwargs,
		# ) -> Dict[str, Any]:
		# 	text = self.generate(
		# 		prompt=prompt,
		# 		system_prompt=system_prompt,
		# 		force_json=force_json,
		# 		max_tokens=max_tokens,
		# 		temperature=temperature,
		# 	)
		# 	return _safe_json(text)
		#
		# def extract_guideline(
		# 		self,
		# 		text: str,
		# 		prompt: str,
		# 		*,
		# 		force_json: bool = True,
		# 		max_tokens: int = 64000,
		# 		temperature: float = 0.3,
		# 		**kwargs,
		# ) -> Dict[str, Any]:
		# 	full_prompt = prompt.replace("{{TEXT}}", text)
		# 	return self.extract_json(
		# 		prompt=full_prompt,
		# 		force_json=force_json,
		# 		max_tokens=max_tokens,
		# 		temperature=temperature,