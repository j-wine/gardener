# Use the official Python slim image as a base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies specified in the requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app directory content to the container
COPY . .

# Expose the port that Streamlit will run on
EXPOSE 8501


# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
