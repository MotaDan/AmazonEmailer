from bs4 import BeautifulSoup
import requests
import sqlite3
from os import remove, path
import csv
import tablib

databaseName = "amazonBestSellers.db"
# Deleting the previous database so I don't have duplicate entries. I don't care what the top 20 was yesterday.
if path.isfile(databaseName):
    remove(databaseName)
    
connection = sqlite3.connect(databaseName)
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

pages = ('https://www.amazon.com/gp/bestsellers/wireless/ref=sv_cps_6', 
         'https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Unlocked/zgbs/wireless/2407749011/ref=zg_bs_nav_cps_1_cps', 
         'https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Phone-Cases-Holsters-Clips/zgbs/wireless/2407760011/ref=zg_bs_nav_cps_2_2407749011')

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
with open('AmazonItems.xls', 'wb') as f:
    f.write(book.xls)

# Writing the items information in a csv file.
with open('AmazonItems.csv', 'w', newline='') as f:
    fileWriter = csv.writer(f)
    cursor.execute("""SELECT rank, name, reviewscore, price, link FROM items WHERE category = 'Cell Phones & Accessories' ORDER BY rank""")
    result = cursor.fetchall()
    
    fileWriter.writerow(("Rank", "Name", "Review Score", "Price", "Link"))
    for item in result:
        fileWriter.writerow(item)

# Reading the information from the csv file and placing it in a text file.
with open('AmazonItems.csv', 'r', newline='') as csvf:
    fileReader = csv.reader(csvf)
    next(fileReader)  # Skipping column name line

    with open('AmazonItems.txt', 'w') as txtf:
        for row in fileReader:
            txtf.write("\n".join(row[1:]))  # Leaving out rank
            txtf.write("\n\n")

connection.close()