# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy all project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8080

# Start FastAPI app
CMD ["python", "Backend/main.py"]
