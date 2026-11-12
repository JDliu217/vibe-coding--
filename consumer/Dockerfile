FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY libs ./libs
COPY services ./services
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts ./scripts
ENV PYTHONPATH=/app/libs/common
ENV PORT=8090
ENV SERVICE=api-gateway
CMD ["sh", "-c", "python -m uvicorn app.main:app --app-dir services/$SERVICE --host 0.0.0.0 --port $PORT"]
