FROM python:3.12-slim

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./backend/requirements.txt
COPY backend/requirements-vector.txt ./backend/requirements-vector.txt
ARG WITH_VECTOR=false
RUN if [ "$WITH_VECTOR" = "true" ]; then \
      pip install --no-cache-dir -r backend/requirements-vector.txt; \
    else pip install --no-cache-dir -r backend/requirements.txt; fi

# Copy backend code, knowledge base and vector database
COPY backend ./backend
COPY tests/knowledge_base ./tests/knowledge_base
COPY chroma_db ./chroma_db

WORKDIR /app/backend

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
