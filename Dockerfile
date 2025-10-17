# Debian 11 (Bullseye) ভিত্তিক পাইথন ইমেজ ব্যবহার করুন যা Chromium এর নির্ভরতা সমর্থন করে
FROM python:3.9-bullseye

# আপনার অ্যাপের জন্য একটি ফোল্ডার তৈরি করুন
WORKDIR /app

# 1. লিনাক্স নির্ভরতা (Chromium) ইনস্টল করা
RUN apt-get update && apt-get install -y \
    # Chromium Browser এবং Driver (সঠিক পাথে ইনস্টল হবে)
    chromium \
    chromium-driver \
    # অন্যান্য প্রয়োজনীয় লাইব্রেরি
    libnss3 \
    libxss1 \
    libappindicator3-1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcairo2 \
    libcups2 \
    libgbm1 \
    libgdk-pixbuf-2.0-0 \
    libgtk-3-0 \
    libxkbcommon0 \
    libasound2 \
    libfontconfig1 \
    libexpat1 \
    libfreetype6 \
    libpng16-16 \
    libjpeg62-turbo \
    # ইন্সটলেশন শেষে অপ্রয়োজনীয় ফাইল মুছে ফেলা
    && rm -rf /var/lib/apt/lists/*

# 2. CHROMEDRIVER_PATH এনভায়রনমেন্ট ভেরিয়েবল সেট করুন (server.py এর জন্য)
ENV CHROMEDRIVER_PATH /usr/bin/chromedriver

# 3. Python নির্ভরতা ইনস্টল করা
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. আপনার কোড কপি করা
COPY . .

# 5. সার্ভার শুরু করার কমান্ড (Gunicorn ব্যবহার করে)
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 server:app
