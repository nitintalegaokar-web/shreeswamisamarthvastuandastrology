FROM python:3.12-slim-bookworm
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources && apt-get update && apt-get install -y --no-install-recommends chromium fonts-noto-core fonts-liberation && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY protected/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY . /app
RUN useradd --create-home --uid 10001 calculator && mkdir -p /data && chown calculator:calculator /data
USER calculator
ENV CALCULATOR_CHROMIUM=/usr/bin/chromium KP_ACCOUNT_DATABASE=/data/accounts.sqlite KP_COOKIE_SECURE=1
EXPOSE 8080
CMD ["python", "protected/server.py", "--host", "0.0.0.0", "--port", "8080"]
