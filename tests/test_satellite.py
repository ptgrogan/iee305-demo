import pytest

from pydantic import ValidationError

from satellites import Satellite

def test_set_mass():
    satellite = Satellite(acronym="Landsat-7", mass=2100, power=1980)
    assert satellite.mass == 2100

def test_missing_mass():
    with pytest.raises(ValidationError):
        satellite = Satellite(acronym="Landsat-7", power=1980)