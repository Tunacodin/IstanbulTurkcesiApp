# İstanbul Türkçesi Diksiyon — HF Spaces backend
# FastAPI + wav2vec2 + audio assessment

FROM python:3.11-slim

# Sistem bağımlılıkları (audio + ML için)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# HF Spaces user (zorunlu: writable cache için non-root user)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/user/.cache/huggingface \
    PORT=7860

WORKDIR /home/user/app

# Önce requirements'ı kopyala (Docker layer cache için)
COPY --chown=user:user poc/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --user --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Uygulama kodunu kopyala
COPY --chown=user:user poc ./poc
COPY --chown=user:user data ./data

# Audio bundle'lari ac (LFS-tracked tar.gz'ler — bulk wav upload calismadigi icin tar yontemi)
RUN if [ -f data/knowledge/word_clips.tar.gz ]; then \
      echo "Extracting word_clips.tar.gz..." && \
      tar -xzf data/knowledge/word_clips.tar.gz -C data/knowledge/ && \
      rm data/knowledge/word_clips.tar.gz && \
      echo "word_clips: $(ls data/knowledge/word_clips/ | wc -l) files"; \
    fi && \
    if [ -f data/exercises/refs.tar.gz ]; then \
      echo "Extracting refs.tar.gz..." && \
      tar -xzf data/exercises/refs.tar.gz -C data/exercises/ && \
      rm data/exercises/refs.tar.gz && \
      echo "refs: $(ls data/exercises/refs/ | wc -l) files"; \
    fi

WORKDIR /home/user/app/poc

# HF Spaces 7860'ı bekliyor
EXPOSE 7860

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
