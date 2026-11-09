import numpy as np
from fastapi import APIRouter, Depends

from app.api.rate_limit import rate_limited_user
from app.db.models import User
from app.schemas.predict import HouseFeatures, PredictionOut
from app.services.model_service import get_model

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictionOut)
def predict(features: HouseFeatures, _: User = Depends(rate_limited_user)):
    x = np.array([[*features.model_dump().values()]])
    return PredictionOut(prediction=float(get_model().predict(x)[0]))