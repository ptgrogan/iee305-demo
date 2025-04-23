from pydantic import BaseModel

class Satellite(BaseModel):
    acronym: str
    mass: float
    power: float
