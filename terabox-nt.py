import os
import json
import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TOKEN_FILE = "mail-token.json"
ACCOUNTS_FILE = "accounts.json"
PASSWORD = "FR13NDSclay"

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return []

tokens = load_tokens()
token_index = 0

def get_api_headers(token):
    return {"Authorization": token}

def get_temp_email(token):
    headers = get_api_headers(token)
    url = "https://tempmail100.com/web/generate"
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", {}).get("address", "")
    return ""

def get_otp(token):
    headers = get_api_headers(token)
    url = "https://tempmail100.com/web/emails"
    for _ in range(2):  # Only retry twice
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            emails = response.json().get("data", {}).get("list", [])
            if emails:
                for email in emails:
                    subject = email.get("subject", "")
                    otp_match = re.search(r"(\d{4,6})", subject)
                    if otp_match:
                        return otp_match.group(1)
        print("No OTP received yet. Retrying...")
        time.sleep(5)
    return None

def save_account(email, password, token_id):
    accounts = []
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            try:
                accounts = json.load(f)
            except json.JSONDecodeError:
                pass
    accounts.append({"email": email, "password": password, "token_id": token_id})
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=4)
    print(f"✅ Account saved: {email} (Token ID: {token_id})")

def create_account():
    global token_index
    if not tokens:
        print("No API tokens available.")
        return False
    
    token_data = tokens[token_index % len(tokens)]
    token = token_data["token"]
    token_id = token_data["id"]
    token_index += 1
    
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
    
    try:
        temp_email = get_temp_email(token)
        if not temp_email:
            print("Failed to fetch temporary email.")
            driver.quit()
            return False
        
        print(f"📧 Temporary Email: {temp_email} (Token ID: {token_id})")
        driver.get("https://www.1024terabox.com/wap/outlogin/emailRegister?redirectUrl=https://www.1024terabox.com/wap/webmaster/?isClickLogin=true&tab=2")
        time.sleep(5)
        
        email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email-input")))
        email_input.send_keys(temp_email)
        
        submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-class-register")))
        submit_button.click()
        
        print("⏳ Waiting for OTP...")
        otp = get_otp(token)
        if otp:
            print(f"Received OTP: {otp}")
            otp_inputs = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".captcha-input input[type='text']"))
            )
            for i, digit in enumerate(otp):
                if i < len(otp_inputs):
                    otp_inputs[i].send_keys(digit)
            print("OTP submitted successfully.")
        else:
            print("Failed to retrieve OTP.")
            driver.quit()
            return False
        
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password'][placeholder='Enter your password']"))
        )
        password_input.send_keys(PASSWORD)
        print("Password entered.")
        
        create_account_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-class-register"))
        )
        create_account_button.click()
        print("Account creation process started.")
        
        time.sleep(15)
        save_account(temp_email, PASSWORD, token_id)
        driver.quit()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        driver.quit()
        return False

def main():
    while True:
        print("\n=== Creating a new account ===")
        success = create_account()
        if success:
            print("✅ Account created successfully!")
        else:
            print("❌ Failed to create account. Retrying in 20 seconds...")
        print("⏳ Waiting 20 seconds before creating the next account...")
        for i in range(20, 0, -1):
            print(f"{i} seconds remaining...")
            time.sleep(1)

if __name__ == "__main__":
    main()
