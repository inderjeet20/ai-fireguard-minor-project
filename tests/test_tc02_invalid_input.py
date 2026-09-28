"""
TC-02: Invalid, Missing or Out-of-Range Input
Synopsis Expectation:
Each submission rejected with an informative message identifying the offending field;
no prediction attempted; application does not terminate abnormally.
"""

import pytest
from pydantic import ValidationError
from api.services.ml_model import EnvironmentalInput

def test_tc02_negative_humidity_rejected():
    with pytest.raises(ValidationError) as excinfo:
        EnvironmentalInput(
            temperature=30.0,
            relative_humidity=-10.0, # Implausible negative humidity
            wind_speed=15.0,
            rainfall=0.0
        )
    assert "Relative humidity must be between 0% and 100%" in str(excinfo.value)

def test_tc02_excessive_temperature_rejected():
    with pytest.raises(ValidationError) as excinfo:
        EnvironmentalInput(
            temperature=95.0, # Beyond max realistic temperature 65°C
            relative_humidity=40.0,
            wind_speed=10.0,
            rainfall=0.0
        )
    assert "Temperature must be between -30°C and 65°C" in str(excinfo.value)

def test_tc02_missing_mandatory_field():
    with pytest.raises(ValidationError) as excinfo:
        # Missing relative_humidity and temperature
        EnvironmentalInput(
            wind_speed=10.0,
            rainfall=0.0
        )
    assert "temperature" in str(excinfo.value)
