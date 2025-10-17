import os
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS # CORS ফিক্সের জন্য ইমপোর্ট করা হয়েছে
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

app = Flask(__name__)
# *** সমাধান: CORS নীতি সেট করুন যাতে যেকোনো ডোমেইন থেকে অ্যাক্সেস করা যায় ***
CORS(app) 

# Railway-এর জন্য ChromeDriver এর পথ:
CHROME_DRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver") 

def check_facebook_id(number_to_check):
    """
    Headless Chrome ব্যবহার করে Facebook-এ ফোন নম্বর অনুসন্ধান করে।
    """
    
    # 1. Chrome Options সেটআপ
    options = Options()
    options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,1024")
    options.add_argument("--remote-debugging-host=0.0.0.0")
    options.add_argument("--remote-debugging-port=9222")

    # 2. Driver Initialization
    driver = None
    try:
        service = ChromeService(executable_path=CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        
        # 3. Navigation
        url = "https://mbasic.facebook.com/login/identify/"
        driver.get(url)
        
        # 4. Cookie Handling (যদি আসে)
        try:
            WebDriverWait(driver, 7).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="cookie-policy-dialog-accept-button"]'))
            ).click()
        except TimeoutException:
            pass
            
        # 5. Phone Number Search
        try:
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "identify_search_text_input"))
            )
            search_input.send_keys(number_to_check)
            
            search_button = driver.find_element(By.NAME, "did_submit")
            search_button.click()
            
            # 6. অপেক্ষা ও ফলাফল যাচাই
            time.sleep(4) 
            
            page_source = driver.page_source
            
            if "doesn't match an account" in page_source or "আপনার দেওয়া তথ্যের সাথে কোনো অ্যাকাউন্ট খুঁজে পাইনি" in page_source:
                return 'id_not_found'
            else:
                return 'id_found'
                
        except NoSuchElementException:
            print("Search element not found, page structure changed.")
            return 'error_page_structure'
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
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
            return jsonify({'status': 'error', 'message': 'An issue occurred during the check'}), 500
            
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
