from dotenv import load_dotenv, dotenv_values
import logging
from datetime import datetime, timedelta
import pickle
from playwright.sync_api import sync_playwright
import steam.webauth as wa
import os

class Worker:

    def __init__(self, username: str, password: str, otp_code: str) -> None:
        self._username = username
        self._password = password
        self._otp_code = otp_code
        self.loadenv = load_dotenv()

    def run(self):
        # Set up logging configuration
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            if os.path.exists(f"{self._username}.pkl"):
                #loadout cookies into the playwright
                with open(f"{self._username}.pkl", 'rb') as pickle_file:
                    saved_cookies = pickle.load(pickle_file)
                context.add_cookies(saved_cookies)
            else:
                try:
                    user = wa.WebAuth(username=self._username)
                    try:
                        user.cli_login(password=self._password, twofactor_code=self._otp_code)
                    except wa.CaptchaRequired:
                        logging.error("Captcha Required")
                        print(user.captcha_url)
                    except wa.TwoFactorCodeRequired:
                        logging.error("Two-factor authentication code required.")
                        # This code is for when Steam Guard two-factor authentication is required
                        user.login(twofactor_code=self._otp_code)
                        # Ask a human to solve the captcha and then provide the solution
                        captcha_solution = input("Enter captcha solution: ")
                        user.login(password=self._password, captcha=captcha_solution)
                    except wa.LoginIncorrect:
                        logging.error("Login Incorrect")
                        # Save the cookies from the session using pickle
                    cookies_to_save = []
                    new_expiry = datetime.now() + timedelta(days=365)  # Set the desired expiration time (1 year in this case)
                    for cookie in user.session.cookies:
                        cookie.expires = new_expiry.timestamp()
                        cookies_to_save.append({
                            'name': cookie.name,
                            'value': cookie.value,
                            'expires': cookie.expires,
                            'domain': cookie.domain,
                            'path': cookie.path,
                            'secure': cookie.secure,
                            'rest': cookie._rest,
                        })
                    # Save the cookies with extended expiration time and attributes using pickle
                    with open(f'{self._username}.pkl', 'wb') as pickle_file:
                        pickle.dump(cookies_to_save, pickle_file)

                except Exception as e:
                    logging.debug(e)
            page = context.new_page()
            page.goto(os.getenv("MY_URL"))


            """Logged on and Automation task On"""
            page.click("input.btn_green_white_innerfade")
            page.click('a[href="/db"]')
            
            
            # Find the input element and fill in a value
            input_selector = 'input.mat-input-element[formcontrolname="name"]'
            page.fill(input_selector, "AWP | Dragon Lore")

if __name__ == "__main__":
    # Create a Worker instance and run it
    worker = Worker("your_username", "your_password", "your_otp_code")
    worker.run()
