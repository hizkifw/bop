FROM python:3.9

WORKDIR /app
RUN set -ex; \
    apt-get update; \
    apt-get install -y --no-install-recommends ffmpeg; \
    rm -rf /var/lib/apt/lists/*;

COPY requirements.txt .
RUN set -ex; python3 -m pip install -r requirements.txt;

COPY . .
CMD ["python3", "-u", "bop.py"]
