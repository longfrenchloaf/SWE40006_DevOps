FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Copy backend source code
COPY backend/ .

# Copy templates folder
COPY templates/ ./templates/

EXPOSE 5000

CMD ["python", "billing.py"]
