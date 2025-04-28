from sqlmodel import Field, Session, SQLModel, create_engine, select
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException

class Satellite(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    acronym: str
    mass: float
    power: float

engine = create_engine("sqlite:///database.db", connect_args={"check_same_thread": False})

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)

def get_session():
    with Session(engine) as session:
        yield session

class SatelliteCreate(SQLModel):
    acronym: str
    mass: float
    power: float

@app.post("/satellites/")
def create_satellite(
    sat: SatelliteCreate,
    session: Session = Depends(get_session)
) -> int:
  db_sat = Satellite.model_validate(sat)
  session.add(db_sat)
  session.commit()
  session.refresh(db_sat)
  return db_sat.id

class SatelliteRead(SQLModel):
    id: int
    acronym: str
    mass: float
    power: float

@app.get("/satellites/{id}")
def read_satellite(
    id: int,
    session: Session = Depends(get_session)
) -> SatelliteRead:
  db_sat = session.get(Satellite, id)
  if db_sat is None: 
     raise HTTPException(404, f"Satellite {id} not found")
  return db_sat

@app.get("/satellites/")
def read_satellites(
    session: Session = Depends(get_session)
) -> list[SatelliteRead]:
  return session.exec(select(Satellite)).all()

@app.put("/satellites/{id}")
def update_satellite(
    id: int,
    sat: SatelliteCreate,
    session: Session = Depends(get_session)
) -> SatelliteRead:
  db_sat = session.get(Satellite, id)
  if db_sat is None: 
    raise HTTPException(404, f"Satellite {id} not found")
  db_sat.sqlmodel_update(sat.model_dump())
  session.add(db_sat)
  session.commit()
  session.refresh(db_sat)
  return db_sat

class SatelliteUpdate(SQLModel):
    acronym: str | None = None
    mass: float | None = None
    power: float | None = None

@app.patch("/satellites/{id}")
def patch_satellite(
    id: int,
    sat: SatelliteUpdate,
    session: Session = Depends(get_session)
) -> SatelliteRead:
  db_sat = session.get(Satellite, id)
  if db_sat is None: 
    raise HTTPException(404, f"Satellite {id} not found")
  db_sat.sqlmodel_update(sat.model_dump(exclude_unset=True))
  session.add(db_sat)
  session.commit()
  session.refresh(db_sat)
  return db_sat

@app.delete("/satellites/{id}")
def delete_satellite(
   id: int,
   session: Session = Depends(get_session)
):
  db_sat = session.get(Satellite, id)
  if db_sat is None: 
    raise HTTPException(404, f"Satellite {id} not found")
  session.delete(db_sat)
  session.commit()
