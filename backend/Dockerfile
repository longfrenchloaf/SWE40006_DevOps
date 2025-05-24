FROM python:3.11-slim

WORKDIR /app

# Copy entrypoint script and make it executable (Keep this for now if you added it)
# COPY backend/entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt # Added --no-cache-dir

# Copy backend source code
COPY backend/ .

# Copy templates folder
COPY templates/ ./templates/

EXPOSE 5000

# Use Gunicorn instead of the Flask development server
# Syntax: gunicorn [OPTIONS] module:app
# Replace 'billing:app' if your Flask app instance is named differently in billing.py
# Or if your main Flask app file is named differently.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "billing:app"]

# If you were using an entrypoint script, modify it to exec the gunicorn command:
# ENTRYPOINT ["/entrypoint.sh"]
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "billing:app"]
# entrypoint.sh should end with 'exec "$@"'