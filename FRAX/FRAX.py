import selenium
from selenium import webdriver
from selenium.webdriver import ActionChains
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import contextlib


class TestFRAX():
    def initialize(self, executable_path='./chromedriver_102', url='https://www.sheffield.ac.uk/FRAX/tool.aspx?country=25'):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        self.driver = webdriver.Chrome(
            executable_path=executable_path, chrome_options=options)
        self.url = url
        self.vars = {}
        self.driver.get(url)

    def teardown_method(self):
        self.driver.quit()

    def calculate_frax(self,
                       pat_id: str,
                       age: int,
                       year: int,
                       month: int,
                       day: int,
                       female: bool,
                       wt: float,
                       ht: float,
                       previous_fracture: bool,
                       parent_fractured: bool,
                       smoking: bool,
                       glucocorticoid: bool,
                       rheumatoid: bool,
                       secondary: bool,
                       alcohol: bool,
                       femoral_method: str,
                       femoral_value: float):

        clear_and_send_keys = (
            ("ctl00_ContentPlaceHolder1_nameid", pat_id),
            ("ctl00_ContentPlaceHolder1_toolage", age),
            ("ctl00_ContentPlaceHolder1_year", year),
            ("ctl00_ContentPlaceHolder1_month", month),
            ("ctl00_ContentPlaceHolder1_day", day),
            ("ctl00_ContentPlaceHolder1_toolweight", wt),
            ("ctl00_ContentPlaceHolder1_ht", ht),
        )
        for element, value in clear_and_send_keys:
            self.driver.find_element(By.ID, element).clear()
            self.driver.find_element(By.ID, element).send_keys(value)

        click_button_keys = (
            ('ctl00_ContentPlaceHolder1_sex', female),
            ('ctl00_ContentPlaceHolder1_previousfracture', previous_fracture),
            ('ctl00_ContentPlaceHolder1_pfracturehip', parent_fractured),
            ('ctl00_ContentPlaceHolder1_currentsmoker', smoking),
            ('ctl00_ContentPlaceHolder1_glucocorticoids', glucocorticoid),
            ('ctl00_ContentPlaceHolder1_arthritis', rheumatoid),
            ('ctl00_ContentPlaceHolder1_osteoporosis', secondary),
            ('ctl00_ContentPlaceHolder1_alcohol', alcohol)
        )
        for element, value in click_button_keys:
            if value == True:
                self.driver.find_element(By.ID, f'{element}2').click()
            elif value == False:
                self.driver.find_element(By.ID, f'{element}1').click()

        dropdown = self.driver.find_element(By.ID, "dxa")
        dropdown.find_element(By.XPATH, "//option[. = 'Select BMD']").click()
        dropdown.find_element(
            By.XPATH, f"//option[. = '{femoral_method}']").click()
        with contextlib.suppress(Exception):
            self.driver.switch_to.alert
            self.driver.find_element(
                By.ID, "ctl00_ContentPlaceHolder1_bmd_input").send_keys(Keys.ENTER)

        self.driver.find_element(
            By.ID, "ctl00_ContentPlaceHolder1_bmd_input").clear()
        self.driver.find_element(
            By.ID, "ctl00_ContentPlaceHolder1_bmd_input").send_keys(femoral_value)
        time.sleep(0.5)
        self.driver.find_element(
            By.ID, "ctl00_ContentPlaceHolder1_btnCalculate").click()
        with contextlib.suppress(Exception):
            self.driver.switch_to.alert
            return None, self.driver.switch_to.alert.text
        self.driver.implicitly_wait(time_to_wait=5)

        osteo = self.driver.find_element(
            By.CSS_SELECTOR, ".result-box:nth-child(2) .result-score").text
        fracture = self.driver.find_element(
            By.CSS_SELECTOR, ".result-box:nth-child(3) .result-score").text
        return float(osteo), float(fracture)
