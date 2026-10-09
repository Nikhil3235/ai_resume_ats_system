import os
import logging
from typing import Any, Union, List
import numpy as np

logger = logging.getLogger('ats_resume_scorer')

class LightweightEmbedder:
    """
    High-efficiency semantic vectorizer designed for environments with <=512MB RAM
    (such as Render Free Tier). Uses HashingVectorizer with L2 normalization to produce
    fast, consistent cosine similarity vectors without loading heavy PyTorch models.
    """
    def __init__(self, n_features: int = 512):
        from sklearn.feature_extraction.text import HashingVectorizer
        self.n_features = n_features
        self._vectorizer = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            norm='l2',
            ngram_range=(1, 2)
        )

    def encode(self, text: Union[str, List[str]], convert_to_tensor: bool = False) -> Any:
        if isinstance(text, str):
            texts = [text]
            single = True
        else:
            texts = list(text)
            single = False

        sparse_vecs = self._vectorizer.transform(texts)
        dense_vecs = sparse_vecs.toarray()

        if single:
            return dense_vecs[0]
        return dense_vecs


def get_embedder() -> Any:
    """
    Returns an embedder instance. Defaults to LightweightEmbedder for fast startup
    and ultra-low RAM usage (<50MB). If USE_HEAVY_EMBEDDER is explicitly set to true,
    attempts to load SentenceTransformer.
    """
    use_heavy = os.getenv("USE_HEAVY_EMBEDDER", "false").lower() in ("true", "1")
    if use_heavy:
        try:
            from sentence_transformers import SentenceTransformer
            from backend.core.config import SENTENCE_TRANSFORMER_MODEL
            logger.info(f"Loading heavy SentenceTransformer: {SENTENCE_TRANSFORMER_MODEL}")
            return SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to LightweightEmbedder.")

    logger.info("Initialized LightweightEmbedder (Optimized for <512MB RAM Render Free Tier).")
    return LightweightEmbedder()
