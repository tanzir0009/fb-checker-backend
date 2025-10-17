import os
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

app = Flask(__name__)
# CORS নীতি সেট করা
CORS(app) 

# রেলওয়েতে ChromeDriver এবং Chrome Binary এর পথ
# এই পথগুলো Railway/Docker পরিবেশের জন্য সবচেয়ে সাধারণ।
CHROME_DRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
# Chromium বাইনারির জন্য অতিরিক্ত ডিফল্ট পাথ যুক্ত করা হলো 
CHROME_BINARY_PATH = os.environ.get("CHROME_BIN", "/usr/bin/chromium")

# রুট ইউআরএল-এ হেলথচেক রুট
@app.route('/')
def health_check():
    # এটি নিশ্চিত করবে যে সার্ভারটি ক্র্যাশ না করে চলছে
    return jsonify({"status": "Server Running", "message": "Access /check-facebook-id for API endpoint."}), 200


def check_facebook_id(number_to_check):
    """
    Headless Chrome ব্যবহার করে Facebook-এ ফোন নম্বর অনুসন্ধান করে।
    """
    
    # 1. Chrome Options সেটআপ
    options = Options()
    # ব্রাউজারের বাইনারি পাথ স্পষ্টভাবে সেট করা
    options.binary_location = CHROME_BINARY_PATH 
    
    # Docker/Linux এ স্থিতিশীলতার জন্য Headless মোড এবং arguments
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox") # Docker এ REQUIRED
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3") 
    options.add_argument("--silent")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--disable-extensions")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # 2. Driver Initialization
    driver = None
    try:
        # ChromeService ব্যবহার করে স্পষ্টভাবে ড্রাইভারের পাথ সেট করা
        # service_timeout 60 সেকেন্ড সেট করা হলো
        service = ChromeService(executable_path=CHROME_DRIVER_PATH, service_timeout=60)
        driver = webdriver.Chrome(service=service, options=options) 
        
        # 3. Navigation
        url = "https://mbasic.facebook.com/login/identify/"
        driver.get(url)
        
        # 4. Cookie Handling 
        try:
            # 5 সেকেন্ড অপেক্ষা করা
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="cookie-policy-dialog-accept-button"]'))
            ).click()
        except TimeoutException:
            pass
            
        # 5. Phone Number Search
        try:
            # ইনপুট ফিল্ড খুঁজে বের করা (10 সেকেন্ড অপেক্ষা)
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "identify_search_text_input"))
            )
            search_input.send_keys(number_to_check)
            
            search_button = driver.find_element(By.NAME, "did_submit")
            search_button.click()
            
            # 6. অপেক্ষা ও ফলাফল যাচাই
            WebDriverWait(driver, 10).until(
                EC.url_changes(url)
            )
            time.sleep(2) 

            page_source = driver.page_source
            
            if "doesn't match an account" in page_source or "আপনার দেওয়া তথ্যের সাথে কোনো অ্যাকাউন্ট খুঁজে পাইনি" in page_source:
                return 'id_not_found'
            else:
                return 'id_found'
                
        except (NoSuchElementException, TimeoutException):
            print("Selenium: Search element interaction failed or timed out.")
            return 'error_page_structure'
            
    except Exception as e:
        # Selenium initialization error (likely binary not found)
        print(f"--- FATAL SELENIUM INITIALIZATION ERROR ---: {e}") 
        return 'error_general'
        
    finally:
        if driver:
            driver.quit()

@app.route('/check-facebook-id', methods=['POST'])
def check_id_endpoint():
    """API endpoint to receive POST requests."""
    try:
        data = request.get_json()
        number = data.get('number')
        
        if not number:
            return jsonify({'status': 'error', 'message': 'Phone number missing'}), 400
            
        result = check_facebook_id(number)
        
        if result == 'id_not_found':
            return jsonify({'status': 'id_not_found', 'message': 'Account not found'})
        elif result == 'id_found':
            return jsonify({'status': 'id_found', 'message': 'Account found'})
        else:
            # 500 ত্রুটি ফিরিয়ে দেবে 
            return jsonify({'status': 'error', 'message': 'Internal Facebook check failed (Selenium error). Check server logs.'}), 500
            
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
