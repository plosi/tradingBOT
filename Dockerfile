FROM  python:3.8-slim-buster

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 8050

ENTRYPOINT [ "python3", "dashboard.py" ]
