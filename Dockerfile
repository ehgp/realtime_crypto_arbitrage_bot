FROM python:3.8

WORKDIR /app

COPY . .

RUN pip install pipenv==2021.11.23
RUN pipenv install --verbose
# EXPOSE 3080
# ENV PORT 3080
CMD [ "pipenv run python", "main.py" ]
# CMD ["echo", "no testing"]