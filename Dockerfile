# Start with a clean, official Python environment
FROM python:3.9-slim

# Set a working directory inside the container
WORKDIR /app

# Copy the requirements file and install the libraries
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of our application code (main.py)
COPY . .

# The command to start our Gunicorn production server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]