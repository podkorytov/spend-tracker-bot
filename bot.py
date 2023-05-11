import configparser
import telebot
import logging
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Enable logging
logging.basicConfig(level=logging.DEBUG)

# Read configuration values from file
config = configparser.ConfigParser()
config.read('config.cfg')

# Get Telegram bot token from config file
telegram_bot_token = config.get('TELEGRAM', 'bot_token')

# Get Google Sheets API credentials from JSON file
google_sheets_credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'google_sheets_credentials.json',
    ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
)

# Authenticate with Google Sheets API
google_sheets_client = gspread.authorize(google_sheets_credentials)

# Get the specified sheet and worksheet
google_sheets_sheet = google_sheets_client.open(config.get('GOOGLE_SHEETS', 'sheet_name')).worksheet(
    config.get('GOOGLE_SHEETS', 'worksheet_name')
)

# Create Telegram bot object
bot = telebot.TeleBot(telegram_bot_token)

# Authorized users
AUTHORIZED_USERS = config.get('TELEGRAM', 'authorized_users').split(',')

# Handle incoming messages
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if str(message.from_user.id) not in AUTHORIZED_USERS:
        bot.reply_to(message, "Sorry, you are not authorized to use this bot.")
        return

    # Hello message
    bot.reply_to(message, "Hello! This is Home Accounting Bot. Send me any text message and I'll add it to the spreadsheet.")


@bot.message_handler(func=lambda message: True)
def add_record_to_sheet(message):
    if str(message.from_user.id) not in AUTHORIZED_USERS:
        bot.reply_to(message, "Sorry, you are not authorized to use this bot.")
        return

    # split the message into two parts: the number and the text
    match = re.match(r'^(\d+)\s+(.+)$', message.text)
    if not match:
        bot.reply_to(message, "Invalid format. Please provide a price followed by description.")
        return

    number = match.group(1)
    text = match.group(2)

    # get the column and find the top empty cell
    column_number = int(config.get('GOOGLE_SHEETS', 'column_number'))
    column = google_sheets_sheet.col_values(column_number)
    top_empty_cell = len(column) + 1

    # update the worksheet with the number and text
    google_sheets_sheet.update_cell(top_empty_cell, column_number, text)
    google_sheets_sheet.update_cell(top_empty_cell, column_number + 1, number)

    # reply to client
    bot.reply_to(message, f"Your message has been added to row {top_empty_cell} in the sheet!")


bot.polling()
