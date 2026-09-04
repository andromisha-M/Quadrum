FROM python:3.11-slim

# LibreOffice (writer + calc only, to keep the image lean) converts Office
# invoices to PDF; the fonts stop converted documents rendering as blank boxes.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        libreoffice-calc \
        fonts-dejavu \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 18880

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "18880"]
