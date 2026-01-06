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
        
        # 1. Wait for fields
        user_input = wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
        pass_input = driver.find_element(By.ID, "passwordField")
        
        # 2. CLEAR POPUPS: Remove any overlapping elements using JavaScript
        # This targets the common 'one-tap' login and cookie banners
        driver.execute_script("""
            var elements = document.querySelectorAll('.m-one-tap-container, .modal, .overlay, #cookie_policy_banner');
            for(var i=0; i<elements.length; i++){
                elements[i].style.display='none';
            }
        """)
        time.sleep(2)

        # 3. Fill Credentials
        user_input.clear()
        user_input.send_keys(USERNAME)
        pass_input.clear()
        pass_input.send_keys(PASSWORD)
        
        # 4. FORCE CLICK: Use JavaScript to click the button directly
        # This bypasses the 'not interactable' error entirely
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].click();", login_btn)
        
        log_msg("Login forced via JS. Waiting for redirect...")
        time.sleep(10) # Give it extra time for the security check
        
        driver.get(PROFILE_URL)
        time.sleep(5)
        
        if "profile" in driver.current_url.lower():
            log_msg("Successfully reached Profile Page.")
            return True
        else:
            log_msg(f"Failed to reach profile. Current URL: {driver.current_url}")
            return False
    except Exception as e:
        log_msg(f"Login Error: {e}")
        driver.save_screenshot("login_error.png") # Capture what is blocking the button
        return False

def update_headline(driver):
    try:
        wait = WebDriverWait(driver, 20)
        log_msg("Starting headline update process...")

        # 1. Scroll down and up to trigger lazy loading of profile elements
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        # 2. Try multiple XPATHs for the Edit Pencil (Naukri changes these often)
        edit_selectors = [
            "//span[contains(@class, 'editIcon')]",
            "//span[contains(@class, 'icon-edit')]",
            "//div[contains(@class, 'resume-headline')]//span[contains(@class, 'edit')]",
            "//em[text()='edit']"
        ]
        
        edit_pencil = None
        for selector in edit_selectors:
            try:
                edit_pencil = driver.find_element(By.XPATH, selector)
                if edit_pencil.is_displayed():
                    log_msg(f"Found edit button with: {selector}")
                    break
            except:
                continue

        if not edit_pencil:
            log_msg("❌ Could not find Edit button. Saving screenshot...")
            driver.save_screenshot("edit_not_found.png")
            return False

        # 3. Click Edit using JS to be safe
        driver.execute_script("arguments[0].click();", edit_pencil)
        
        # 4. Update Headline Text
        headline_field = wait.until(EC.presence_of_element_located((By.ID, "resumeHeadlineText")))
        current_text = headline_field.get_attribute("value")
        
        # Toggle period
        new_text = current_text[:-1] if current_text.endswith(".") else current_text + "."
        
        # Using JS to set value ensures it works even if field is slightly obscured
        driver.execute_script("arguments[0].value = '';", headline_field)
        headline_field.send_keys(new_text)
        
        # 5. Click Save
        save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Save']")))
        driver.execute_script("arguments[0].click();", save_btn)
        
        time.sleep(5)
        log_msg(f"✅ Profile Freshness Boosted! Headline: {new_text}")
        return True
    except Exception as e:
        log_msg(f"Update Error: {e}")
        driver.save_screenshot("headline_error.png")
        return False

if __name__ == "__main__":
    log_msg("Starting Naukri Update...")
    drvr = get_driver()
    if login_and_jump(drvr):
        update_headline(drvr)
    drvr.quit()
    log_msg("Done.")
