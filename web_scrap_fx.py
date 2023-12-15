from requests_html import HTMLSession
import smtplib
from email.message import EmailMessage
import os
import logging

def get_logger():

    new_logger = logging.getLogger(__name__)

    f_handler = logging.FileHandler('web_scrap.log')
    f_handler.setLevel(logging.DEBUG)

    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)

    new_logger.addHandler(f_handler)
    new_logger.setLevel(logging.DEBUG)

    return new_logger

mylogger = get_logger()

def web_scrap():

    session = HTMLSession()
    r = session.get('https://uk.finance.yahoo.com/currencies')
    exchange_info = r.html.find('tr' , containing='GBPAUD', first=True).text
    exchange_info_list = exchange_info.split('\n')

    header_info = r.html.find('table', first=True).text
    exchange_headers = header_info.split('\n')[0:5]

    exchange_dict = {exc_head: ex_info for exc_head, ex_info in zip(exchange_headers, exchange_info_list)}

    info_in_string = ''.join(f'{key} - {value}\n' for key, value in exchange_dict.items())

    message = "Today's exchange rate:\n\n{}".format(info_in_string)

    mylogger.debug(f'{web_scrap.__name__} function has run')

    return message


def share_price(url, amt):

    session = HTMLSession()
    r = session.get(url)

    share_info = r.html.find('#quote-header-info', first=True).text
    info = share_info.split('\n')[:4:3]
    value = int(amt) * eval(info[1][:6:1]) / 100

    mylogger.debug('Share price function has run')

    share_details = '\n'.join(info)

    result = f'{share_details}\nValue - £{value:,.2f}'

    return result

def weather():

    session = HTMLSession()
    r = session.get('https://www.bbc.co.uk/weather/2643743')

    temps = r.html.find('div.wr-time-slot-primary__temperature')
    times = r.html.find('span.wr-time-slot-primary__time')


    list_temps = [temp.text[:3:1] for temp in temps]
    list_times = [time.text for time in times]


    comb_list = [w for w in zip(list_times, list_temps)]

    res = ''.join(f'{key} - {value}\n' for key, value in comb_list)

    mylogger.debug('Weather function has run')

    return res



def send_email(message, subject):

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = 'Sam Morris <samuel.morris1980@gmail.com>'
    msg['To'] = 'sam_morris66@hotmail.com'

    msg.set_content(message)

    print(os.environ)


    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login('samuel.morris1980@gmail.com', os.environ['email_password'])
        server.send_message(msg)


def fpl_price_updates():

    session = HTMLSession()
    r = session.get('https://www.livefpl.net/prices')

    price = r.html.find('tbody', first=True).text

    price_list = price.split('\n')

    del price_list[1::4]

    player = {}
    players = []

    # Range START, END, STEP
    for item in range(0, len(price_list), 3):

        player['Name'] = price_list[item]
        player['Old price'] = price_list[item + 1]
        player['New price'] = price_list[item + 2]

        res = ''.join(f'{key} - {value}\n' for key, value in player.items())

        players.append(f'{res}\n')


    return "".join(players)


msg = f'{web_scrap()}\n{share_price("https://uk.finance.yahoo.com/quote/CMCX.L?p=CMCX.L", 1225)}' \
     f'\n\n{share_price("https://uk.finance.yahoo.com/quote/LGEN.L?p=LGEN.L", 1500)}\n\nWeather Today:\n{weather()}' \
    f'\n{fpl_price_updates()}'


send_email(msg, 'Exchange rate latest')
