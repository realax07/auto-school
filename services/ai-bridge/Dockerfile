FROM python:3.12-slim

WORKDIR /app
COPY app.py /app/app.py

# stdlib-only: pip не нужен
EXPOSE 8790
CMD ["python3", "/app/app.py"]
