"""Testing script"""
import pytest
from amazonemailer import *


def test_get_asin():
    """ASIN is retrieved from address."""
    aemailer = AmazonEmailer()
    address = "https://www.amazon.com/AmazonBasics-Apple-Certified-Lightning-Cable/dp/B010S9N6OO?_encoding=UTF8&psc=1"
    expected_asin = "B010S9N6OO"
    
    assert expected_asin == aemailer.get_asin(address)
    
    
@pytest.fixture
def config_setup():
    aemailer = AmazonEmailer()
    database_name = "./tests/database_test.db"
    config_name = "./tests/config_test.yaml"
    file_name = "./tests/AmazonItems_test"
    range = "15,50"
    pages = """https://www.amazon.com/gp/bestsellers/wireless/ref=sv_cps_6, https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Unlocked/zgbs/wireless/2407749011/ref=zg_bs_nav_cps_1_cps, https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Phone-Cases-Holsters-Clips/zgbs/wireless/2407760011/ref=zg_bs_nav_cps_2_2407749011"""
    aemailer.setup_config(config=config_name, database=database_name, file=file_name, pages=pages, items_range=range)
    return aemailer
    
    
def test_setup_database(config_setup):
    """The database is what I think it is."""
    aemailer = config_setup
    aemailer._database_name = "./tests/test_setup_database.db"
    aemailer.setup_database()
    
    assert path.isfile(aemailer._database_name)
    remove(aemailer._database_name)

    
def test_items_to_csv(config_setup):
    """The items are stored in a csv file."""
    aemailer = config_setup
    og_file_name = aemailer._file_name
    aemailer._file_name = "./tests/test_items_to_csv"
    aemailer._pages = "https://www.amazon.com/gp/bestsellers/wireless/ref=sv_cps_6"
    aemailer.items_to_csv()
    
    assert path.isfile(aemailer._file_name + ".csv")
    
    with open(aemailer._file_name + ".csv", 'r') as new, open(og_file_name + ".csv", 'r') as original:
        assert new.read() == original.read()
    
    remove(aemailer._file_name + ".csv")
    
    
def test_items_to_xls(config_setup):
    """The items are stored in a xls file."""
    aemailer = config_setup
    og_file_name = aemailer._file_name
    aemailer._file_name = "./tests/test_items_to_xls"
    aemailer.items_to_xls()
    
    assert path.isfile(aemailer._file_name + ".xls")
    
    with open(aemailer._file_name + ".xls", 'rb') as new, open(og_file_name + ".xls", 'rb') as original:
        assert new.read() == original.read()
    
    remove(aemailer._file_name + ".xls")
    
    
def test_pull_items_best_sellers(config_setup):
    """Items from given page and range are returned."""
    aemailer = config_setup
    aemailer._database_name = "./tests/test_pull_items_best_sellers.db"
    aemailer._file_name = "./tests/test_pull_items"
    aemailer.setup_database()
    aemailer.pull_items_best_sellers()
    aemailer.items_to_xls()
    aemailer.items_to_csv()
    
    # Don't compare contents because they change from day to day.
    assert path.isfile(aemailer._file_name + ".xls")
    assert path.isfile(aemailer._file_name + ".csv")
        
    remove(aemailer._file_name + ".xls")
    remove(aemailer._file_name + ".csv")
    remove(aemailer._database_name)
    
    
def test_write_config(config_setup):
    """Values are written to the config file."""
    aemailer = config_setup
    og_config_name = aemailer._config_name
    aemailer._config_name = "./tests/test_write_config.yaml"
    aemailer.write_config()
    
    with open(aemailer._config_name, 'r') as new, open(og_config_name, 'r') as original:
        # The first line is different because the two config files have different names.
        assert new.readlines()[1:] == original.readlines()[1:]
    
    remove(aemailer._config_name)
    
    
def test_read_config():
    """Values are read from the config file."""
    aemailer = AmazonEmailer()
    aemailer._config_name = "./tests/config_test.yaml"
    aemailer.read_config()
    
    assert aemailer._database_name == "./tests/database_test.db"
    assert aemailer._config_name == "./tests/config_test.yaml"
    assert aemailer._email_list == []
    assert aemailer._pages == ['https://www.amazon.com/gp/bestsellers/wireless/ref=sv_cps_6', ' https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Unlocked/zgbs/wireless/2407749011/ref=zg_bs_nav_cps_1_cps', ' https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Phone-Cases-Holsters-Clips/zgbs/wireless/2407760011/ref=zg_bs_nav_cps_2_2407749011']
    assert aemailer._range == ['15', '50']
    assert aemailer._file_name == "./tests/AmazonItems_test"
    assert aemailer._email_address == None
    assert aemailer._email_password == ''
    
    
def test_setup_config():
    """Config is read in and everything is set up."""
    aemailer = AmazonEmailer()
    database_name = "./tests/database_test.db"
    config_name = "./tests/config_test.yaml"
    email_list = "Test@gmail.com,Test2@gmail.com"
    pages = """https://www.amazon.com/gp/bestsellers/wireless/ref=sv_cps_6, https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Unlocked/zgbs/wireless/2407749011/ref=zg_bs_nav_cps_1_cps, https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Phone-Cases-Holsters-Clips/zgbs/wireless/2407760011/ref=zg_bs_nav_cps_2_2407749011"""
    range = "1,50"
    file_name = "./tests/AmazonItems_test"
    email_address = "sender@gmail.com"
    email_password = "password"
    
    aemailer.setup_config(pages=pages, email_list=email_list, items_range=range, config=config_name, database=database_name, file=file_name, email_address=email_address, email_password=email_password)
    
    assert aemailer._database_name == "./tests/database_test.db"
    assert aemailer._config_name == "./tests/config_test.yaml"
    assert aemailer._email_list == ['Test@gmail.com', 'Test2@gmail.com']
    assert aemailer._pages == ['https://www.amazon.com/gp/bestsellers/wireless/ref=sv_cps_6', ' https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Unlocked/zgbs/wireless/2407749011/ref=zg_bs_nav_cps_1_cps', ' https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Phone-Cases-Holsters-Clips/zgbs/wireless/2407760011/ref=zg_bs_nav_cps_2_2407749011']
    assert aemailer._range == ['1', '50']
    assert aemailer._file_name == "./tests/AmazonItems_test"
    assert aemailer._email_address == 'sender@gmail.com'
    assert aemailer._email_password == 'password'
    

def test_send_email(capfd, config_setup):
    """Emails are sent to the passed in list. I don't have a good way to test this so it just goes with no email."""
    aemailer = config_setup
    aemailer._email_address = None
    aemailer.send_email()
    out, _ = capfd.readouterr()
    
    assert out == "Need gmail address to send emails from.\n"
    
