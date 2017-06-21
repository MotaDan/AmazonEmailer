"""Gets items from amazon and sends out an email with the items."""
import argparse
from amazonemailer import *
import schedule
import time


def main(arguments, emailer):
    """Sets up database, gets items, generates files and emails them."""
    emailer.read_config()
    print("Config read.")
    emailer.setup_config(pages=arguments.pages,
                         email_list=arguments.email_list,
                         items_range=arguments.range,
                         config=arguments.config,
                         database=arguments.database,
                         file=arguments.file,
                         email_address=arguments.email_address,
                         email_password=arguments.email_password,
                         send_time=arguments.time,
                         frequency=arguments.frequency)
    emailer.write_config()
    
    emailer.setup_database()
    if emailer.pull_items_search() != 'bot':
        print("Items retrieved")
    else:
        return
    
    emailer.items_to_xls()
    print("xls file created.")
    emailer.items_to_csv()
    print("csv file created")

    print("Sending emails.")
    emailer.send_email()
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gets items from amazon and sends out an email with the items")
    parser.add_argument("-c", "--config", help="location of config file")
    parser.add_argument("-e", "--email_list", help="email addresses items should be sent to, comma separated")
    parser.add_argument("-p", "--pages", help="pages that should be checked for items, comma separated")
    parser.add_argument("-r", "--range", help="range of rankings that should be returned, comma separated")
    parser.add_argument("-d", "--database", help="database name to be generated")
    parser.add_argument("-f", "--file", help="file name to be generated")
    parser.add_argument("-a", "--email_address", help="email address for the sender")
    parser.add_argument("-b", "--email_password", help="email address password for the sender")
    parser.add_argument("-t", "--time", help="time to be run")
    parser.add_argument("-q", "--frequency", help="how often the email is sent. daily, weekly, monthly")
    parser.add_argument("-s", "--no-schedule", help="disables the schedule from being run", dest='no_schedule', action='store_true')
    args = parser.parse_args()
    
    aemailer = AmazonEmailer()
    
    main(args, aemailer)
    
    # Run the schedule
    if args.no_schedule is False:
        frequency = {'daily': 1, 'weekly': 7, 'monthly': 30}
        
        schedule.every(frequency[aemailer.frequency]).days.at(aemailer.time).do(main, args, aemailer)
        
        while True:
            schedule.run_pending()
            time.sleep(1)

