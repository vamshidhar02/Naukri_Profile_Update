import os
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import constants

# Credentials from Secrets/Constants
USERNAME = constants.USERNAME
PASSWORD = constants.PASSWORD
LOGIN_URL = "https://www.naukri.com/nlogin/login"
PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

logging.basicConfig(level=logging.INFO, format="%(asctime)s : %(message)s")

def log_msg(msg):
    print(msg)
    logging.info(msg)

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def login_and_jump(driver):
    try:
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 20)
        
        # Fill Credentials
        wait.until(EC.presence_of_element_located((By.ID, "usernameField"))).send_keys(USERNAME)
        driver.find_element(By.ID, "passwordField").send_keys(PASSWORD)
        
        # JS Click Login
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].click();", login_btn)
        log_msg("Login clicked. Waiting for redirect...")
        
        time.sleep(7)
        driver.get(PROFILE_URL)
        time.sleep(5)
        
        if "profile" in driver.current_url:
            log_msg("Landed on Profile Page.")
            return True
        return False
    except Exception as e:
        log_msg(f"Login Error: {e}")
        return False

def update_headline(driver):
    try:
        wait = WebDriverWait(driver, 20)
        
        # Click the edit icon for Basic Details
        edit_pencil = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'editIcon')]")))
        driver.execute_script("arguments[0].click();", edit_pencil)
        
        # Update Headline Text
        headline_field = wait.until(EC.presence_of_element_located((By.ID, "resumeHeadlineText")))
        current_text = headline_field.get_attribute("value")
        
        # Toggle a period at the end to force an 'update'
        new_text = current_text[:-1] if current_text.endswith(".") else current_text + "."
        
        headline_field.clear()
        headline_field.send_keys(new_text)
        
        # Click Save
        save_btn = driver.find_element(By.XPATH, "//button[text()='Save']")
        driver.execute_script("arguments[0].click();", save_btn)
        
        time.sleep(3)
        log_msg(f"✅ Headline updated to: {new_text}")
        return True
    except Exception as e:
        log_msg(f"Update Error: {e}")
        # Take a screenshot on failure to debug via Artifacts
        driver.save_screenshot("error_screenshot.png")
        return False

if __name__ == "__main__":
    log_msg("Starting Naukri Update...")
    drvr = get_driver()
    if login_and_jump(drvr):
        update_headline(drvr)
    drvr.quit()
    log_msg("Done.")
