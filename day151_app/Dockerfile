FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Required flags for Docker:
#   --server.address 0.0.0.0   → listen on all interfaces
#   --server.headless true     → disable browser opening (container has no GUI)
#   --server.port 8501         → explicit port
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]