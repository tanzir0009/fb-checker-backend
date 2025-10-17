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

# রেলওয়েতে /usr/bin/chromedriver সাধারণত একটি symlink থাকে।
# সরাসরি Chromium binary এর পথ ব্যবহার করা আরও নির্ভরযোগ্য।
CHROME_DRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
# Chromium Binary এর পথ
CHROME_BINARY_PATH = os.environ.get("CHROME_BIN", "/usr/bin/chromium")

def check_facebook_id(number_to_check):
    """
    Headless Chrome ব্যবহার করে Facebook-এ ফোন নম্বর অনুসন্ধান করে।
    """
    
    # 1. Chrome Options সেটআপ
    options = Options()
    
    # *** 500 Error Fix: ব্রাউজারের বাইনারি পাথ স্পষ্টভাবে সেট করুন ***
    options.binary_location = CHROME_BINARY_PATH
    
    # Docker/Linux এ স্থিতিশীলতার জন্য REQUIRED Headless মোড এবং arguments
    options.add_argument("--headless=new") # নতুন হেডলেস মোড
    options.add_argument("--no-sandbox") 
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080") # বড় রেজোলিউশন
    options.add_argument("--remote-debugging-host=0.0.0.0")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--log-level=3") # শুধুমাত্র মারাত্মক ত্রুটিগুলো লগ করবে
    options.add_argument("--silent")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--disable-extensions")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


    # 2. Driver Initialization
    driver = None
    try:
        # ChromeDriver Path ব্যবহার করে Service সেটআপ
        service = ChromeService(executable_path=CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        
        # 3. Navigation
        url = "https://mbasic.facebook.com/login/identify/"
        driver.get(url)
        
        # 4. Cookie Handling (যদি আসে) - কুকি হ্যান্ডলিং কে আরও সহনশীল করা হয়েছে
        try:
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
            
            # সার্চ বাটন ক্লিক করা
            search_button = driver.find_element(By.NAME, "did_submit")
            search_button.click()
            
            # 6. অপেক্ষা ও ফলাফল যাচাই
            # পেজ লোড হওয়ার জন্য একটু বেশি অপেক্ষা করা হলো
            WebDriverWait(driver, 10).until(
                EC.url_changes(url) # URL পরিবর্তন হওয়ার জন্য অপেক্ষা করা
            )
            time.sleep(2) # অতিরিক্ত নিশ্চিতকরণের জন্য

            page_source = driver.page_source
            
            # ফলাফল যাচাই: বাংলা ও ইংরেজি দুটি মেসেজই চেক করা
            if "doesn't match an account" in page_source or "আপনার দেওয়া তথ্যের সাথে কোনো অ্যাকাউন্ট খুঁজে পাইনি" in page_source:
                return 'id_not_found'
            else:
                return 'id_found'
                
        except (NoSuchElementException, TimeoutException):
            print("Search element interaction failed or timed out.")
            return 'error_page_structure'
            
    except Exception as e:
        # কোনো বড় ত্রুটি হলে, এটিকে লগে দেখাবে
        print(f"--- FATAL SELENIUM ERROR ---: {e}") 
        return 'error_general'
        
    finally:
        # ব্রাউজার বন্ধ করা
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
            # যদি 'error_general' বা 'error_page_structure' আসে
            return jsonify({'status': 'error', 'message': 'An internal issue occurred during the Facebook check.'}), 500
            
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
