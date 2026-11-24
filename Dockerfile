FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY assignment3 /app/assignment3
COPY sql /app/sql
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn assignment3.web:app --host 0.0.0.0 --port ${PORT:-8000}"]
