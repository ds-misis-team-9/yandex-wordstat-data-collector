import argparse
import datetime
import urllib
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from transliterate import translit
from webdriver_manager.chrome import ChromeDriverManager

YANDEX_WORDSTAT_URL = 'https://wordstat.yandex.com'
YANDEX_WORDSTAT_HISTORY_URL = f'{YANDEX_WORDSTAT_URL}/#!/history?period=weekly&regions=225&words='
OUTPUT_DATA_FOLDER = 'downloaded_data'
SHORT_TIMEOUT = 5
LONG_TIMEOUT = 180
HEADER_COLUMN_NAMES = ['search_query', 'period_start', 'period_end', 'absolute_value']
DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"

LOGIN_XPATH = "//td[@class='b-head-userinfo__entry']/a/span"
USERNAME_XPATH = "//div[@class='b-domik__username']/span/span/input"
PASSWORD_XPATH = "//div[@class='b-domik__password']/span/span/input"
SUBMIT_XPATH = "//div[@class='b-domik__button']/span"
SEARCH_RESULTS_TABLE_XPATH = "//div[@class='b-history__table-box']"
CAPTCHA_INPUT_XPATH = "//td[@class='b-page__captcha-input-td']/span/span/input"
SEARCH_INPUT_XPATH = "//td[@class='b-search__col b-search__input']/span"

request_words = ['потеря обоняния', 'симптомы короновируса', 'Анализы на короновирус', 'Признаки короновируса',
                 'КТ легких', 'Регламент лечения короновирусной инфекции', 'Схемы лечения препаратами короновируса',
                 'Показания для госпитализации с подозрением на коронавирусную болезнь',
                 'Купить противовирусные препараты (Фавипиравир, Ремдесивир)', 'Купить Гидроксихлорохин',
                 'Купить амоксициллин, азитромицин, левофлоксацин, моксифлоксацин', 'Купить антикоагулянты для лечения',
                 'Как защититься от короновируса', 'КОВИД-19', 'потеря вкуса', 'кашель', 'поражение сосудистой стенки',
                 'оксигенация', 'дыхательная функция', 'сатурация', 'пандемия', 'респираторная вирусная инфекция',
                 'SARS-Cov-2', 'пневмония', 'дыхательная недостаточность', 'насморк', 'мышечная слабость',
                 'высокая температура', 'озноб', 'рисунок матовое стекло', 'одышка', 'бессонница',
                 'положительный результат теста на ПЦР', 'наличие антител М', 'наличие антител G', 'Коронавир',
                 'Парацетомол', 'Дексаметазон', 'Уровень кислорода в крови', 'Кислород в крови', 'Вакцинация',
                 'Спутник V', 'иммунитет', 'АстраЗенека', 'Pfizer', 'побочные эффекты', 'осложенния',
                 'противопоказания', 'тромбоз', 'ЭпиВакКорона', 'КовиВак', 'инкубационный период', 'вирулентность',
                 'мутации', 'Британский штамм', 'маска', 'перчатки', 'срок жизни вируса на поверхности', 'профилактика',
                 'антитела g короновирус ковид -19', 'антитела к ковиду показатели', 'вакцина гам ковид вак',
                 'вакцина гам ковид вак и спутник м это одно и тоже или нет', 'вакцины от ковида',
                 'гам ковид вак или спутник м', 'гам-ковид-вак', 'гам-ковид-вак и спутник одно и тоже', 'ковид',
                 'ковид статистика россия', 'прививка от ковид -19 спутник инструкция противопоказания',
                 'прививки от ковида', 'регистр ковид']


def site_login(driver, login, password):
    driver.implicitly_wait(1)
    driver.get(YANDEX_WORDSTAT_URL)
    login_element = driver.find_element(By.XPATH, LOGIN_XPATH)
    login_element.click()

    username_input = driver.find_element(By.XPATH, USERNAME_XPATH)
    password_input = driver.find_element(By.XPATH, PASSWORD_XPATH)
    submit_span = driver.find_element(By.XPATH, SUBMIT_XPATH)

    username_input.send_keys(login)
    password_input.send_keys(password)

    submit_span.click()


def is_captcha_visible(driver):
    try:
        captcha_input = WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.XPATH, CAPTCHA_INPUT_XPATH)))
        return captcha_input.is_displayed()
    except TimeoutException:
        return False


def solve_captcha(driver):
    driver.switch_to.window(driver.current_window_handle)

    try:
        WebDriverWait(driver, SHORT_TIMEOUT).until(EC.visibility_of_element_located((By.XPATH, CAPTCHA_INPUT_XPATH)))
        WebDriverWait(driver, LONG_TIMEOUT).until_not(EC.visibility_of_element_located((By.XPATH, CAPTCHA_INPUT_XPATH)))
    except TimeoutException:
        pass


def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    trs = soup.find_all('tr', {"class": ["odd", "even"]})
    rows = []
    for tr in trs:
        td_iterator = tr.findChildren("td", recursive=False)
        f1, f2 = td_iterator[0].text.replace(u'\xa0', ' ').replace(' ', '').split('-')
        f3 = td_iterator[2].text
        rows.append((f1, f2, f3))

    return rows


def check_for_captcha_and_solve_it(driver):
    search_span = driver.find_element(By.XPATH, SEARCH_INPUT_XPATH)

    try:
        search_span.click()
    except ElementClickInterceptedException:
        while is_captcha_visible(driver):
            solve_captcha(driver)

    search_span_clickable = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, SEARCH_INPUT_XPATH)))
    search_span_clickable.click()


def write_csv_file(search_query_words, data_rows, path, divisor='|'):
    f_name = translit(search_query_words, 'ru', reversed=True).replace(' ', '_')
    file_full_path = f"{path}/{f_name}.csv"
    with open(file_full_path, 'w') as f:
        f.write(f"{divisor.join(HEADER_COLUMN_NAMES)}\n")
        for row in data_rows:
            f.write(f"{divisor.join([search_query_words, row[0], row[1], row[2]])}\n")


def try_and_parse_data(driver):
    try:
        stats_table = driver.find_element(By.XPATH, SEARCH_RESULTS_TABLE_XPATH)
        stats_table_visible = WebDriverWait(driver, 10).until(
            EC.visibility_of(stats_table)
        )

        return stats_table_visible.get_attribute('innerHTML')
    except NoSuchElementException:
        # nothing found
        return None


def parse_and_write_to_file(search_query_words, table_html, path):
    data_rows = parse_html(table_html)
    write_csv_file(search_query_words, data_rows, path)


def parse_content_by_url(driver, search_query_words, path):
    encoded_words = urllib.parse.quote(search_query_words.encode('utf-8'))
    url = YANDEX_WORDSTAT_HISTORY_URL + encoded_words
    driver.get(url)

    check_for_captcha_and_solve_it(driver)

    data = try_and_parse_data(driver)
    if data:
        parse_and_write_to_file(search_query_words, data, path)


def create_download_folder_if_not_exists(path, create_subfolder):
    Path(path).mkdir(parents=True, exist_ok=True)
    if create_subfolder:
        t = datetime.datetime.now()
        subfolder_name = t.strftime(DATE_FORMAT)
        final_path = f"{path}/{subfolder_name}"
        Path(final_path).mkdir()

        return final_path


def parse_arguments():
    parser = argparse.ArgumentParser(description='Parse yandex wordstat for query results')
    parser.add_argument('username', type=str, nargs=1,
                        help='username to authenticate with yandex')
    parser.add_argument('password', type=str, nargs=1,
                        help='password to authenticate with yandex')

    args = parser.parse_args()
    return args.username[0], args.password[0]


def main():
    yandex_login, yandex_password = parse_arguments()
    output_data_path = create_download_folder_if_not_exists(OUTPUT_DATA_FOLDER, True)
    with webdriver.Chrome(ChromeDriverManager().install()) as driver:
        site_login(driver, yandex_login, yandex_password)
        for word in request_words:
            parse_content_by_url(driver, word, output_data_path)


if __name__ == '__main__':
    main()
