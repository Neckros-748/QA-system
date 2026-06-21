import os
from pathlib import Path
from typing import List, Optional, Set, Dict
from dataclasses import dataclass, field
# from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	# LLM
	LLM_BASE_URL: str = "https://api.xiaomimimo.com/v1" # "https://openrouter.ai/api/v1"
	LLM_MODEL: str    = "mimo-v2-flash"
	LLM_API_KEY: str  = ""

	# GRAPH


	# SQL :: Postgres
	POSTGRES_USER: str
	POSTGRES_PASSWORD: str
	POSTGRES_DATABASE: str

	model_config = {
		"env_file":          ".env",
		"env_file_encoding": "utf-8",
	}

	# LLM_BASE_URL: str = os.environ["LLM_BASE_URL"]
	# LLM_MODEL: str    = os.environ["LLM_MODEL"]
	# LLM_API_KEY: str  = os.environ["LLM_API_KEY"]


@dataclass
class AnnotatorConfig:
	# Models
	model_name: Dict[str, str] = field(
		default_factory=lambda: {
			"extractor":            "ru_core_news_sm",                       # python -m extractor download ru_core_news_sm
			"sentence_transformer": "paraphrase-multilingual-MiniLM-L12-v2", #
		})

	# Обработка текста
	disable: List[str] = field(
		default_factory=lambda: [
			"ner" # , "lemmatizer"
		])

	# Path
	path_to_data: Path = ""

	# Flags
	include_annotation: bool = True
	include_subchunks:  bool = True
	include_markup:     bool = True

	# Batch
	batch_size: int = 1000
	n_process: int  = 1


	#
	#
	normalize_embeddings: bool = True
	#
	# # Global index
	# use_ivf: bool = True
	# ivf_min_vectors: int = 2000
	# ivf_min_nlist: int = 32
	# ivf_max_nlist: int = 4096
	# ivf_train_size: int = 8192
	# nprobe: int = 16
	#
	# # Candidate cache
	# candidate_cache_size: int = 16
	# candidate_exact_threshold: int = 128
	encode_batch_size: int = 64



settings = Settings()
