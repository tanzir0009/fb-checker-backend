from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import os
import sys

# Railway/Docker পরিবেশে Chromium-এর পথ
CHROME_DRIVER_PATH = "/usr/bin/chromedriver" 

app = Flask(__name__)

def check_facebook_id(number_to_check):
    """
    Selenium ব্যবহার করে একটি নম্বর Facebook-এ খুঁজে পাওয়া যায় কিনা তা পরীক্ষা করে।
    """
    driver = None
    try:
        # Chrome Options সেটআপ
        options = Options()
        # সার্ভার/হোস্টিং পরিবেশে চালানোর জন্য REQUIRED Headless Options
        options.add_argument("--headless")
        options.add_argument("--no-sandbox") # Docker/Linux পরিবেশে অপরিহার্য
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # ড্রাইভার সার্ভিস ইনিশিয়ালাইজেশন (Railway/Docker-এর জন্য)
        service = Service(executable_path=CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get("https://mbasic.facebook.com/login/identify/")

        # কুকি হ্যান্ডলিং (ঐচ্ছিক)
        try:
            cookie_button = WebDriverWait(driver, 7).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@data-testid='cookie-policy-manage-dialog-accept-button']")
                )
            )
            cookie_button.click()
        except TimeoutException:
            pass
        except Exception as e:
            print(f"Cookie click error: {e}", file=sys.stderr)

        # নম্বর অনুসন্ধান প্রক্রিয়া
        try:
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "identify_search_text_input"))
            )
            search_input.send_keys(str(number_to_check))
            
            submit_button = driver.find_element(By.NAME, "did_submit")
            submit_button.click()
            
            time.sleep(5) 
            
            # আইডি না মেলার বার্তা পরীক্ষা
            if "doesn't match an account" in driver.page_source:
                return 'id_not_found'
            
            return 'id_found'
            
        except NoSuchElementException:
            return 'search_elements_missing'
        except TimeoutException:
            return 'page_load_timeout'

    except WebDriverException as e:
        print(f"WebDriver Initialization Error: {e}", file=sys.stderr)
        return 'driver_init_failed'
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 'unknown_error'
    finally:
        if driver:
            driver.quit()

@app.route('/check-facebook-id', methods=['POST'])
def api_endpoint():
    """
    ফ্রন্ট-এন্ড থেকে JSON ডেটা গ্রহণ করে এবং ফলাফল JSON এ রিটার্ন করে।
    """
    try:
        # Cross-Origin Resource Sharing (CORS) অনুমতি প্রদান
        # Railway-তে যখন ফ্রন্ট-এন্ড এবং ব্যাক-এন্ড আলাদা ডোমেইনে থাকে, তখন এটি প্রয়োজন
        from flask_cors import CORS
        CORS(app) 
        
        data = request.get_json()
        number = data.get('number')
        
        if not number:
            return jsonify({"status": "error", "message": "অনুসন্ধানের জন্য নম্বর আবশ্যক।"}), 400

        result_code = check_facebook_id(number)
        
        return jsonify({"status": "success", "result": result_code})

    except Exception as e:
        print(f"API Handler Error: {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": "সার্ভারে ডেটা প্রক্রিয়াকরণে সমস্যা হয়েছে।"}), 500

if __name__ == '__main__':
    # Railway পোর্ট এনভায়রনমেন্ট ভেরিয়েবল থেকে আসে
    port = int(os.environ.get('PORT', 5000))
    # Gunicorn ব্যবহার করে হোস্ট করা ভালো, তবে লোকাল টেস্টিং এর জন্য Flask-এর ডিফল্ট রান ব্যবহার করা যেতে পারে:
    # app.run(host='0.0.0.0', port=port, debug=False)
    # Railway-এর জন্য এই ফাইলটিকে Gunicorn দিয়ে চালানো হবে (CMD-তে দেখুন)।
    print(f"Flask app starting on port {port}")
