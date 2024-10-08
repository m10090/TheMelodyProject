import undetected_chromedriver as uc
import requests
import asyncio

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from GlobalVariable import (
    CF_PASSWORD,
    CF_USERNAME,
    logger
)


jsessionid = ""

async def get_max_rate(handle: str) -> int:
    # Codeforces API endpoint for rating history
    url = f"https://codeforces.com/api/user.rating?handle={handle}"

    try:
        # Make a request to the Codeforces API
        response = requests.get(url)
        data = response.json()

        # Check if the request was successful
        if data["status"] == "OK":
            # Extract rating changes
            rating_changes = data["result"]
            if not rating_changes:
                return 0

            max_rating = max(change["newRating"] for change in rating_changes)
            return max_rating

    except BaseException as e:
        logger.error(e)
    return -1


#######################################################################################################

LOGIN_URL = "https://codeforces.com/enter"
TALK_URL = "https://codeforces.com/usertalk/with/"

options = uc.ChromeOptions()
options.headless = False
_driver = uc.Chrome(options=options)


async def check_login(driver=_driver) -> bool:
    try:
        await asyncio.sleep(2)
        driver.get(LOGIN_URL)
        await asyncio.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        if "Logout" in soup.get_text():
            return True
        driver.delete_cookie('JSESSIONID')
        await asyncio.sleep(1)
        driver.add_cookie({'name': 'JSESSIONID', 'value': jsessionid, 'domain': 'codeforces.com'})
        await asyncio.sleep(1)
        driver.refresh()
        await asyncio.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        if "Logout" in soup.get_text():
            return True
        else:
            return False
    except Exception as e:
        logger.error(e)
        return False


async def ensure_login(driver=_driver) -> bool:
    # Start a Chrome session with undetected-chromedriver

    if await check_login(driver):
        logger.info("Already logged in!")
        return True
    try:
        driver.get(LOGIN_URL)
        # Wait for the username field to be present
        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "handleOrEmail"))
        )
        username.click()
        username.send_keys(CF_USERNAME)
        password = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password.click()
        password.send_keys(CF_PASSWORD)

        remember = driver.find_element(By.ID, "remember")
        remember.click()

        login_button = driver.find_element(By.CLASS_NAME, "submit")
        login_button.click()

        await asyncio.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        if "Logout" in soup.get_text() or ".Melody" in soup.get_text():
            global jsessionid
            jsessionid = driver.get_cookie('JSESSIONID')
            logger.info("Login successful!")
            return True
        else:
            logger.info("Login failed or not detected properly.")
            return False
        await asyncio.sleep(2)

    except Exception as e:
        logger.info(f"An error occurred: {e}")
        return False

    finally:
        # driver.quit() # this is reda's fulat
        pass


# Check for the code on Codeforces user talk page
async def check_code_on_codeforces(
        handle: str, code: str
) -> bool:
    driver = _driver
    url = TALK_URL + handle
    timeout = 120  # 2 minute
    driver.get(url)
    await asyncio.sleep(20)
    for _ in range(timeout // 5):  # max 2 minute
        driver.refresh()
        soup = BeautifulSoup(driver.page_source, "html.parser")
        if code in soup.get_text():
            return True
        await asyncio.sleep(5)  # Wait 10 seconds before checking again

    return False
