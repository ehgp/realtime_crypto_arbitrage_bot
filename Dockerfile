FROM python:3.7-slim as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
# EXPOSE 3080
# ENV PORT 3080
# ARG KUCOIN_YOUR_API_KEY
# ARG KUCOIN_YOUR_SECRET
# ARG KUCOIN_YOUR_PASS
ENV KUCOIN_YOUR_API_KEY=${KUCOIN_YOUR_API_KEY}
ENV KUCOIN_YOUR_SECRET=${KUCOIN_YOUR_SECRET}
ENV KUCOIN_YOUR_PASS=${KUCOIN_YOUR_PASS}
ENV CBPRO_YOUR_API_KEY=${CBPRO_YOUR_API_KEY}
ENV CBPRO_YOUR_SECRET=${CBPRO_YOUR_SECRET}
ENV CBPRO_YOUR_PASS=${CBPRO_YOUR_PASS}
ENV GEMINI_YOUR_API_KEY=${GEMINI_YOUR_API_KEY}
ENV GEMINI_YOUR_SECRET=${GEMINI_YOUR_SECRET}
# Install pipenv and compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev libssl-dev graphviz parallel
WORKDIR /app

# Install application into container
COPY . .
RUN pip install --upgrade pip

RUN pip install -r requirements.txt
# Run the application
# CMD ["python", "main.py"]


# If you must use pipenv comment out requirements.txt install first
# RUN pip install pipenv==2022.1.8
# RUN pipenv install --verbose 3
# Run the application
# CMD ["pipenv", "run", "python", "main.py"]
