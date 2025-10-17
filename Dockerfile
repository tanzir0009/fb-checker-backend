# Debian 11 (Bullseye) ভিত্তিক পাইথন ইমেজ ব্যবহার করুন যা Chromium এর নির্ভরতা সমর্থন করে
FROM python:3.9-bullseye

# আপনার অ্যাপের জন্য একটি ফোল্ডার তৈরি করুন
WORKDIR /app

# 1. লিনাক্স নির্ভরতা (Chromium) ইনস্টল করা
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
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
    && rm -rf /var/lib/apt/lists/*

# 2. CHROMEDRIVER_PATH এনভায়রনমেন্ট ভেরিয়েবল সেট করুন
ENV CHROMEDRIVER_PATH /usr/bin/chromedriver

# 3. Python নির্ভরতা ইনস্টল করা
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. আপনার কোড কপি করা
COPY . .

# 5. সার্ভার শুরু করার চূড়ান্ত কমান্ড (Gunicorn ব্যবহার করে)
# PORT পরিবেশ ভেরিয়েবল ব্যবহার করে Gunicorn কে Railway এর সাথে সিঙ্ক্রোনাইজ করা হয়েছে।
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "1", "server:app"]
