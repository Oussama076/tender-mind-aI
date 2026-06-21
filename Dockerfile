# Use official Python lightweight image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Command to run both services (in a real production environment, use docker-compose or separate containers)
# We will use a small script to start both
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
