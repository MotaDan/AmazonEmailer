from bs4 import BeautifulSoup
import requests
import sqlite3
from os import remove, path, makedirs
import csv
import tablib

_database_name = "output/amazonBestSellers.db"

def setup_database(database_name=_database_name):
    """Setting up sqlite database for items."""
    _database_name = database_name
    makedirs(path.dirname(database_name), exist_ok=True)
    
    # Deleting the previous database to avoid duplicate entries. I don't care what items existed before.
    if path.isfile(_database_name):
        remove(_database_name)
        
    connection = sqlite3.connect(_database_name)
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
    unique (name, reviewScore, price, link, rank));"""

    cursor.execute(sql_command)
    
    
def items_to_csv(file_name="output/AmazonItems.csv"):
    """Writing the items information to a csv file."""
    connection = sqlite3.connect(_database_name)
    cursor = connection.cursor()
    
    makedirs(path.dirname(file_name), exist_ok=True)
    with open(file_name, 'w', newline='') as f:
        fileWriter = csv.writer(f)
        cursor.execute("""SELECT rank, name, reviewscore, price, link FROM items WHERE category = 'Cell Phones & Accessories' ORDER BY rank""")
        result = cursor.fetchall()
        
        fileWriter.writerow(("Rank", "Name", "Review Score", "Price", "Link"))
        for item in result:
            fileWriter.writerow(item)
            
            
def items_to_xls(file_name="output/AmazonItems.xls"):
    """Writing the items information to an excel file with multiple sheets."""
    connection = sqlite3.connect(_database_name)
    cursor = connection.cursor()
    
    cursor.execute("""SELECT category FROM items GROUP BY category ORDER BY item_number""")
    categories = cursor.fetchall()

    book = tablib.Databook()

    for category in categories:
        cursor.execute("""SELECT rank, name, reviewscore, price, link FROM items WHERE category = ?ORDER BY rank""", category)
        items = cursor.fetchall()
        data = tablib.Dataset(title = category[0][:31])
        data.headers = ["Rank", "Name", "Review Score", "Price", "Link"]
        
        for item in items:
            data.append(item)
        
        book.add_sheet(data)
        
    # Writing the items information to an excel file with multiple sheets
    makedirs(path.dirname(file_name), exist_ok=True)
    with open(file_name, 'wb') as f:
        f.write(book.xls)
        
        
def pull_items(pages=[]):
    """Pulls items down from amazon for the given pages."""
    connection = sqlite3.connect(_database_name)
    cursor = connection.cursor()
    
    for page in pages:
        r = requests.get(page)
        asoup = BeautifulSoup(r.text, 'lxml')
        
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
            rankstr = item.find('span', class_='zg_rankNumber').string.strip().rstrip('.')
            
            sql_command = """INSERT INTO items (item_number, category, name, reviewscore, price, link, rank)
            VALUES (NULL, ?, ?, ?, ?, ?, ?);"""
            cursor.execute(sql_command, (categorystr, namestr, reviewscorestr, pricestr, linkstr, rankstr))

        connection.commit()
        
        
def setup_config(config_name=''):
    """Get all available information from passed in config file."""
    pass
    
    
def send_email(email_list=[]):
    """Sends output files to the emails in the list."""
    pass
