#!/usr/bin/env python3
"""
WebUntis Auto-Login Script (FSV-Zugang SSO)
A simple Python program to automate login to WebUntis via FSV-Zugang SSO
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from dotenv import load_dotenv

load_dotenv()


class WebUntisAutoLogin:
    """Automated login handler for WebUntis via FSV-Zugang SSO"""

    # URLs
    WEBUNTIS_URL = "https://peleus.webuntis.com/WebUntis/?school=Ferd.von+Steinbeis#/basic/login"
    SSO_DOMAIN = "idam.steinbeis.schule"

    # Timeouts
    DEFAULT_TIMEOUT = 10
    LONG_TIMEOUT = 30

    def __init__(self, username=None, password=None, headless=False):
        """
        Initialize the auto-login handler

        Args:
            username (str): FSV username or email
            password (str): FSV password
            headless (bool): Run browser in headless mode
        """
        self.username = username or os.getenv("FSV_USERNAME")
        self.password = password or os.getenv("FSV_PASSWORD")
        self.headless = headless
        self.driver = None
        self.wait = None

        if not self.username or not self.password:
            raise ValueError("Username and password must be provided or set in environment variables")

    def setup_driver(self):
        """Initialize the Chrome WebDriver with appropriate options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Additional options for better compatibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Set a realistic user agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Initialize driver
        self.driver = webdriver.Chrome(options=chrome_options)

        # Set window size (important for element visibility)
        if not self.headless:
            self.driver.maximize_window()
        else:
            self.driver.set_window_size(1920, 1080)

        # Initialize wait
        self.wait = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT)

        print("✓ WebDriver initialized")

    def navigate_to_webuntis(self):
        """Navigate to WebUntis login page"""
        print(f"Navigating to WebUntis...")
        self.driver.get(self.WEBUNTIS_URL)

        # Wait for the page to be in a ready state
        time.sleep(3)

        # Wait for the body to be present (page loaded)
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except:
            pass

        # Additional wait for JavaScript to execute
        time.sleep(2)

        print("✓ Navigated to WebUntis")

    def click_fsv_zugang(self):
        """Click the FVS-Zugang (SSO) button"""
        print("Looking for FVS-Zugang button...")

        try:
            # Wait for button to be present and visible
            wait = WebDriverWait(self.driver, 20)

            # Find the button
            fsv_button = wait.until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'FVS-Zugang')]"))
            )
            print("✓ Found FVS-Zugang button")

            # Wait a moment for any animations
            time.sleep(1)

            # Use JavaScript to click - most reliable method
            self.driver.execute_script("arguments[0].click();", fsv_button)
            print("✓ Clicked FVS-Zugang button")

            # Wait for redirect to SSO page
            print("Waiting for redirect to SSO page...")
            wait.until(EC.url_contains(self.SSO_DOMAIN))
            print("✓ Redirected to SSO page")

        except TimeoutException as e:
            print(f"✗ Timeout error: {e}")
            print(f"Current URL: {self.driver.current_url}")

            # Debug: show available buttons
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                print("Available buttons:")
                for i, btn in enumerate(buttons[:10]):
                    print(f"  {i}: '{btn.text}'")
            except:
                pass

            raise
        except Exception as e:
            print(f"✗ Error: {e}")

            # Save screenshot for debugging
            try:
                self.driver.save_screenshot("error_screenshot.png")
                print("Screenshot saved to error_screenshot.png")
            except:
                pass

            raise

    def fill_sso_credentials(self):
        """Fill in username and password on SSO page"""
        print("Filling in SSO credentials...")

        try:
            # Wait for username field to be present
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )

            # Wait for password field
            password_field = self.driver.find_element(By.ID, "password")

            # Clear and fill username
            username_field.clear()
            username_field.send_keys(self.username)
            print(f"✓ Entered username: {self.username}")

            # Clear and fill password
            password_field.clear()
            password_field.send_keys(self.password)
            print("✓ Entered password")

        except (TimeoutException, NoSuchElementException) as e:
            print(f"✗ Error finding login fields: {e}")
            raise

    def submit_login(self):
        """Submit the login form"""
        print("Submitting login form...")

        try:
            # Find and click the login button
            login_button = self.driver.find_element(By.ID, "kc-login")
            login_button.click()
            print("✓ Clicked login button")

            # Wait for redirect back to WebUntis (OAuth callback)
            wait_long = WebDriverWait(self.driver, self.LONG_TIMEOUT)
            wait_long.until(EC.url_contains("peleus.webuntis.com"))
            print("✓ Redirected back to WebUntis (OAuth callback)")

            # At this point we're at the ROOT URL, not the actual app
            # The SPA needs to navigate to establish the session with JSESSIONID
            print("Loading WebUntis dashboard to establish session...")
            self.driver.get("https://peleus.webuntis.com/WebUntis/?school=Ferd.von+Steinbeis#/today")

            # Wait for page to be fully loaded (document.readyState === 'complete')
            print("Waiting for dashboard to fully load...")
            wait_long.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

            # Wait for SPA to initialize and session to be created
            time.sleep(5)
            print("✓ Dashboard loaded - session established")

        except TimeoutException:
            print("✗ Timeout: Login may have failed or took too long")
            raise

    def verify_login(self):
        """Verify that login was successful"""
        print("Verifying login...")

        try:
            # Check current URL
            current_url = self.driver.current_url
            print(f"Current URL: {current_url}")

            # We should already be on the dashboard from submit_login()
            # Just need to verify elements are present
            print("Checking for dashboard elements...")
            time.sleep(2)  # Brief wait for elements to render

            # Look for elements that indicate successful login
            try:
                # Try to find dashboard elements
                dashboard_element = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//h1 | //h3 | //a[contains(@href, 'main')] | //*[contains(text(), 'Heute')]"))
                )
                print("✓ Login successful - Dashboard elements found!")

                # Wait a bit more to ensure all session cookies are set
                print("Ensuring all session cookies are set...")
                time.sleep(2)

                return True
            except TimeoutException:
                # If we can't find the dashboard element, check if we're at least not on login page
                if "login" not in current_url.lower():
                    print("✓ Login appears successful (no longer on login page)")
                    return True
                else:
                    print("✗ Still on login page - login may have failed")
                    return False

        except Exception as e:
            print(f"✗ Error verifying login: {e}")
            return False

    def get_session_data(self):
        """Extract cookies and bearer token and return as dictionary"""
        try:
            # Wait a moment to ensure all cookies are set
            print("\nExtracting session data...")
            time.sleep(2)

            # Get all cookies using Chrome DevTools Protocol
            cookies = self.driver.execute_cdp_cmd("Network.getAllCookies", {}).get("cookies", [])

            # Debug: Show all cookies
            print(f"Captured {len(cookies)} cookies")
            jsessionid_found = False
            for cookie in cookies:
                cookie_name = cookie.get('name', '')
                if 'jsessionid' in cookie_name.lower():
                    jsessionid_found = True
                    print(f"  ✓ JSESSIONID found!")

            if not jsessionid_found:
                print("  ⚠ Warning: JSESSIONID not found in cookies")

            # Try to extract bearer token by calling the token endpoint
            bearer_token = None
            person_id = None
            tenant_id = None

            try:
                print("Extracting bearer token...")
                # Execute a request to get the bearer token
                token_response = self.driver.execute_script("""
                    return fetch('https://peleus.webuntis.com/WebUntis/api/token/new')
                        .then(response => response.text())
                        .then(data => data.replace(/"/g, ''))
                        .catch(err => null);
                """)

                if token_response:
                    bearer_token = token_response

                    # Parse the JWT to extract person_id and tenant_id
                    import base64
                    import json
                    try:
                        payload = bearer_token.split('.')[1]
                        payload += '=' * (4 - len(payload) % 4)
                        decoded = json.loads(base64.b64decode(payload))
                        person_id = decoded.get('person_id')
                        tenant_id = decoded.get('tenant_id')
                        username = decoded.get('username')

                        print(f"✓ Extracted bearer token")
                        print(f"  Username: {username}")
                        print(f"  Person ID: {person_id}")
                        print(f"  Tenant ID: {tenant_id}")
                    except Exception as e:
                        print(f"  Warning: Could not parse token: {e}")
            except Exception as e:
                print(f"  Warning: Could not extract bearer token: {e}")

            # Return session data
            session_data = {
                'cookies': cookies,
                'bearer_token': bearer_token,
                'person_id': person_id,
                'tenant_id': tenant_id,
                'timestamp': time.time()
            }

            print(f"✓ Session data extracted successfully")
            return session_data

        except Exception as e:
            print(f"✗ Error extracting session data: {e}")
            import traceback
            traceback.print_exc()
            return None

    def login(self):
        """
        Perform the complete login process

        Returns:
            dict: Session data with cookies and bearer token if successful, None otherwise
        """
        try:
            print("\n" + "="*60)
            print("WebUntis Auto-Login (FSV-Zugang SSO)")
            print("="*60 + "\n")

            # Setup driver
            self.setup_driver()

            # Perform fresh login
            print("Performing fresh login...")
            self.navigate_to_webuntis()
            self.click_fsv_zugang()
            self.fill_sso_credentials()
            self.submit_login()

            # Verify and extract session data
            if self.verify_login():
                session_data = self.get_session_data()
                if session_data:
                    print("\n" + "="*60)
                    print("✓ LOGIN SUCCESSFUL!")
                    print("="*60 + "\n")
                    return session_data
                else:
                    print("\n" + "="*60)
                    print("✗ FAILED TO EXTRACT SESSION DATA!")
                    print("="*60 + "\n")
                    return None
            else:
                print("\n" + "="*60)
                print("✗ LOGIN FAILED!")
                print("="*60 + "\n")
                return None

        except Exception as e:
            print(f"\n✗ Error during login: {e}")
            return None

    def close(self):
        """Close the browser"""
        if self.driver:
            print("\nClosing browser...")
            self.driver.quit()
            print("✓ Browser closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def main():
    """Main entry point"""
    # Get credentials from environment variables or prompt user
    username = os.getenv("FSV_USERNAME")
    password = os.getenv("FSV_PASSWORD")

    if not username:
        username = input("Enter FSV username: ")
    if not password:
        import getpass
        password = getpass.getpass("Enter FSV password: ")

    # Create instance and login
    with WebUntisAutoLogin(username, password, headless=False) as auto_login:
        session_data = auto_login.login()

        if session_data:
            print("\nYou are now logged in!")
            print(f"Session data contains:")
            print(f"  - {len(session_data['cookies'])} cookies")
            print(f"  - Bearer token: {'Yes' if session_data['bearer_token'] else 'No'}")
            print(f"  - Person ID: {session_data['person_id']}")
            print(f"  - Tenant ID: {session_data['tenant_id']}")
            print("\nBrowser will remain open for 30 seconds...")
            time.sleep(30)
        else:
            print("\nLogin failed. Please check your credentials.")
            time.sleep(5)


if __name__ == "__main__":
    main()

