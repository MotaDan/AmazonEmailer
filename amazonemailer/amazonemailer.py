from bs4 import BeautifulSoup
import requests
import sqlite3
from os import remove, path, makedirs
import csv
import tablib
import re
import yagmail
import yaml
from math import ceil


class AmazonEmailer:
    
    def __init__(self):
        """Setting up private variables."""
        self._database_name = "output/amazonBestSellers.db"
        self._config_name = "./amzonemailer_config.yaml"
        self._email_list = ''
        self._pages = ''
        self._range = ''
        self._file_name = ''
        self._email_address = ''
        self._email_password = ''
    

    def setup_database(self, database_name=""):
        """Setting up sqlite database for items."""
        if database_name != "":
            self._database_name = database_name
            
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
        unique (name, reviewScore, price, link, rank, asin));"""

        cursor.execute(sql_command)
        
        
    def items_to_csv(self, file_name="output/AmazonItems.csv"):
        """Writing the items information to a csv file."""
        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()
        
        makedirs(path.dirname(file_name), exist_ok=True)
        with open(file_name, 'w', newline='') as f:
            fileWriter = csv.writer(f)
            cursor.execute("""SELECT rank, name, reviewscore, price, asin, link FROM items WHERE category = 'Cell Phones & Accessories' AND rank >= ? ORDER BY rank""", (int(self._range[0]),))
            result = cursor.fetchall()
            
            fileWriter.writerow(("Rank", "Name", "Review Score", "Price", "ASIN", "Link"))
            for item in result:
                fileWriter.writerow(item)
                
                
    def items_to_xls(self, file_name="output/AmazonItems.xls"):
        """Writing the items information to an excel file with multiple sheets."""
        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()
        
        cursor.execute("""SELECT category FROM items GROUP BY category ORDER BY item_number""")
        categories = cursor.fetchall()

        if len(categories) > 0:
            book = tablib.Databook()

            for category in categories:
                cursor.execute("""SELECT rank, name, reviewscore, price, asin, link FROM items WHERE category = ? AND rank >= ? ORDER BY rank""", (str(category[0]), int(self._range[0])))
                items = cursor.fetchall()
                data = tablib.Dataset(title = category[0][:31])
                data.headers = ["Rank", "Name", "Review Score", "Price", "ASIN", "Link"]
                
                for item in items:
                    data.append(item)
                
                book.add_sheet(data)
                
            # Writing the items information to an excel file with multiple sheets
            makedirs(path.dirname(file_name), exist_ok=True)
            with open(file_name, 'wb') as f:
                f.write(book.xls)
            
            
    def get_asin(self, address):
        """Strips the ASIN out of a url and returns in."""
        splitaddy = re.split('[/\?]+', address)
        asin = [elem for elem in splitaddy if re.match("[A-Z0-9]{10}", elem)]
        asin = " ".join(asin)  # In case there are false positives everything is returned.
        if len(asin) > 10:   print(asin)
        return asin
        
        
    def pull_items(self, pages=[]):
        """Pulls items down from amazon for the given pages."""
        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()
        
        for page in pages:
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
        
        with open(self._config_name, 'w') as f:
            yaml.dump({'pages': ','.join(self._pages), 'email list': ','.join(self._email_list), 'range': ','.join(self._range), 'config name': self._config_name, 'database name': self._database_name, 'file name': self._file_name, 'email address': self._email_address, 'email password': self._email_password}, f)
        
        
    def read_config(self):
        """Reads in a config file and stores all the values in the private variables."""
        with open(self._config_name, 'r') as f:
            config_info = yaml.load(f)
            
        self._pages = config_info['pages'].split(',')
        self._email_list = config_info['email list'].split(',')
        self._range = config_info['range'].split(',')
        self._config_name = config_info['config name']
        self._database_name = config_info['database name']
        self._file_name = config_info['file name']
        self._email_address = config_info['email address']
        self._email_password = config_info['email password']
        
        
    def setup_config(self, pages, email_list, range, config, database, file, email_address, email_password):
        """Get all available information from passed in config file."""
        self._pages = pages.split(',') if pages is not None else self._pages
        self._email_list = email_list.split(',') if email_list is not None else self._email_list
        self._range = range.split(',') if range is not None else self._range
        self._config_name = config if config is not None else self._config_name
        self._database_name = database if database is not None else self._database_name
        self._file_name = file if file is not None else self._file_name
        self._email_address = email_address if email_address is not None else self._email_address
        self._email_password = email_password if email_password is not None else self._email_password
        
        
    def send_email(self, email_list=[]):
        """Sends output files to the emails in the list."""
        yag = yagmail.SMTP(self._email_address, self._email_password)
        contents = ["Attached are the amazon items.",  "output/AmazonItems.csv"]
        
        if len(email_list) > 0:
            yag.send(to=email_list, subject="AmazonEmailer Test in script", contents=contents)
        else:
            yag.send(subject="AmazonEmailer Test in script", contents=contents)
