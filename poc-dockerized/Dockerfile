FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=8080

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ .

# Create directory for project root (for database access)
RUN mkdir -p /project_root

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["sh", "-c", "python app.py --port $PORT --host 0.0.0.0"]