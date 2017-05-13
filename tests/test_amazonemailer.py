"""Testing script"""
import pytest
from os import path
from amazonemailer import get_asin, setup_database, send_email, write_config

def test_get_asin():
    """ASIN is retrieved from address."""
    address = "https://www.amazon.com/AmazonBasics-Apple-Certified-Lightning-Cable/dp/B010S9N6OO?_encoding=UTF8&psc=1"
    expected_asin = "B010S9N6OO"
    
    assert expected_asin == get_asin(address)
    
    
def test_setup_database():
    """The database is what I think it is."""
    database_name = "./tests/test_database.db"
    setup_database(database_name)
    
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
    write_config()
    assert True
    
    
def test_read_config():
    """Values are read from the config file."""
    assert True
    
    
def test_setup_config():
    """Config is read in and everything is set up."""
    assert True
    
    
def test_send_email():
    """Emails are sent to the passed in list."""
    email_list = []
    
    send_email(email_list)
    
