from sqlalchemy import select
from sqlalchemy.orm import Session

from ..algorithms.prediction import predict_do_risk
from ..core.config import settings
from ..models import Prediction, SensorData


def create_prediction(db: Session, row: SensorData, horizon_minutes: int = 60) -> Prediction:
    readings = list(db.scalars(select(SensorData).where(
        SensorData.pond_id == row.pond_id,
    ).order_by(SensorData.timestamp.desc()).limit(60)))
    readings.reverse()
    result = predict_do_risk(readings, horizon_minutes, settings.do_critical, settings.do_warning)
    prediction = Prediction(pond_id=row.pond_id, risk_level=result.risk_level,
                            probability=result.probability, horizon_minutes=result.horizon_minutes,
                            data_source=row.data_source)
    db.add(prediction)
    return prediction
