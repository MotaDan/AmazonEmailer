from bs4 import BeautifulSoup
import requests
import sqlite3
from os import remove, path, makedirs
import csv
import tablib
import re
import yagmail
import keyring
import yaml
from math import ceil
import time
from fake_useragent import UserAgent


class AmazonEmailer:
    def __init__(self):
        """Setting up private variables."""
        self._database_name = "./output/amazonBestSellers.db"
        self._config_name = "./amazonemailer_config.txt"
        self._email_list = ''
        self._pages = ''
        self._range = ['1', '60']
        self._file_name = "./output/AmazonItems"
        self._email_address = ''
        self._email_password = ''
        self._time = "9:00"
        self._frequency = "daily"

    def setup_database(self):
        """Setting up sqlite database for items."""
        makedirs(path.dirname(self._database_name), exist_ok=True)

        # Deleting the previous database to avoid duplicate entries. I don't care what items existed before.
        if path.isfile(self._database_name):
            remove(self._database_name)

        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()

        sql_command = """
        CREATE TABLE if not exists items ( 
        item_number INTEGER PRIMARY KEY, 
        category TEXT, 
        name TEXT, 
        reviewscore TEXT, 
        price FLOAT, 
        link TEXT, 
        rank INTEGER, 
        asin TEXT, 
        reviewers INTEGER, 
        unique (name, reviewScore, price, link, rank, asin));"""

        cursor.execute(sql_command)

    def items_to_csv(self):
        """Writing the items information to a csv file."""
        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()

        cursor.execute("""SELECT category FROM items GROUP BY category ORDER BY item_number""")
        categories = cursor.fetchall()

        makedirs(path.dirname(self._file_name), exist_ok=True)

        if len(categories) > 0:
            with open(self._file_name + ".csv", 'w', newline='') as f:
                file_writer = csv.writer(f)
                cursor.execute(
                    """SELECT rank, name, reviewscore, price, asin, link, category FROM items WHERE category = ? AND 
                    rank >= ? AND rank <= ? ORDER BY rank""",
                    (str(categories[0][0]), int(self._range[0]), int(self._range[1])))
                result = cursor.fetchall()

                file_writer.writerow(("BSR Rank", "Name", "Review Score", "Price", "ASIN", "Link", "Category"))
                for item in result:
                    file_writer.writerow(item)

    def items_to_xls(self):
        """Writing the items information to an excel file with multiple sheets."""
        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()

        cursor.execute("""SELECT category FROM items GROUP BY category ORDER BY item_number""")
        categories = cursor.fetchall()

        if len(categories) > 0:
            book = tablib.Databook()

            for category in categories:
                cursor.execute(
                    """SELECT rank, name, price, asin, link, category FROM items WHERE category = ? AND rank >= ? AND 
                    rank <= ?ORDER BY rank""",
                    (str(category[0]), int(self._range[0]), int(self._range[1])))
                items = cursor.fetchall()
                data = tablib.Dataset(title=category[0][-31:])
                data.headers = ["BSR Rank", "Name", "Price", "ASIN", "Link", "Item Category"]

                for item in items:
                    data.append(item)

                book.add_sheet(data)

            # Writing the items information to an excel file with multiple sheets
            makedirs(path.dirname(self._file_name), exist_ok=True)
            with open(self._file_name + ".xls", 'wb') as f:
                f.write(book.xls)

    @staticmethod
    def get_asin(address):
        """Strips the ASIN out of a url and returns in."""
        splitaddy = re.split('[/?]+', address)
        asin = [elem for elem in splitaddy if re.match("[A-Z0-9]{10}", elem)]
        asin = " ".join(asin)  # In case there are false positives everything is returned.
        if len(asin) > 10:
            print(asin)
        return asin

    def pull_individual_item(self):
        """Pulls item information down for a single item."""
        pass

    def pull_items_search(self):
        """Pulls items down from amazon for the given pages."""
        print("Retrieving Items...")

        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()
        ua = UserAgent()
        ua.update()
        
        for page in self._pages:
            headers = {'User-Agent': '{}'.format(ua.random)}
            r = requests.get(page, headers=headers)
            asoup = BeautifulSoup(r.text, 'lxml')

            if asoup.head.title.string != "Robot Check":
                print("You've been discovered as a bot. Take a break and come back tomorrow.")
                return 'bot'

            items_list = asoup.find_all('li', class_="s-result-item")
            
            if len(items_list) > 0:
                first_page_num = int(ceil(int(self._range[0]) / len(items_list)))
                last_page_num = int(ceil(int(self._range[1]) / len(items_list)))
            else:
                print("No items found.")
                with open("./output/no_items.html", 'w') as f:
                    f.write(asoup.prettify())
                    print("Item less html written to ./output/no_items.html")
                break

            # Getting the category
            category_chain = asoup.find('h2', id="s-result-count").span.contents
            categorystr = ''
            for category in category_chain:
                if category.string is not None:
                    categorystr += category.string
            categorystr = categorystr.replace(':', '-')
            print(categorystr)

            # Fast forwarding to the first page in the range
            next_page = "https://www.amazon.com" + asoup.find('span', class_="pagnLink").contents[0]['href']
            first_valid_page = next_page.replace("page=2", "page={}".format(first_page_num))
            r = requests.get(first_valid_page)

            # Going through all the pages and getting their items.
            for page_num in range(first_page_num, last_page_num + 1):
                asoup = BeautifulSoup(r.text, 'lxml')

                # zg_itemImmersion is the tag that contains all the data on an item.
                items = asoup.find_all('li', class_="s-result-item")

                # Scrapping the item information and adding it to the database.
                for item in items:
                    linkstr = item.find('a', class_="a-link-normal a-text-normal")['href']
                    namestr = item.find('h2').string

                    reviewscorestr = ''
                    if item.find('i', class_=re.compile("a-icon a-icon-star a-star-.")) is not None:
                        reviewscorestr = item.find('i', class_=re.compile("a-icon a-icon-star a-star-.")).string
                    
                    reviewersstr = '0'
                    psbl_num_reviewers_tag = item.find('a', class_="a-size-small a-link-normal a-text-normal")
                    if psbl_num_reviewers_tag and "#customerReviews" in psbl_num_reviewers_tag['href']:
                        reviewersstr = item.find('a', class_="a-size-small a-link-normal a-text-normal").string

                    pricestr = '0.00'
                    # The price is broken up into a whole section and fractional section.
                    if item.find('span', class_="sx-price-whole") is not None and item.find('sup', class_="sx-price-fractional") is not None:
                        whole = item.find('span', class_="sx-price-whole").string
                        fract = item.find('sup', class_="sx-price-fractional").string
                        pricestr = "{}.{}".format(whole, fract)
                    # The price is just its own full string value.
                    elif pricestr == '0.00' and item.find('span', class_="a-size-small s-padding-right-micro") is not None:
                        pricestr = item.find('span', class_="a-size-small s-padding-right-micro").string 

                    asinstr = item['data-asin']
                    rankstr = item['id'][len("result_"):]

                    sql_command = """INSERT  OR IGNORE INTO items (item_number, category, name, reviewscore, price, link, rank, asin, reviewers)
                    VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?);"""
                    cursor.execute(sql_command, (
                        categorystr, namestr, reviewscorestr, pricestr, linkstr, rankstr, asinstr, reviewersstr))

                connection.commit()

                try:
                    next_page = "https://www.amazon.com" + asoup.find('a', id="pagnNextLink")['href']
                except TypeError:
                    if asoup.head.title.string != "Robot Check":
                        print("Error: No more pages, range higher than number of items.")
                        with open("./output/failed_{}.html".format(categorystr.replace(" ", "")), 'w') as f:
                            f.write(asoup.prettify())
                            print("Failed html written to ./output/failed_{}.html".format(categorystr.replace(" ", "")))
                    else:
                        print("You've been discovered as a bot. Take a break and come back tomorrow.")
                        return 'bot'
                    
                    break
                
                if page_num != last_page_num:
                    time.sleep(5)
                    r = requests.get(next_page)

            if page is not self._pages[-1]:
                time.sleep(45)

    def pull_items_best_sellers(self):
        """Pulls items down from amazon for the given top 100 best sellers pages."""
        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()

        for page in self._pages:
            r = requests.get(page)
            first_page_num = int(ceil(int(self._range[0]) / 20))

            # Fast forwarding to the first page in the range
            for page_num in range(first_page_num):
                asoup = BeautifulSoup(r.text, 'lxml')
                next_page = asoup.find('a', page=str(page_num + 1))['href']
                r = requests.get(next_page)

            # Going through all the pages and getting their items.
            for page_num in range(first_page_num, int(ceil(int(self._range[1]) / 20)) + 1):
                asoup = BeautifulSoup(r.text, 'lxml')
                next_page = asoup.find('a', page=str(page_num + 1))['href']
                categorystr = asoup.find('span', class_="category").string

                # zg_itemImmersion is the tag that contains all the data on an item.
                items = asoup.find_all('div', class_="zg_itemImmersion")

                # Scrapping the item information and adding it to the database.
                for item in items:
                    wrapper = item.find('div', class_='zg_itemWrapper')
                    links = wrapper.find_all('a')
                    namestr = links[0].find_all('div')[1].string.strip()
                    reviewscorestr = links[1]['title'] if len(links) > 1 else ""
                    pricestr = ""
                    if wrapper.find(class_="a-size-base a-color-price") is not None:
                        pricestr = wrapper.find(class_="a-size-base a-color-price").string.lstrip('$')
                    linkstr = "https://www.amazon.com" + wrapper.find('a')['href']
                    asinstr = self.get_asin(linkstr)
                    rankstr = item.find('span', class_='zg_rankNumber').string.strip().rstrip('.')

                    sql_command = """INSERT  OR IGNORE INTO items (item_number, category, name, reviewscore, price, link, rank, asin)
                    VALUES (NULL, ?, ?, ?, ?, ?, ?, ?);"""
                    cursor.execute(sql_command,
                                   (categorystr, namestr, reviewscorestr, pricestr, linkstr, rankstr, asinstr))

                connection.commit()
                r = requests.get(next_page)

    def write_config(self):
        """Takes the private functions and stores them out to a config file."""
        makedirs(path.dirname(self._config_name), exist_ok=True)

        email_address = self._email_address if self._email_address is not None else ''

        with open(self._config_name, 'w') as f:
            yaml.dump({'pages': ', '.join(self._pages),
                       'email list': ', '.join(self._email_list),
                       'range': ', '.join(self._range),
                       'config name': self._config_name,
                       'database name': self._database_name,
                       'file name': self._file_name,
                       'email info': {'email address': email_address, 'email password': ''},
                       'time': self._time,
                       'frequency': self._frequency}, f, default_flow_style=False)

    def read_config(self):
        """Reads in a config file and stores all the values in the private variables."""
        with open(self._config_name, 'r') as f:
            config_info = yaml.load(f)

        try:
            self.setup_config(pages=config_info['pages'],
                              email_list=config_info['email list'],
                              items_range=config_info['range'],
                              config=config_info['config name'],
                              database=config_info['database name'],
                              file=config_info['file name'],
                              email_address=config_info['email info']['email address'],
                              email_password=config_info['email info']['email password'],
                              send_time=config_info['time'],
                              frequency=config_info['frequency'])
        except KeyError as e:
            print("Incomplete config file.")
            print(e)

    def setup_config(self, pages=None, email_list=None, items_range=None, config=None, database=None, file=None,
                     email_address=None, email_password=None, send_time=None, frequency=None):
        """Get all available information from passed in config file."""
        self._pages = pages.replace(' ', '').split(',') if pages is not None and len(pages) > 0 else self._pages
        self._email_list = email_list.replace(' ', '').split(',') if email_list is not None and len(email_list) > 0 else self._email_list
        self._range = items_range.replace(' ', '').split(',') if items_range is not None and re.search("[0-9]+,\s?[0-9]+", items_range) is not None else self._range
        self._config_name = config if config is not None else self._config_name
        self._database_name = database if database is not None else self._database_name
        self._file_name = file if file is not None else self._file_name
        self._email_address = email_address if email_address is not None else self._email_address
        self._email_password = email_password if email_password is not None else self._email_password
        self._time = send_time if send_time is not None else self._time
        self._frequency = frequency if frequency is not None else self._frequency

    def send_email(self):
        """Sends output files to the emails in the list."""
        email_address = self._email_address if self._email_address != '' else None

        if self._email_password != '':
            self.store_email_info()

        try:
            with yagmail.SMTP(email_address) as yag:
                contents = ["Attached are the amazon items.", "output/AmazonItems.xls"]

                if len(self._email_list) > 0:
                    yag.send(to=self._email_list, subject="AmazonEmailer", contents=contents)
                    print("Email sent to " + ", ".join(self._email_list))
                else:
                    yag.send(subject="AmazonEmailer", contents=contents)
                    print("Email sent to " + email_address)
        except FileNotFoundError:
            print("Need gmail address to send emails from.")

    def store_email_info(self):
        """Stores email address and password in keyring."""
        yagmail.register(self._email_address, self._email_password)
        print("Email address and password stored to keyring.")

    @property
    def frequency(self):
        return self._frequency

    @property
    def time(self):
        return self._time
