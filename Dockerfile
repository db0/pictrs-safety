FROM docker.io/python:3.10-slim-bookworm

WORKDIR /app
COPY requirements.txt requirements.txt

ENV PYTHONPATH='/app'
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT [ "python3.10" ]
EXPOSE 14051
CMD ["python", "api_server.py", "-vvi"]