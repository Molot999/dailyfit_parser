from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import dbconnection as db

def get_urls(end_page, start_page=1):
    driver = webdriver.Chrome()
    # Установить неявное ожидание загрузки элементов
    driver.implicitly_wait(3)
    url_base = 'http://dailyfit.ru/katalog-uprazhnenij/?pg='
    urls = []
    for page_num in range(start_page, end_page+1):
        try:
            driver.get(f'{url_base}{page_num}')
            # Приостановить загрузку страницы после 5 секунд
            time.sleep(5)
            # Выполнить JavaScript, чтобы прервать загрузку страницы
            driver.execute_script("window.stop();")
            # Найти элементы на странице по CSS-селектору
            element = driver.find_element(By.CLASS_NAME, 'ui.two.stackable.cards')
            print('element', element)
            elements = element.find_elements(By.CLASS_NAME, 'ui.fluid.card')
            print('elements len = ', len(elements))
            for el in elements:
                img_el = el.find_element(By.CLASS_NAME, 'ui.image')
                href = img_el.get_attribute('href')
                urls.append(href)
        except Exception as e:
            print('Ошибка!', e)
            continue
    # Открыть файл для записи
    with open("urls.txt", "w", encoding='utf8') as file:
        # Записать каждую строку в файл
        for url in urls:
            file.write(url + '\n')

def add_exercise_data(url_list):
    from selenium.webdriver.chrome.options import Options
    # Создание объекта настроек Chrome
    chrome_options = Options()
    # Отключение проверки SSL-сертификата
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.set_capability('pageLoadStrategy', "none")
    driver = webdriver.Chrome(chrome_options)
    for url in url_list:
        try:
            driver.get(url)
            time.sleep(2)
            # Получаем название и параметры
            exercise_data_block = driver.find_element(By.CLASS_NAME, 'ui.clearing.segment')
            title = exercise_data_block.find_element(By.CLASS_NAME, 'ui.header').text
            elem = exercise_data_block.find_element(By.CLASS_NAME, 'ui.stackable.grid')
            ex_info_column = elem.find_element(By.CLASS_NAME, 'ten.wide.column')
            ex_info_table = ex_info_column.find_element(By.CLASS_NAME, 'ui.bulleted.list')
            ex_infos = ex_info_table.find_elements(By.CLASS_NAME, 'item')
            ex_infos_dict = {}
            for info in ex_infos:
                info_text = info.text
                info_text = info_text.split(':')
                name = info_text[0].strip()
                value = info_text[1].strip()
                ex_infos_dict[name] = value

            exercise_id = add_exercise_to_db(title, ex_infos_dict, url)
            
            with open('urls_done.txt', 'a', encoding='UTF-8') as f:
                f.write(url + '\n')

            # Получаем фото для М
            male_block = driver.find_element(By.CSS_SELECTOR, 'div.ui.tab[data-tab="male"]')

            male_photo_links = male_block.find_elements(By.TAG_NAME, 'a')

            # Итерируйтесь по найденным элементам и получайте их атрибут `href`
            for link in male_photo_links:
                href = link.get_attribute('href')
                db.add_available_exercise_photo(exercise_id, href, 'male')

            # Получаем фото для Ж
            female_block = driver.find_element(By.CSS_SELECTOR, 'div.ui.tab[data-tab="female"]')

            female_photo_links = female_block.find_elements(By.TAG_NAME, 'a')

            # Итерируйтесь по найденным элементам и получайте их атрибут `href`
            for link in female_photo_links:
                href = link.get_attribute('href')
                db.add_available_exercise_photo(exercise_id, href, 'female')

        except Exception as e:
            print('Ошибка! get_exercise_data() -> url:', url, e)
            continue
        
    driver.quit()

def add_exercise_to_db(title:str, ex_infos_dict:dict, url:str):
    muscle_group = ex_infos_dict.get('Группа мышц')
    additional_muscles = ex_infos_dict.get('Дополнительные мышцы')
    ex_type = ex_infos_dict.get('Тип упражнения')
    ex_kind = ex_infos_dict.get('Вид упражнения')
    equipment = ex_infos_dict.get('Оборудование')
    difficulty_level = ex_infos_dict.get('Уровень сложности')
    return db.add_available_exercise(
        title,
        muscle_group,
        additional_muscles,
        ex_type,
        ex_kind,
        equipment,
        difficulty_level,
        url
    )

if __name__ == '__main__':
    # Чтение файла с обработанными ссылками
    with open('urls_done.txt', 'r') as f:
        urls_done = set(f.read().splitlines())

    # Чтение файла со всеми ссылками
    with open('urls.txt', 'r') as f:
        urls = set(f.read().splitlines())

    # Получение списка необработанных ссылок
    urls = urls - urls_done
    add_exercise_data(urls)