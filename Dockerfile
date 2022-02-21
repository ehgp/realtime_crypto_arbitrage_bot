FROM python:3.7-alpine as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

# Install pipenv and compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev libssl-dev

# Install python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /app

# Install application into container
COPY . .

# Run the application


# ENTRYPOINT ["python", "-m", "http.server"]
# CMD ["--directory", "directory", "3080"]
# CMD python main.py runserver 0.0.0.0:3080
# EXPOSE 3080
# ENV PORT 3080
# CMD [ "pipenv", "run", "python", "/app/bin/main.py" ]
# CMD ["echo", "no testing"]
# Run the application
# ENTRYPOINT ["python", "-m", "http.server"]
# CMD ["--directory", "directory", "8000"]
