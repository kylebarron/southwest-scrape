#! /usr/bin/env python3
"""
Program: recreation_gov_scrape.py
Author:  Kyle Barron
Created: 6/15/2018, 9:38:50 PM
Updated: 6/15/2018, 9:38:50 PM
Purpose: Scrape Southwest flights
"""

import platform

from operator import itemgetter

from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys


def main():
    origin = 'bos'
    dest = 'san'
    date = '2019-03-17'

    if platform.system() == 'Darwin':
        chromedriver_path = './bin/chromedriver_mac'
    elif platform.system() == 'Linux':
        chromedriver_path = './bin/chromedriver_linux'

    driver = webdriver.Chrome(chromedriver_path)
    driver.set_window_size(1200, 800)

    url = make_url(origin, dest, date)
    data = scrape(driver, url)

    # Deduplicate list with non hashable content
    s = []
    for i in data:
        if i not in s:
            s.append(i)

    # Sort by price
    data = sorted(s, key=itemgetter('price'))

    driver.close()


def scrape(driver, url):
    soup = get_soup(driver, url)
    lis = soup.find_all(
        class_=
        'air-booking-select-detail air-booking-select-detail_min-products air-booking-select-detail_min-duration-and-stops'
    )

    data = []
    for li in lis:
        li
        times = li.find_all(
            class_=
            'air-operations-time-status air-operations-time-status_booking-primary select-detail--time'
        )
        dep_time = times[0].text
        arr_time = times[1].text

        duration = li.find(class_='flight-stops--duration-time').text
        stops = [
            x.text[:3] for x in li.find_all(class_='flight-stops--item-title')
        ]
        price = li.find(
            class_='fare-button fare-button_primary-yellow select-detail--fare'
        )

        # Account for sold out flights without a coach class fare
        try:
            price = price.find(class_='fare-button--value-total').text
        except AttributeError:
            continue

        data.append({
            'price': price,
            'dep_time': dep_time,
            'arr_time': arr_time,
            'duration': duration,
            'stops': stops
        })

    return data


def get_soup(driver, url):
    # Load page
    driver.get(url)

    # Wait until fare buttons exist
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,
                                        '.fare-button--button')))
    html = driver.find_element_by_tag_name('html')
    html.send_keys(Keys.END)
    sleep(5)

    return BeautifulSoup(driver.page_source, 'lxml')


def make_url(origin, dest, date):
    """

    This only finds one way flights

    Args:
        origin (str): origin airport code
        dest (str): destination airport code
        date (str): date of departure (YYYY-MM-DD)

    """

    url = 'https://www.southwest.com/air/booking/select.html?'
    url += 'originationAirportCode=' + origin.upper()
    url += '&destinationAirportCode=' + dest.upper()
    url += '&returnAirportCode='
    url += '&departureDate=' + date
    url += '&departureTimeOfDay=ALL_DAY&returnDate=&returnTimeOfDay=ALL_DAY'
    url += '&adultPassengersCount=1&seniorPassengersCount=0'
    url += '&fareType=USD&passengerType=ADULT&tripType=oneway'

    return url


if __name__ == '__main__':
    main()
