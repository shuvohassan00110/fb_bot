FROM python:3.11-slim

# Create non-root user with allowed UID (10000–20000)
RUN useradd -u 10001 -m appuser

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER 10001

# Environment
ENV PYTHONUNBUFFERED=1

# Run bot
CMD ["python", "main.py"]
