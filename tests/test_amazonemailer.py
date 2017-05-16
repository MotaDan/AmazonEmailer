"""Testing script"""
import pytest
from os import path
from amazonemailer import *


def test_get_asin():
    """ASIN is retrieved from address."""
    aemailer = AmazonEmailer()
    address = "https://www.amazon.com/AmazonBasics-Apple-Certified-Lightning-Cable/dp/B010S9N6OO?_encoding=UTF8&psc=1"
    expected_asin = "B010S9N6OO"
    
    assert expected_asin == aemailer.get_asin(address)
    
    
def test_setup_database():
    """The database is what I think it is."""
    aemailer = AmazonEmailer()
    database_name = "./tests/test_database.db"
    aemailer.setup_config(database=database_name)
    aemailer.setup_database()
    
    assert path.isfile(database_name)

    
def test_items_to_csv():
    """The items are stored in a csv file."""
    assert True
    
    
def test_items_to_xls():
    """The items are stored in a xls file."""
    assert True
    
    
def test_pull_items():
    """Items from given page and range are returned."""
    assert True
    
    
def test_write_config():
    """Values are written to the config file."""
    aemailer = AmazonEmailer()
    aemailer.write_config()
    assert True
    
    
def test_read_config():
    """Values are read from the config file."""
    aemailer = AmazonEmailer()
    aemailer.read_config()
    assert True
    
    
def test_setup_config():
    """Config is read in and everything is set up."""
    assert True
    
    
def test_send_email():
    """Emails are sent to the passed in list."""
    aemailer = AmazonEmailer()
    email_list = []
    
    #aemailer().send_email(email_list)
    
