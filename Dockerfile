# Use the official Python image as base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=websiteServerForTesting.py
ENV FLASK_ENV=production

# Set the working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy the application code
COPY . /app

# Expose the HTTP port
EXPOSE 5000

# Initialize the database
RUN python3 initdb.py

# Run the Flask app
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]

