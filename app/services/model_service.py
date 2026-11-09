from functools import lru_cache

import joblib
from huggingface_hub import hf_hub_download

from app.core.config import settings


@lru_cache(maxsize=1)
def get_model():
    path = hf_hub_download(repo_id=settings.hf_repo_id,
                           filename=settings.hf_filename,
                           token=settings.hf_token,
                           )
    return joblib.load(path)