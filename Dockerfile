# Use an official Python runtime as a parent image
FROM python:3.11.2-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Make the main script executable
RUN chmod +x /app/main.py

# Set the default entrypoint to the Python script
ENTRYPOINT ["python3", "/app/main.py"]