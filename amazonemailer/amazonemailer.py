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


class AmazonEmailer:
    
    def __init__(self):
        """Setting up private variables."""
        self._database_name = "./output/amazonBestSellers.db"
        self._config_name = "./amazonemailer_config.yaml"
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
                fileWriter = csv.writer(f)
                cursor.execute("""SELECT rank, name, reviewscore, price, asin, link, category, reviewers FROM items WHERE category = ? AND rank >= ? AND rank <= ? ORDER BY rank""", (str(categories[0][0]), int(self._range[0]), int(self._range[1])))
                result = cursor.fetchall()
                
                fileWriter.writerow(("BSR Rank", "Name", "Review Score", "Price", "ASIN", "Link", "Category", "# of Reviews"))
                for item in result:
                    fileWriter.writerow(item)
                
                
    def items_to_xls(self):
        """Writing the items information to an excel file with multiple sheets."""
        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()
        
        cursor.execute("""SELECT category FROM items GROUP BY category ORDER BY item_number""")
        categories = cursor.fetchall()
        
        if len(categories) > 0:
            book = tablib.Databook()

            for category in categories:
                cursor.execute("""SELECT rank, name, price, asin, link, category, reviewers FROM items WHERE category = ? AND rank >= ? AND rank <= ?ORDER BY rank""", (str(category[0]), int(self._range[0]), int(self._range[1])))
                items = cursor.fetchall()
                data = tablib.Dataset(title = category[0][-31:])
                data.headers = ["BSR Rank", "Name", "Price", "ASIN", "Link", "Item Category", "# of Reviews"]
                
                for item in items:
                    data.append(item)
                
                book.add_sheet(data)
                
            # Writing the items information to an excel file with multiple sheets
            makedirs(path.dirname(self._file_name), exist_ok=True)
            with open(self._file_name + ".xls", 'wb') as f:
                f.write(book.xls)
            
            
    def get_asin(self, address):
        """Strips the ASIN out of a url and returns in."""
        splitaddy = re.split('[/\?]+', address)
        asin = [elem for elem in splitaddy if re.match("[A-Z0-9]{10}", elem)]
        asin = " ".join(asin)  # In case there are false positives everything is returned.
        if len(asin) > 10:   print(asin)
        return asin
        
        
    def pull_items(self):
        """Pulls items down from amazon for the given pages."""
        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()
        
        for page in self._pages:
            r = requests.get(page)
            asoup = BeautifulSoup(r.text, 'lxml')
            items_list = asoup.find_all('li', class_="s-result-item")
            first_page_num = ceil(int(self._range[0]) / len(items_list))
            last_page_num = ceil(int(self._range[1]) / len(items_list))
            
            # Getting the category
            category_chain = asoup.find('h2', id="s-result-count").span.contents
            categorystr = ''
            for category in category_chain:
               categorystr += category.string
            categorystr = categorystr.replace(':', '>')
            
            # Fast forwarding to the first page in the range
            next_page = "https://www.amazon.com" + asoup.find('span', class_="pagnLink").contents[0]['href']
            first_valid_page = next_page.replace("page=2", "page={}".format(first_page_num))
            r = requests.get(first_valid_page)
            
            # Going through all the pages and getting their items.
            for page_num in range(first_page_num, last_page_num+1):
                asoup = BeautifulSoup(r.text, 'lxml')
                try:
                    next_page = "https://www.amazon.com" + asoup.find('a', id="pagnNextLink")['href']
                except TypeError:
                    print("Error: Range higher than number of items.")
                    print(categorystr)
                    break
                
                # zg_itemImmersion is the tag that contains all the data on an item.
                items = asoup.find_all('li', class_="s-result-item")
                
                # Scrapping the item information and adding it to the database.
                for item in items:
                    linkstr = item.find('a', class_="a-link-normal a-text-normal")['href']
                    namestr = item.find('h2').string
                    psbl_review_score = item.find('i', class_=re.compile("a-icon a-icon-star a-star-."))
                    reviewscorestr = psbl_review_score.string if psbl_review_score is not None else ""
                    psbl_num_reviewers_tag = item.find('a', class_="a-size-small a-link-normal a-text-normal")
                    if psbl_num_reviewers_tag and "#customerReviews" in psbl_num_reviewers_tag['href']:
                        reviewersstr = item.find('a', class_="a-size-small a-link-normal a-text-normal").string
                    else:
                        reviewersstr = '0'
                    whole = item.find('span', class_="sx-price-whole").string if item.find('span', class_="sx-price-whole") is not None else '00'
                    fract = item.find('sup', class_="sx-price-fractional").string if item.find('sup', class_="sx-price-fractional") is not None else '00'
                    pricestr = "{}.{}".format(whole, fract)
                    asinstr = item['data-asin']
                    rankstr = item['id'][len("result_"):]
                    
                    sql_command = """INSERT  OR IGNORE INTO items (item_number, category, name, reviewscore, price, link, rank, asin, reviewers)
                    VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?);"""
                    cursor.execute(sql_command, (categorystr, namestr, reviewscorestr, pricestr, linkstr, rankstr, asinstr, reviewersstr))

                connection.commit()
                time.sleep(1)
                r = requests.get(next_page)
        
        
    def pull_items_best_sellers(self):
        """Pulls items down from amazon for the given top 100 best sellers pages."""
        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()
        
        for page in self._pages:
            r = requests.get(page)
            first_page_num = ceil(int(self._range[0]) / 20)
            
            # Fast forwarding to the first page in the range
            for page_num in range(first_page_num):
                asoup = BeautifulSoup(r.text, 'lxml')
                next_page = asoup.find('a', page=str(page_num+1))['href']
                r = requests.get(next_page)
            
            # Going through all the pages and getting their items.
            for page_num in range(first_page_num, ceil(int(self._range[1]) / 20)+1):
                asoup = BeautifulSoup(r.text, 'lxml')
                next_page = asoup.find('a', page=str(page_num+1))['href']
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
                    cursor.execute(sql_command, (categorystr, namestr, reviewscorestr, pricestr, linkstr, rankstr, asinstr))

                connection.commit()
                r = requests.get(next_page)
            
            
    def write_config(self):
        """Takes the private functions and stores them out to a config file."""
        makedirs(path.dirname(self._config_name), exist_ok=True)
        
        email_address = self._email_address if self._email_address is not None else ''
        
        with open(self._config_name, 'w') as f:
            yaml.dump({'pages': ','.join(self._pages), 'email list': ','.join(self._email_list), 'range': ','.join(self._range), 'config name': self._config_name, 'database name': self._database_name, 'file name': self._file_name, 'email info': {'email address': email_address, 'email password': ''}, 'time': self._time, 'frequency': self._frequency}, f, default_flow_style=False)
        
        
    def read_config(self):
        """Reads in a config file and stores all the values in the private variables."""
        with open(self._config_name, 'r') as f:
            config_info = yaml.load(f)
        
        self._pages = config_info['pages'].split(',') if len(config_info['pages']) > 0 else []
        self._email_list = config_info['email list'].split(',') if len(config_info['email list']) > 0 else []
        self._range = config_info['range'].split(',') if len(config_info['range']) > 0 else self._range
        self._config_name = config_info['config name']
        self._database_name = config_info['database name']
        self._file_name = config_info['file name']
        self._email_address = config_info['email info']['email address'] if config_info['email info']['email address'] != '' else None
        self._email_password = config_info['email info']['email password']
        self._time = config_info['time']
        self._frequency = config_info['frequency']
        
        
    def setup_config(self, pages=None, email_list=None, range=None, config=None, database=None, file=None, email_address=None, email_password=None, time=None, frequency=None):
        """Get all available information from passed in config file."""
        self._pages = pages.split(',') if pages is not None else self._pages
        self._email_list = email_list.split(',') if email_list is not None else self._email_list
        self._range = range.split(',') if range is not None else self._range
        self._config_name = config if config is not None else self._config_name
        self._database_name = database if database is not None else self._database_name
        self._file_name = file if file is not None else self._file_name
        self._email_address = email_address if email_address is not None else self._email_address
        self._email_password = email_password if email_password is not None else self._email_password
        self._time = time if time is not None else self._time
        self._frequency = frequency if frequency is not None else self._frequency
        
        
    def send_email(self):
        """Sends output files to the emails in the list."""
        if self._email_address and keyring.get_password('yagmail', self._email_address) is None:
            self.store_email_info()
        
        try:
            with yagmail.SMTP(self._email_address) as yag:
                contents = ["Attached are the amazon items.",  "output/AmazonItems.csv", "output/AmazonItems.xls"]
                
                if len(self._email_list) > 0:
                    yag.send(to=self._email_list, subject="AmazonEmailer", contents=contents)
                    print("Email sent to " + ", ".join(self._email_list))
                else:
                    yag.send(subject="AmazonEmailer", contents=contents)
                    print("Email sent to " + self._email_address)
        except FileNotFoundError:
            print("Need gmail address to send emails from.")
            
            
    def store_email_info(self):
        """Stores email address and password in keyring."""
        yagmail.register(self._email_address, self._email_password)
        print("Email address and password stored to keyring.")
        