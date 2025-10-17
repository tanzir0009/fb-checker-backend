# নতুন, স্থিতিশীল বেস ইমেজ: Debian Buster (Debian 10) ভিত্তিক Python ইমেজ
FROM python:3.9-buster

# প্রয়োজনীয় Linux লাইব্রেরি এবং Headless Chromium ইনস্টল করা
# Buster-এ apt-get install কমান্ডটি প্যাকেজগুলো সঠিকভাবে খুঁজে পাবে
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libnss3 \
    libxss1 \
    libappindicator1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcairo2 \
    libcups2 \
    libgbm1 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libxkbcommon0 \
    libasound2 \
    libfontconfig1 \
    libexpat1 \
    libfreetype6 \
    libpng16-16 \
    libjpeg-turbo8 \
    && rm -rf /var/lib/apt/lists/*

# আপনার অ্যাপের ফাইল রাখার ডিরেক্টরি
WORKDIR /app

# নির্ভরতা ইনস্টল করা
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# আপনার কোড কপি করা
COPY . .

# সার্ভার চালানোর কমান্ড (Gunicorn ব্যবহার করে)
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 server:app
