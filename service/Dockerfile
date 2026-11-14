FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir pillow==11.3.0 && mkdir -p /app/data
COPY server.py /app/server.py
EXPOSE 8088
CMD ["python", "/app/server.py"]
