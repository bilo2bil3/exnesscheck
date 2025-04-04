import time
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

def get_auth_token_with_selenium(email, password):
    """Use Selenium to authenticate with the Exness Affiliates website and extract the token"""
    
    try:
        logger.info("Attempting to authenticate using Selenium browser automation")
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Initialize the Chrome driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        try:
            # Navigate to the login page
            login_url = "https://my.exnessaffiliates.com/en/auth/login/"
            driver.get(login_url)
            logger.info(f"Navigated to login page: {login_url}")
            
            # Wait for the page to load completely and bypass any security checks
            time.sleep(5)
            
            # Find and fill in the email input
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
                )
                email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
                email_input.clear()
                email_input.send_keys(email)
                logger.info("Email entered successfully")
            except (TimeoutException, NoSuchElementException) as e:
                logger.error(f"Could not find email input: {e}")
                return None
            
            # Find and fill in the password input
            try:
                password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                password_input.clear()
                password_input.send_keys(password)
                logger.info("Password entered successfully")
            except NoSuchElementException as e:
                logger.error(f"Could not find password input: {e}")
                return None
            
            # Find and click the login button
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_button.click()
                logger.info("Login button clicked")
            except NoSuchElementException as e:
                logger.error(f"Could not find login button: {e}")
                return None
            
            # Wait for login to complete and redirect
            time.sleep(5)
            
            # Extract the token from local storage
            try:
                token = driver.execute_script("return localStorage.getItem('token');")
                if token:
                    logger.info("Successfully extracted auth token with Selenium")
                    
                    # Also save cookies
                    cookies = driver.get_cookies()
                    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                    
                    return {
                        'token': token,
                        'cookies': cookie_dict
                    }
                else:
                    # If token not found in localStorage, check for it in the network requests
                    logger.warning("Token not found in localStorage, checking page for auth info")
                    page_source = driver.page_source
                    
                    # Log the current URL to see if login was successful
                    logger.info(f"Current URL after login attempt: {driver.current_url}")
                    
                    if "dashboard" in driver.current_url or "reports" in driver.current_url:
                        logger.info("Login appears successful based on URL")
                        
                        # Get all cookies
                        cookies = driver.get_cookies()
                        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                        
                        # Try to get auth token via JavaScript
                        possible_token_locations = [
                            "localStorage.getItem('token')",
                            "localStorage.getItem('auth_token')",
                            "localStorage.getItem('accessToken')",
                            "document.cookie.match(/(?:^|;\\s*)token=([^;]*)/)",
                            "document.cookie"
                        ]
                        
                        for location in possible_token_locations:
                            try:
                                result = driver.execute_script(f"return {location};")
                                if result and len(result) > 20:  # Tokens are usually long
                                    logger.info(f"Found potential token in {location}")
                                    return {
                                        'token': result,
                                        'cookies': cookie_dict
                                    }
                            except Exception as e:
                                logger.warning(f"Error getting token from {location}: {e}")
                        
                        # If we got here but couldn't find a token, return cookies only
                        logger.warning("No token found, but login successful. Returning cookies only.")
                        return {
                            'token': None,
                            'cookies': cookie_dict
                        }
            except Exception as e:
                logger.error(f"Error extracting token: {e}")
            
            logger.error("Failed to extract auth token with Selenium")
            return None
            
        finally:
            # Close the browser
            driver.quit()
            logger.info("Selenium browser closed")
    
    except Exception as e:
        logger.error(f"Selenium authentication error: {e}")
        return None 