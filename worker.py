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
            page.set_viewport_size({"width": 1600, "height": 1200})
            print(os.getenv("MY_URL"))
            page.goto("https://steamcommunity.com/openid/login?openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select&openid.identity=http://specs.openid.net/auth/2.0/identifier_select&openid.mode=checkid_setup&openid.ns=http://specs.openid.net/auth/2.0&openid.realm=https://csfloat.app&openid.return_to=https://csfloat.app/return")


            """Logged on and Automation task On"""
            page.click("input.btn_green_white_innerfade")
            page.wait_for_selector("span:has-text('Successfully logged into CSFloat')",timeout=200000)

            page.wait_for_selector('a[href="/db"]', timeout=200000)

            page.click('a[href="/db"]')
            
            page.wait_for_selector('input.mat-input-element[formcontrolname="name"]', timeout=200000)
            # Find the input element and fill in a value
            input_selector = 'input.mat-input-element[formcontrolname="name"]'
            page.fill(input_selector, "Karambit")
            page.keyboard.press("Enter")


            page.fill('input[formcontrolname="maxAge"]',str(7))
            page.click("span.button-text")


            filter_items = """let intervalId; // Declare a variable to hold the interval ID
            function extractSteamIdFromUrl(url) {
            const matches = url.match(/profiles\/(\d+)/);
            if (matches && matches.length > 1) {
                return matches[1];
            }
            return null;
            }
            function autoScrollPage() {
            const rowsWithHistory = document.querySelectorAll('tr[role="row"]');
            
            
            const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
            const scrollAmount = vh * 20; // Scroll down by 1% of the viewport height
            
            const number_items = document.querySelectorAll('td.mat-cell.cdk-cell.cdk-column-rank.mat-column-rank.ng-star-inserted');
            const lastNumberItems = number_items.length - 1;
            const total =   number_items[lastNumberItems].innerHTML.match(/\d+/g).map(Number);
            
            const count_numbers = document.getElementsByClassName('mat-card mat-focus-indicator count ng-star-inserted')[0].innerText.match(/\d+/g).map(Number).join('');
            if (parseInt(count_numbers) === parseInt(total[0])) {
                clearInterval(intervalId); // Clear the interval when the condition is met
                const rowsArray = Array.from(rowsWithHistory);
                rowsArray.forEach((row) => {
                const userprofile = row.querySelector('a.playerAvatar.online');
                if(userprofile){
                    const href = userprofile.getAttribute('href');
                    if (href.startsWith("https://steamcommunity.com/profiles/") && href.includes("/inventory")) {
                    const steamId = extractSteamIdFromUrl(href);
            
                    if (steamId) {
                        fetch(`http://localhost:8000/api?url=${steamId}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data !== null) {  // Check if data is not null
                            const steamProfileUrl = `https://steamcommunity.com/profiles/${data.steam_id}`;
                            console.log(steamProfileUrl);
                            }
                        })
                    }
                    }
                }
                });


            } else {
                window.scrollBy(0, scrollAmount); // Scroll down if the condition is not met
                console.log("Scrolling down");
            }
            // Convert the NodeList to an array
            const rowsArray = Array.from(rowsWithHistory);
            
            // Remove rows containing the word "history"
            rowsArray.forEach((row) => {
                if (row.innerText.includes('history')) {
                row.remove();
                }
                
                const linkElement = row.querySelector('a.playerAvatar.offline');
                    if (linkElement) {
                        // Remove the parent element of linkElement
                        row.remove();
                }
            
            
            });
            
            }
            
            // Call the autoScrollPage function every 5 seconds
            intervalId = setInterval(autoScrollPage, 5000);"""
            page.evaluate(filter_items)
     
