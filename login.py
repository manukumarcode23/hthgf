import time
import cv2
import numpy as np
import pyautogui
import json
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Paths to button images
LOGIN_BUTTON_IMAGE_PATH = "login_button.png"
EMAIL_INPUT_IMAGE_PATH = "email_input.png"
PASSWORD_INPUT_IMAGE_PATH = "password_input.png"
FINAL_LOGIN_BUTTON_IMAGE_PATH = "final_login_button.png"
ACCOUNTS_JSON_PATH = "accounts.json"

# Create cookies directory if not exists
COOKIES_DIR = os.path.join(os.getcwd(), "cookies")
if not os.path.exists(COOKIES_DIR):
    os.makedirs(COOKIES_DIR)

def open_browser():
    """Opens Chrome in incognito mode and navigates to the target website."""
    options = Options()
    options.add_argument("--incognito")
    options.add_argument("no-sandbox")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    url = "https://www.1024tera.com/sharing/link?surl=XArbV4UEK12YORhU6Ci25w"
    print(f"🌐 Opening URL: {url}")
    driver.get(url)
    time.sleep(5)  # Allow full page load

    return driver

def find_and_click(image_path, offset_x=0, offset_y=0):
    """
    Uses image recognition to find and click an element on the screen.
    """
    print(f"🔍 Searching for element in {image_path} using image recognition...")
    screen = pyautogui.screenshot()
    screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
    
    element_img = cv2.imread(image_path)
    
    result = cv2.matchTemplate(screen, element_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val > 0.8:  # Adjust threshold if needed
        element_x, element_y = max_loc
        element_width = element_img.shape[1]  
        element_height = element_img.shape[0]  

        click_x = element_x + int(element_width * 0.4) + offset_x  
        click_y = element_y + int(element_height / 2) + offset_y  

        pyautogui.click(click_x, click_y)
        print(f"✅ Element clicked at ({click_x}, {click_y}) using image recognition!")
        return True
    else:
        print(f"❌ Element not found: {image_path}")
        return False

def type_text(text):
    """Types the given text using pyautogui."""
    print(f"⌨️ Typing: {text}")
    pyautogui.typewrite(text, interval=0.1)
    print("✅ Text typed successfully!")

def extract_cookies(driver, index):
    """Extracts cookies and saves them to a file."""
    try:
        output_file = os.path.join(COOKIES_DIR, f"cookies{index}.txt")
        
        all_cookies = driver.execute_script("""
            let cookieString = '';
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                cookieString += cookies[i].trim() + '; ';
            }
            return cookieString;
        """)

        with open(output_file, 'w') as f:
            f.write(all_cookies.strip())

        print(f"✅ Cookies saved to: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error extracting cookies: {e}")
        return False

def get_next_cookie_index():
    """Determines the next available cookie file index."""
    existing_files = [f for f in os.listdir(COOKIES_DIR) if f.startswith("cookies") and f.endswith(".txt")]
    if existing_files:
        existing_indices = [int(re.search(r"cookies(\d+)\.txt", f).group(1)) for f in existing_files if re.search(r"cookies(\d+)\.txt", f)]
        return max(existing_indices) + 1
    return 1

def read_credentials_from_json(json_path):
    """Reads all emails and passwords from accounts.json file."""
    try:
        with open(json_path, "r") as file:
            accounts = json.load(file)
        return accounts if isinstance(accounts, list) else []
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return []

def login_and_extract_cookies(email, password, cookie_index):
    """Logs in using image recognition, extracts cookies, and saves them."""
    driver = open_browser()
    
    print("🔄 Trying image recognition method for login button...")
    if find_and_click(LOGIN_BUTTON_IMAGE_PATH, offset_x=5):
        time.sleep(5)

        print("🔄 Searching for email input field...")
        if find_and_click(EMAIL_INPUT_IMAGE_PATH, offset_x=10):
            time.sleep(2)
            type_text(email)
            time.sleep(2)

            print("🔄 Searching for password input field...")
            if find_and_click(PASSWORD_INPUT_IMAGE_PATH, offset_x=10):
                time.sleep(2)
                type_text(password)
                time.sleep(2)

                print("🔄 Searching for final login button...")
                if find_and_click(FINAL_LOGIN_BUTTON_IMAGE_PATH, offset_x=10):
                    time.sleep(10)
                    extract_cookies(driver, cookie_index)
    
    driver.quit()
    print("✅ Browser session closed.")

def main():
    accounts = read_credentials_from_json(ACCOUNTS_JSON_PATH)
    if not accounts:
        print("❌ No accounts found in JSON file. Exiting.")
        return

    cookie_index = get_next_cookie_index()
    
    for account in accounts:
        email = account.get("email")
        password = account.get("password")
        if email and password:
            print(f"\n🔵 Logging in with email: {email}")
            login_and_extract_cookies(email, password, cookie_index)
            cookie_index += 1  # Increment index for next account

if __name__ == "__main__":
    main()
