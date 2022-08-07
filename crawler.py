from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup

from datetime import datetime
from time import sleep, time
import json
import re

start_time = time()


class StreetBeat:
    url = 'https://street-beat.ru/cat/kids/?page=%s'
    product_list = []

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                                    {"source": "const newProto = navigator.__proto__;"
                                               "delete newProto.webdriver;"
                                               "navigator.__proto__ = newProto;"})
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride',
                                    {"userAgent": 'Mozilla/5.0 (X11; Linux x86_64) '
                                                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                  'Chrome/99.0.4844.51 Safari/537.36'})
        self.wait = WebDriverWait(self.driver, 10)

    def bypass_all_pages(self):
        """
        We find out the number of pages in the catalog and ask each.
        """
        link = 'https://street-beat.ru/cat/kids/'
        data = self.get_json_data(link)
        pages_count = data['catalog']['pagination']['lastPage']
        for i in range(1, pages_count + 1):
            print(f'parsing {i} page out of {pages_count}')
            self.parse_items(self.url % i)
            self.driver.quit()

    def parse_items(self, link):
        """
        We parse all links on the page.
        We parse the data that is in the api, the rest from the product card.
        :param link: link to current page.
        """
        data = self.get_json_data(link)
        items = data['catalog']['listing']['items']
        for item in items:
            url = 'https://street-beat.ru' + item['url']
            print(url)
            self.driver.get(url)
            sleep(3)
            self.wait.until(
               EC.presence_of_element_located((By.XPATH, '/html/body/article/div[1]/div')))
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            category = soup.find_all('a', {'class': 'breadcrumbs__link'})
            category1 = category[-4].text.strip()
            category2 = category[-3].text.strip()
            category3 = category[-2].text.strip()
            category4 = category[-1].text.strip()
            try:
                brand = soup.find("div", {"class": "tags-list"}).find_all('a')[2].text.replace("Другие товары", "").strip()
            except:
                brand = ''
            try:
                description = soup.find('div', {'class': 'tab__header'}).find('div', {'class': 'tab__description'}).text
            except:
                description = ''
            added = datetime.now().strftime("%Y-%m-%d %H:%M")
            updated = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.product_list.append({
                'SKU': item['id'], 'Vendor code': '', 'Name': item['title'], 'Brand': brand,
                'Category1': category1, 'Category2': category2, 'Category3': category3, 'Category4': category4,
                'Price old': item['price']['recommended']['price'],
                'Price': item['price']['special']['price'],
                'Price unit': item['price']['recommended']['currency'], 'Available': 'True', 'Added': added,
                'Updated': updated, 'Url': url, 'Image url': item['image']['main']['desktopX2'],
                'txtDescription': description
            })

    def get_json_data(self, link):
        """
        :param link: link to current page.
        :return: api data from the page in .json format.
        """
        self.driver.get(link)
        self.wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div')))
        data = re.search(r'__INITIAL_STATE__ \= JSON\.parse\(\'(.+)\'\);\n', self.driver.page_source).group(
            1).replace('\\', '')
        return json.loads(data)

    def save_data(self):
        """
        Save data from the product_list in .json format.
        :return:
        """
        with open('street-beat.json', 'w', encoding='utf-8') as file:
            json.dump(self.product_list, file, ensure_ascii=False, indent=3)


if __name__ == "__main__":
    sb = StreetBeat()
    sb.bypass_all_pages()
    sb.save_data()
    print(time() - start_time)
