# Use a base image from CircleCI that includes Python, Chrome, and Chromedriver
# This image is specifically designed for browser testing in CI environments.
FROM cimg/browser:stable

# Set the working directory inside the container
# All subsequent commands will run relative to this directory
WORKDIR /app/test-runner

# --- Install Python Dependencies ---
# Copy the test-specific Python dependency file (requirements.txt)
# Source: 'tests/requirements.txt' is relative to the build context (project root)
# Destination: '.' copies it into the WORKDIR ('/app/test-runner')
COPY tests/requirements.txt .

# Install the Python dependencies listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy Test Code ---
# Copy your test code and test data (the entire content of the 'tests' directory)
# The source path '.' is relative to the Dockerfile's location ('tests/') within the build context
# The destination path '.' copies these files directly into the WORKDIR
COPY . . # Corrected based on previous debugging

# Ensure Chromedriver is in the PATH. cimg/browser image typically ensures this.
# No extra steps needed here to install Chrome or Chromedriver.

# --- Set Default Command ---
# Define the default command to run when the container starts
# This command runs pytest and generates a JUnit XML report
# The command runs from the WORKDIR (/app/test-runner)
# The test file path is relative to the WORKDIR
CMD ["python3", "-m", "pytest", "--junitxml=test-results.xml", "test_food_billing_ui.py"] # Corrected based on previous debugging