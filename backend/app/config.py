from pathlib import Path
from typing import List, Optional, Set, Dict
from dataclasses import dataclass, field
from pydantic_settings import BaseSettings


@dataclass
class Config:

	# Models
	model_name: Dict[str, str] = field(
		default_factory=lambda: {
			"spacy":                "ru_core_news_sm",
			"sentence_transformer": "paraphrase-multilingual-MiniLM-L12-v2",
		})

	# Path
	path_to_data: Optional[Path] = None
	storage_path: Optional[Path] = None

	# Flags
	use_lex_index:      bool = True
	use_vec_index:      bool = True
	include_annotation: bool = True
	include_subchunks:  bool = True
	include_markup:     bool = True

	# Batch
	batch_size: int = 1000
	n_process:  int = 1

	# ==========================================================================
	# Графовая индексация
	# ==========================================================================

	# Обработка текста
	disable: List[str] = field(
		default_factory=lambda: [
			"ner" # , "lemmatizer"
		])

	# ==========================================================================
	# Лексическая и векторная индексация
	# ==========================================================================

	# Лексическая индексация

	# Векторная индексация
	normalize_embeddings: bool = True
	embedding_dim:        int  = 384

	# ==========================================================================
	# Гибридная индексация
	# ==========================================================================

	normalize_graph: bool = True
	normalize_lex:   bool = True
	normalize_vec:   bool = True


class Settings(BaseSettings):
	# LLM
	LLM_BASE_URL:      str
	LLM_MODEL:         str
	LLM_API_KEY:       str

	# SQL :: Postgres
	POSTGRES_USER:     str
	POSTGRES_PASSWORD: str
	POSTGRES_DATABASE: str

	model_config = {
		"env_file":          ".env",
		"env_file_encoding": "utf-8",
	}


settings = Settings()


	# # Global index
	# use_ivf: bool = True
	# ivf_min_vectors: int = 2000
	# ivf_min_nlist: int = 32
	# ivf_max_nlist: int = 4096
	# ivf_train_size: int = 8192
	# nprobe: int = 16



