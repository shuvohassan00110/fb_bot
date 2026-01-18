FROM python:3.11-slim

RUN useradd -u 10001 -m appuser
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app
USER 10001

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["python", "main.py"]
