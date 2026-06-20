FROM python:3.11-slim

WORKDIR /app

# System deps needed by chromadb and sentence-transformers
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first to avoid the 2GB CUDA build
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download the embedding model so cold starts don't hit HF rate limits
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

EXPOSE 8000

CMD ["sh", "-c", "uvicorn chatbot:app --host 0.0.0.0 --port ${PORT:-8000}"]
