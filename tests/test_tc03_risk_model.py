"""
TC-03: Fire-Risk Prediction and Risk Score
Synopsis Expectation:
Prediction executes without error; a fire-risk score is produced on the expected bounded scale
and displayed in interpretable form.
"""

from api.services.ml_model import EnvironmentalInput, ml_engine

def test_tc03_risk_prediction_scale_and_behavior():
    # 1. Extreme wildfire condition: Dry + Hot + Windy
    extreme_input = EnvironmentalInput(
        temperature=43.0,
        relative_humidity=10.0,
        wind_speed=38.0,
        rainfall=0.0,
        ndvi=0.18,
        active_hotspots_nearby=5
    )
    result_extreme = ml_engine.predict(extreme_input)
    assert 0.0 <= result_extreme["risk_score"] <= 1.0
    assert result_extreme["risk_level"] in ["Medium", "High"]
    assert "contributing_factors" in result_extreme

    # 2. Cool + Wet condition
    cool_wet_input = EnvironmentalInput(
        temperature=15.0,
        relative_humidity=85.0,
        wind_speed=5.0,
        rainfall=40.0,
        ndvi=0.70,
        active_hotspots_nearby=0
    )
    result_cool = ml_engine.predict(cool_wet_input)
    assert 0.0 <= result_cool["risk_score"] <= 1.0
    assert result_cool["risk_level"] == "Low"

    # Monotonic property: Extreme condition hazard must exceed Cool/Wet condition hazard
    assert result_extreme["risk_score"] > result_cool["risk_score"]
