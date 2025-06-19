FROM python:3.12-slim

# הגדר את תיקיית העבודה
WORKDIR /app

# שלב 1 – התקנת תלויות מערכת לבנייה ול-WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libffi-dev \
    libxml2 \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    libgdk-pixbuf2.0-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgirepository1.0-dev \
    gir1.2-pango-1.0 \
    libglib2.0-0 \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu \
    tcl8.6-dev tk8.6-dev \
    python3-tk \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# שלב 2 – התקנת תלויות פייתון
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip list > /packages_installed.txt

# שלב 3 – העתקת כל הקוד
COPY . .

# חשיפת פורט
EXPOSE 5000

# הפעלת האפליקציה
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
