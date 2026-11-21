FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install chromium --with-deps \
    && rm -rf /var/lib/apt/lists/*

COPY . .

ENTRYPOINT ["python"]
CMD ["scripts/generate_repo_reel.py", "--help"]
