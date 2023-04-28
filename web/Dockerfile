# Pull base image
FROM python:3.10.2-alpine

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code/

# Set time zone
RUN cp /usr/share/zoneinfo/Asia/Vladivostok /etc/localtime

# Install dependencies
COPY . /code/

RUN pip install -r requirements.txt --progress-bar ascii

EXPOSE 8000
