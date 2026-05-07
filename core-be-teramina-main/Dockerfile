FROM python:3.10-slim

# install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# set the working directory
WORKDIR /app

# copy the project files
COPY . /app

# install the requirements
RUN pip install -r requirements.txt

# expose the port
EXPOSE 8000

# run the app
# CMD ["uvicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "teramina.asgi:application"]
CMD ["uvicorn", "teramina.asgi:application", "--host", "0.0.0.0", "--port", "8000"]