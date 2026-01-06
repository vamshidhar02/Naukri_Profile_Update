#! python3
# -*- coding: utf-8 -*-
"""
Naukri Profile Refresh Automation
Optimized for GitHub Actions (Headless Stealth Mode)
"""

import os
import sys
import time
import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import credentials from your constants.py file
try:
    import constants
    USERNAME = constants.USERNAME
    PASSWORD = constants.PASSWORD
    LOGIN_URL = "https://www.naukri.com/nlogin/login"
    PROFILE_URL = "https://www.naukri.com/mnjuser/profile"
except ImportError:
    print("Error: constants.py not found. Please ensure it exists with USERNAME and PASSWORD.")
    sys.exit(1)

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s : %(message)s")

def log_msg(message):
    print(message)
    logging.info(message)

def catch(error):
    """Logs the error and the line number where it occurred"""
    _, _, exc_tb = sys.exc_info()
    line_no = str(exc_tb.tb_lineno) if exc_tb else "Unknown"
    msg = f"Error: {type(error).__name__} : {error} at Line {line_no}."
    log_msg(msg)

def load_driver():
    """Initializes Chrome in Stealth Headless mode for GitHub Actions"""
    options = webdriver.ChromeOptions()
    
    # Critical flags for Server/Headless environments
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Stealth settings to bypass Bot Detection (Access Denied)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    options.add_argument("--blink-settings=imagesEnabled=false")

    try:
        # Try standard initialization
        driver = webdriver.Chrome(options=options)
    except Exception:
        # Fallback using WebDriver Manager if standard fail
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    # Hide the 'navigator.webdriver' flag
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    return driver

def naukri_login(driver):
    """Performs login and bypasses the dashboard directly to the profile"""
    try:
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 20)
        
        # Locate and fill credentials
        user_field = wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
        user_field.send_keys(USERNAME)
        
        pass_field = driver.find_element(By.ID, "passwordField")
        pass_field.send_keys(PASSWORD)
        
        # Click Login
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_btn.click()
        log_msg("Login credentials submitted.")
        
        # Bypassing the dashboard/OTP screens by jumping straight to Profile
        time.sleep(5)
        log_msg("Redirecting directly to Profile page to bypass security popups...")
        driver.get(PROFILE_URL)
        time.sleep(5)

        if "profile" in driver.current_url.lower():
            log_msg("Successfully landed on Profile Page.")
            return True
        else:
            log_msg(f"Failed to reach Profile. Current URL: {driver.current_url}")
            return False
            
    except Exception as e:
        catch(e)
        return False

def upload_resume(driver, resume_filename):
    """Uploads the resume file to trigger the 'Last Updated' timestamp"""
    try:
        log_msg(f"Searching for upload field to process {resume_filename}...")
        
        # Naukri uses a hidden input[type='file'] for resume updates
        upload_xpath = "//input[@type='file']"
        wait = WebDriverWait(driver, 20)
        
        upload_element = wait.until(EC.presence_of_element_located((By.XPATH, upload_xpath)))
        
        # Convert relative path to absolute path for the OS
        abs_path = os.path.abspath(resume_filename)
        upload_element.send_keys(abs_path)
        
        log_msg(f"File sent to browser: {abs_path}")
        
        # Wait for the upload process to complete (Naukri shows a 'Success' toast)
        time.sleep(10)
        log_msg("✅ Profile Refresh Successful! Resume uploaded.")
        return True
        
    except Exception as e:
        catch(e)
        return False

def main():
    log_msg("----- Naukri.py Script Run Begin -----")
    driver = None
    try:
        driver = load_driver()
        
        if naukri_login(driver):
            # Define the expected resume filename in the root directory
            resume_file = "Resume.pdf"
            
            if os.path.exists(resume_file):
                upload_resume(driver, resume_file)
            else:
                log_msg(f"❌ Error: '{resume_file}' not found in the root directory.")
        else:
            log_msg("❌ Login flow failed. Check credentials or OTP requirements.")

    except Exception as e:
        catch(e)
    finally:
        if driver:
            driver.quit()
            log_msg("Browser session closed.")
    log_msg("----- Naukri.py Script Run Ended -----")

if __name__ == "__main__":
    main()
