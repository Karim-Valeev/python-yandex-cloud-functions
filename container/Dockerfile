FROM python:3.9.6

WORKDIR /opt/app

COPY requirements.txt .

RUN  pip install --no-cache-dir --upgrade pip  \
     && pip install --no-cache-dir -r requirements.txt

COPY settings.py .
COPY main.py .

CMD [ "python", "main.py" ]
