FROM python:3.11-slim

WORKDIR /app

RUN useradd -m -u 10001 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

RUN chown -R appuser:appuser /app

USER appuser

CMD ["./entrypoint.sh"]
