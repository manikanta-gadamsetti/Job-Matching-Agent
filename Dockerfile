FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md main.py ./
COPY src ./src
COPY config.yaml ./config.yaml
COPY data ./data

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
