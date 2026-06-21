import time
from typing import Dict, Any, Optional

from openai import OpenAI

from backend.src.config import settings


class OpenAIClient:
	def __init__(self):
		self.client = OpenAI(
			api_key  = settings.LLM_API_KEY,
			base_url = settings.LLM_BASE_URL,
		)

	def generate(
			self,
			system_prompt: Optional[str]            = None,
			user_prompt:   Optional[str]            = None,
			system_text:   Optional[Dict[str, str]] = None,
			user_text:     Optional[Dict[str, str]] = None,
			max_tokens:    int                      = 256,
			temperature:   float                    = 0.3,
			top_p:         float                    = 0.95,
	) -> Dict[str, Any]:
		"""

		:param system_prompt:
		:param user_prompt:
		:param system_text:
		:param user_text:
		:param max_tokens:
		:param temperature:
		:param top_p:
		:return:
		"""

		start_time = time.time()

		try:
			messages = []

			if system_prompt:
				system_text = system_text or {}
				messages.append({
					"role":    "system",
					"content": system_prompt.format(**system_text)
				})

			if user_prompt:
				user_text = user_text or {}
				messages.append({
					"role":    "user",
					"content": user_prompt.format(**user_text)
				})

			response = self.client.chat.completions.create(
				model       = settings.LLM_MODEL,
				max_tokens  = max_tokens,
				temperature = temperature,
				top_p       = top_p,
				messages    = messages,
				extra_body  = {
					"enable_thinking": False,
				},
			)

			latency = round(time.time() - start_time, 3)

			return {
				"success":  True,
				"response": response.choices[0].message.content,
				"finish":   response.choices[0].finish_reason,
				"time":     latency,
				"error":    None,
				"usage": {
					"prompt_tokens":     response.usage.prompt_tokens,
					"completion_tokens": response.usage.completion_tokens,
					"total_tokens":      response.usage.total_tokens,
				},
			}

		except Exception as e:
			latency = round(time.time() - start_time, 3)

			return {
				"success":  False,
				"response": None,
				"finish":   None,
				"time":     latency,
				"error":    str(e),
				"usage":    {},
			}
