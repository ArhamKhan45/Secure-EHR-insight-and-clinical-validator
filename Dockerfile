FROM python:3.12-slim

WORKDIR /

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    BACKEND_API_URL=http://127.0.0.1:8000/api/v1

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir --no-compile -r /requirements.txt

COPY src /src

EXPOSE 80

CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port 8000 & exec streamlit run src/ui/app.py --server.address=0.0.0.0 --server.port=80"]