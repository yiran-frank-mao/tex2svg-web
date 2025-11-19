FROM python:3.9-slim

RUN apt-get update && apt-get install -y texlive-full pdf2svg

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
