import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def yandex_login(login, password):
    try:
        with webdriver.Chrome(ChromeDriverManager().install()) as driver:
            driver.get('https://wordstat.yandex.ru/')

            sign_in = driver.find_element(By.XPATH, '//span[text()="Войти"]')
            sign_in.click()

            username = driver.find_elements_by_class_name('b-domik__username')
            print('a')
            username.click()
            # driver.implicitly_wait(15)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        print('Login Failed')


def old():
    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.get(r'https://accounts.google.com/signin/v2/identifier?continue=' + \
                   'https%3A%2F%2Fmail.google.com%2Fmail%2F&service=mail&sacu=1&rip=1' + \
                   '&flowName=GlifWebSignIn&flowEntry = ServiceLogin')
        driver.implicitly_wait(15)

        loginBox = driver.find_element_by_xpath('//*[@id ="identifierId"]')
        loginBox.send_keys("login")

        nextButton = driver.find_elements_by_xpath('//*[@id ="identifierNext"]')
        nextButton[0].click()

        passWordBox = driver.find_element_by_xpath(
            '//*[@id ="password"]/div[1]/div / div[1]/input')
        passWordBox.send_keys("password")

        nextButton = driver.find_elements_by_xpath('//*[@id ="passwordNext"]')
        nextButton[0].click()

        print('Login Successful...!!')
    except:
        print('Login Failed')


if __name__ == '__main__':
    yandex_login('a', 'b')
