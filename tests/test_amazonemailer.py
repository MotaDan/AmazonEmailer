"""Testing script"""
import pytest
from amazonemailer import get_asin

def test_get_asin():
    """ASIN is retrieved from address."""
    address = "https://www.amazon.com/AmazonBasics-Apple-Certified-Lightning-Cable/dp/B010S9N6OO?_encoding=UTF8&psc=1"
    expected_asin = "B010S9N6OO"
    
    assert expected_asin == get_asin(address)
    