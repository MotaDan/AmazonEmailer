"""Gets items from amazon and sends out an email with the items."""
import argparse
from amazonemailer import *
import schedule
import time


def main(args):
    """Sets up database, gets items, generates files and emails them."""
    aemailer = AmazonEmailer()
    
    aemailer.read_config()
    aemailer.setup_config(pages=args.pages, email_list=args.email_list, range=args.range, config=args.config, database=args.database, file=args.file, email_address=args.email_address, email_password=args.email_password)
    aemailer.write_config()
    
    aemailer.setup_database()
    aemailer.pull_items()
    
    aemailer.items_to_xls()
    aemailer.items_to_csv()

    aemailer.send_email()
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gets items from amazon and sends out an email with the items")
    parser.add_argument("-c", "--config", help="location of config file")
    parser.add_argument("-e", "--email_list", help="email addresses items should be sent to, comma seperated")
    parser.add_argument("-p", "--pages", help="pages that should be checked for items, comma seperated")
    parser.add_argument("-r", "--range", help="range of rankings that should be returned, comma seperated")
    parser.add_argument("-d", "--database", help="database name to be generated")
    parser.add_argument("-f", "--file", help="file name to be generated")
    parser.add_argument("-a", "--email_address", help="email address for the sender")
    parser.add_argument("-b", "--email_password", help="email address password for the sender")
    parser.add_argument("-s", "--schedule", help="scheduled time to be run every day")
    args = parser.parse_args()
    
    main(args)
    
    if args.schedule:
        schedule.every().day.at(args.schedule).do(main, args)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
