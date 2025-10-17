# বেস ইমেজ: Debian Bullseye (Debian 11) ভিত্তিক Python ইমেজ
# এটি Chromium এবং সমস্ত প্রয়োজনীয় নির্ভরতা সমর্থন করে।
FROM python:3.9-bullseye

# প্রয়োজনীয় Linux লাইব্রেরি এবং Headless Chromium ইনস্টল করা
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
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libxkbcommon0 \
    libasound2 \
    libfontconfig1 \
    libexpat1 \
    libfreetype6 \
    libpng16-16 \
    libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver এর পথ সেট করুন
ENV CHROMEDRIVER_PATH /usr/lib/chromium/chromedriver

# আপনার অ্যাপের ফাইল রাখার ডিরেক্টরি
WORKDIR /app

# নির্ভরতা ইনস্টল করা
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# আপনার কোড কপি করা
COPY . .

# সার্ভার চালানোর কমান্ড (Gunicorn ব্যবহার করে)
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 server:app
