FROM python:3.11-slim

WORKDIR /app

# Copy entrypoint script and make it executable
COPY backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Copy backend source code
COPY backend/ .

# Copy templates folder
COPY templates/ ./templates/

EXPOSE 5000

# Use the entrypoint script, passing the original command as arguments
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "billing.py"]