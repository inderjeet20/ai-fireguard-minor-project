"""
TC-01: Valid Environmental Data Input
Synopsis Expectation:
All values accepted without validation error, correctly associated with their fields,
and structured record passed to preprocessing.
"""

from api.services.ml_model import EnvironmentalInput, ml_engine

def test_tc01_valid_environmental_input():
    # Valid input payload
    data = {
        "temperature": 38.5,
        "relative_humidity": 22.0,
        "wind_speed": 25.0,
        "rainfall": 0.0,
        "ndvi": 0.35,
        "distance_to_settlement_km": 3.2,
        "active_hotspots_nearby": 2
    }
    
    # Validation should succeed cleanly
    validated_record = EnvironmentalInput(**data)
    assert validated_record.temperature == 38.5
    assert validated_record.relative_humidity == 22.0
    assert validated_record.wind_speed == 25.0
    assert validated_record.rainfall == 0.0
    assert validated_record.ndvi == 0.35
    assert validated_record.distance_to_settlement_km == 3.2
    assert validated_record.active_hotspots_nearby == 2

    # Prediction should execute without error
    prediction = ml_engine.predict(validated_record)
    assert "risk_score" in prediction
    assert "risk_level" in prediction
    assert prediction["risk_level"] in ["Low", "Medium", "High"]
