"""Gets items from amazon and sends out an email with the items."""
import argparse
from amazonemailer import *


def main():
    """Sets up database, gets items, generates files and emails them."""
    parser = argparse.ArgumentParser(description="gets items from amazon and sends out an email with the items")
    parser.add_argument("-c", "--config", help="location of config file")
    parser.add_argument("-e", "--email", help="email addresses items should be sent to, comma seperated")
    parser.add_argument("-p", "--pages", help="pages that should be checked for items, comma seperated")
    parser.add_argument("-r", "--range", help="range of rankings that should be returned, comma seperated")
    parser.add_argument("-d", "--database", help="database name to be generated")
    parser.add_argument("-f", "--file", help="file name to be generated")
    args = parser.parse_args()
    
    if args.config:
        setup_config(args.config)

    if args.database:
        setup_database(args.database)
    else:
        setup_database()
        
    if args.pages and args.range:
        pull_items(args.pages.split(','), args.range.split(','))
    elif args.pages:
        pull_items(args.pages.split(','))
    elif args.range:
        pull_items(args.range.split(','))
    else:
        pages = ('https://www.amazon.com/gp/bestsellers/wireless/ref=sv_cps_6', 
             'https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Unlocked/zgbs/wireless/2407749011/ref=zg_bs_nav_cps_1_cps', 
             'https://www.amazon.com/Best-Sellers-Cell-Phones-Accessories-Phone-Cases-Holsters-Clips/zgbs/wireless/2407760011/ref=zg_bs_nav_cps_2_2407749011')

        pull_items(pages)
        
    if args.file:
        items_to_xls(args.file)
        items_to_csv(args.file)
    else:
        items_to_xls()
        items_to_csv()

    if args.email:
        send_email(args.email.split(','))
    else:
        send_email()

if __name__ == "__main__":
    main()
