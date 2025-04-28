from pydantic import BaseModel

class Satellite(BaseModel):
    """
    Satellite object class.

    A satellite object class holds the acronym, mass, and power.
    """
    acronym: str
    mass: float
    power: float
