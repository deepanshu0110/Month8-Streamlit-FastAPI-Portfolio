# Use slim base image for smaller size
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy only requirements first (leverage Docker cache)
COPY requirements.txt .

# Install dependencies without caching to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Run uvicorn with host 0.0.0.0 to accept external connections
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]