import os
from typing import List, Optional, Set
from dataclasses import dataclass, field
# from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	# LLM
	LLM_BASE_URL: str = "https://api.xiaomimimo.com/v1"
	LLM_MODEL: str    = "mimo-v2-flash"
	LLM_API_KEY: str  = "sk-s0pe8dj4igizucrzng2u9ijwvw1uw71c1rl70zmiash6p1fm"

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

	# NLP
	# NLP_ENCODER_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
	# NLP_SPACY_MODEL: str   = "ru_core_news_lg"

	# FLAGS


@dataclass
class SpacyConfig:
	model_name: str = "ru_core_news_lg"

	# Обработка текста
	disable: Optional[List[str]] = field(
		default_factory=lambda: ["ner"] # , "lemmatizer"
	)

	# Batch
	batch_size: int = 1000
	n_process: int  = 1


@dataclass
class EncoderConfig:
	model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
	normalize_embeddings: bool = True

	# Global index
	use_ivf: bool = True
	ivf_min_vectors: int = 2000
	ivf_min_nlist: int = 32
	ivf_max_nlist: int = 4096
	ivf_train_size: int = 8192
	nprobe: int = 16

	# Candidate cache
	candidate_cache_size: int = 16
	candidate_exact_threshold: int = 128  # до этого размера — всегда exact Flat
	encode_batch_size: int = 64


settings = Settings()
