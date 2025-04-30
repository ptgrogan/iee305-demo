FROM python:3.10

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./src /app/src
COPY ./pyproject.toml /app/pyproject.toml

RUN pip install .

CMD ["fastapi", "run", "src/iee305/main.py", "--port", "8000"]