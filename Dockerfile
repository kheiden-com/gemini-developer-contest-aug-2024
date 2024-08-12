# Dockerfile for the Python Flask Server
FROM python:3.12

WORKDIR /app

# Copy the dependencies file to the working directory
# Install the dependencies
# For additional dependencies, add them to an incremental requirements file
# Example: requirements1.txt, requirements2.txt, etc.
# Then add another RUN command. This will help with caching.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY requirements1.txt .
RUN pip install -r requirements1.txt

EXPOSE 4867

WORKDIR /app/src

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:4867", "-t", "0", "--error-logfile", "/var/log/gunicorn/main.log", "--access-logfile", "/var/log/gunicorn/access.log", "--capture-output", "--log-level", "debug", "server:app"]