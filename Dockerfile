FROM python:3.12-alpine

WORKDIR /app

COPY . /app

RUN chmod -R 755 /app

ENV PORT=8090
EXPOSE 8090

CMD ["python", "server.py"]
