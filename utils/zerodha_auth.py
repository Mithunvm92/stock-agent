import os
import time
import pyotp

from kiteconnect import KiteConnect

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager


class ZerodhaAuth:

    def __init__(self):

        self.api_key = os.getenv(
            "ZERODHA_API_KEY"
        )

        self.api_secret = os.getenv(
            "ZERODHA_API_SECRET"
        )

        self.user_id = os.getenv(
            "ZERODHA_USER_ID"
        )

        self.password = os.getenv(
            "ZERODHA_PASSWORD"
        )

        self.totp_secret = os.getenv(
            "ZERODHA_TOTP_SECRET"
        )

        self.kite = KiteConnect(
            api_key=self.api_key
        )

    def generate_access_token(self):

        login_url = self.kite.login_url()

        options = webdriver.ChromeOptions()

        options.add_argument("--headless")

        driver = webdriver.Chrome(
            service=Service(
                ChromeDriverManager().install()
            ),
            options=options
        )

        driver.get(login_url)

        time.sleep(3)

        # USER ID
        driver.find_element(
            By.XPATH,
            '//input[@type=\"text\"]'
        ).send_keys(self.user_id)

        # PASSWORD
        driver.find_element(
            By.XPATH,
            '//input[@type=\"password\"]'
        ).send_keys(self.password)

        driver.find_element(
            By.XPATH,
            '//button[@type=\"submit\"]'
        ).click()

        time.sleep(3)

        # TOTP
        otp = pyotp.TOTP(
            self.totp_secret
        ).now()

        driver.find_element(
            By.XPATH,
            '//input[@type=\"text\"]'
        ).send_keys(otp)

        driver.find_element(
            By.XPATH,
            '//button[@type=\"submit\"]'
        ).click()

        time.sleep(5)

        current_url = driver.current_url

        driver.quit()

        request_token = current_url.split(
            'request_token='
        )[1].split('&')[0]

        session = self.kite.generate_session(
            request_token,
            api_secret=self.api_secret
        )

        access_token = session['access_token']

        print(f\"✅ Access Token Generated\")

        return access_token
