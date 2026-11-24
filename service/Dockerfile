FROM python:3.12-slim
WORKDIR /app
# Pillow's large text needs a real TrueType font; without it, the image
# silently falls back to a tiny bitmap font on the e-ink display.
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pillow==11.3.0 \
    && mkdir -p /app/data
COPY server.py daily_dashboard.py yuvomi_client.py dashboard_settings.py /app/
RUN python -m compileall -q /app && python -c "import server; import dashboard_settings"
EXPOSE 8088
CMD ["python", "/app/server.py"]
