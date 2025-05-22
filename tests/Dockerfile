# Dockerfile located at SWE40006_DevOps/tests/Dockerfile
FROM selenium/standalone-chrome:103.0-20250515 as selenium_base 

# Our test runner image
FROM selenium_base

# Set environment variables
ENV APP_URL=http://4.206.70.73:5000/
# The Selenium image handles headless mode via its own configuration/entrypoint.
# Keep this ENV var for your Python script's logic if it uses it elsewhere.
ENV HEADLESS=true
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy your Python requirements and install them
# The Selenium base image has Python, but you need your specific libraries.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your test files and data into the working directory
COPY . .

# The default ENTRYPOINT/CMD of selenium/standalone-chrome starts the Selenium Hub/Node.
# We need to override this to run *our* pytest command instead.
# The Python executable should be in the PATH, but you can use /usr/local/bin/python if needed.

# Override the container's entrypoint and command to run pytest
ENTRYPOINT ["python"]
CMD ["-m", "pytest", "test_food_billing_ui.py", "--junitxml=test-results.xml"]