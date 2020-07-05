FROM python:3.7.0
ENV PYTHONBUFFERED 1
RUN mkdir /app
WORKDIR /app
COPY . /app/
RUN pip install -r requirements-dev.txt
