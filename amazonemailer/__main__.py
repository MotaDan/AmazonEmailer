"""Gets items from amazon and sends out an email with the items."""
import argparse
from amazonemailer import *


def main():
    """Given an image and a message or file steganographer will hide the message or file in the bits of the image."""
    parser = argparse.ArgumentParser(description="hides a message in a file or returns a message hidden in a file")
    parser.add_argument("-i", help="file to hide a message in or file to reveal a message from")
    parser.add_argument("-m", "--message", help="message to be hidden in the input file")
    parser.add_argument("-o", "--output",
                        help="name of output file to hide message in or to write revealed message")
    parser.add_argument("-f", "--file", help="file to be hidden in the input file")
    parser.add_argument("-r", "--reveal", action='store_true', help="a file will be revealed")
    args = parser.parse_args()

    setup_database()
    pull_items()
    items_to_xls()
    items_to_csv()


if __name__ == "__main__":
    main()
