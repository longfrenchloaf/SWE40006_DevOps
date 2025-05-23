FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy all backend source code inside backend/
COPY . .

# Expose port and default command
EXPOSE 5000
CMD ["python", "billing.py"]
