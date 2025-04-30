from sqlmodel import Field, Session, SQLModel, create_engine, select
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException

class Satellite(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    acronym: str
    mass: float
    power: float

class User(SQLModel, table=True):
   username: str = Field(primary_key=True)
   hashed_password: str

class UserRead(SQLModel):
   username: str

from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def authenticate_user(
      session: Session, 
      username: str, 
      password: str
) -> UserRead:
   user = session.get(User, username)
   if user is None or not password_hash.verify(password, user.hashed_password):
      return None
   return UserRead.model_validate(user)

engine = create_engine("sqlite:///database.db", connect_args={"check_same_thread": False})

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
       me = session.get(User, "pgrogan1")
       if me is None:
        me = User(username="pgrogan1", hashed_password=password_hash.hash("hello"))
        session.add(me)
        session.commit()
    yield

app = FastAPI(lifespan=lifespan)

def get_session():
    with Session(engine) as session:
        yield session

from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

from typing import Annotated
from fastapi import status
from jwt.exceptions import InvalidTokenError

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> UserRead:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    return UserRead(username=username)

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

from fastapi.security import OAuth2PasswordRequestForm

class Token(SQLModel):
   access_token: str
   token_type: str

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session)
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/")
async def read_users_me(
    current_user: Annotated[UserRead, Depends(get_current_user)],
):
    return current_user