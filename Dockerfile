FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# App Runner sends traffic to port 8080 by default
ENV PORT=8080
EXPOSE 8080

# Start the API, binding to the port App Runner expects
CMD ["sh", "-c", "uvicorn telemetry_api.app:app --host 0.0.0.0 --port ${PORT} --app-dir src"]