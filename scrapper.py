# -*- coding: utf-8 -*-
from pyvirtualdisplay import Display
from difflib import SequenceMatcher
import logging
import re
from time import sleep
import requests
from bs4 import BeautifulSoup
from requests.exceptions import MissingSchema
from selenium import webdriver
from googleplaces import GooglePlaces
from tqdm import tqdm

from numpy import genfromtxt
from time import time
from datetime import datetime
from sqlalchemy import Column, Integer, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String

#Storing the DB in a .csv file next door. 

class SessionHandler:
    def __init__(self, browser='chrome', javascript=True, images=False, path=None):
        if browser == 'chrome':
            d = Display(visible=0, size=(1200, 900))
            d.start()
            chrome_options = webdriver.ChromeOptions()
            prefs = {}
            if javascript:
                prefs['profile.managed_default_content_settings.images'] = 2
            if images:
                prefs['profile.managed_default_content_settings.javascript'] = 2
            chrome_options.add_experimental_option("prefs", prefs)
            if path is None:
                self.session = webdriver.Chrome(chrome_options=chrome_options)
            else:
                self.session = webdriver.Chrome(chrome_options=chrome_options, executable_path=path)

class MenuItem:
    """
    Handles dish data, and a separate method for gathering calories for a given dish.
    """
    def __init__(self, dish_name, dish_size, dish_price, dish_cals, dish_items, image=None):
        self.dish_name = dish_name
        self.dish_size = dish_size
        self.dish_price = dish_price
        self.dish_cals = dish_cals
        self.dish_items = dish_items
        self.image = image

    def __repr__(self):
        return "{0},{1}".format(self.dish_name, self.image)

    def gather_dish_cals(self):
        """
        Uses MyFitnessPal.com to gather caloric and other nutritional info.
        """
        with requests.Session() as session:
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'})
            r = session.get('http://www.myfitnesspal.com/food/calorie-chart-nutrition-facts')
            soup = BeautifulSoup(r.content, 'html.parser')
            auth_token = soup.find('meta', attrs={'name': 'csrf-token'}).get('content')
            r = session.post('http://www.myfitnesspal.com/food/search',
                             data={
                                 'utf8': '✓',
                                 'authenticity_token': auth_token,
                                 'search': self.dish_name,
                                 'commit': 'Search'
                             }
                             )
            soup = BeautifulSoup(r.content, 'html.parser')
            try:
                for food_item in soup.find('ul', class_='food_search_results').find_all('li'):
                    r = session.get('http://www.myfitnesspal.com' + food_item.find('a').get('href'))
                    soup = BeautifulSoup(r.content, 'html.parser')
                    self.dish_cals = soup.find('table', attrs={'id': 'nutrition-facts'}).find('td',
                                                                                              class_='col-2').text.strip()
                    break
            except AttributeError:
                self.dish_cals = 'N/A'



class Restaurant:
    def __init__(self, api_response, location, browser):
        self.phone_regex = re.compile(
            '^(?:(?:\(?(?:00|\+)([1-4]\d\d|[1-9]\d?)\)?)?[\-\.\ \\\/]?)?((?:\(?\d{1,}\)?[\-\.\ \\\/]?){0,})(?:[\-\.\ \\\/]?(?:#|ext\.?|extension|x)[\-\.\ \\\/]?(\d+))?$')
        self.email_regex = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
        self.browser = browser
        self.api_response = api_response
        self.url = api_response.website
        self.name = api_response.name
        try:
            self.hours = api_response.details['opening_hours']
        except KeyError:
            self.hours = None
        self.menu_link = None
        self.menu = []
        self.type_of = None
        self.phone_numbers = [api_response.local_phone_number]
        self.emails = []

    def regex_scrape(self):
        """
        Separated function for phone_regex and email_regex to be called on every page crawl.
        :return: None, alters lists in place.
        """
        self.phone_numbers.extend(self.phone_regex.findall(self.browser.session.page_source))
        self.emails.extend(self.email_regex.findall(self.browser.session.page_source))
        pass

    def get_menu_link_from_google(self, logger):
        """
        Attempts to find a menu link via the Google Places response for the Restaurant.
        If none can be found, then we look on the website itself.
        :return: None, alters menu_link
        """
        r = requests.get(self.api_response.url)
        soup = BeautifulSoup(r.content, 'html.parser')
        potential_menu_links = [i for i in re.findall('(http:.*?)"', str(soup)) if 'google.com' not in i]
        logger.log(msg='Trying to get menu from google for {0}'.format(self.name).encode('utf-8'), level=logging.INFO)
        for link in potential_menu_links:
            if 'urbanspoon' in link:
                self.menu_link = link + '#regular', 'urbanspoon'
                self.scrape_menu()
                logger.log(msg='Menu link located.'.encode('utf-8'),
                           level=logging.INFO)
            elif 'singleplatform' in link:
                self.menu_link = link, 'singleplatform'
                #print(link)
                logger.log(msg='Menu link located.'.encode('utf-8'),
                           level=logging.INFO)


    def get_menu_link_from_site(self, logger):
        """
        Searches through links on site to locate a menu_link.
        Only called if menu_link couldn't be found via Google.
        :return: None, alters menu_link
        """
        self.browser.session.get(self.url)
        sleep(10)
        self.regex_scrape()
        for link in self.browser.session.find_elements_by_tag_name('a'):
            try:
                if 'menu' in str(link.get_attribute('href')) or 'menu' in str(link.text.lower()):
                    self.menu_link = link.get_attribute('href'), 'custom'
            except Exception as e:
                #print(e)
                continue

    def scrape_menu(self):
        """
        Controller function for menu scraping.
        :return: None
        """
        try:
            if self.menu_link[1] == 'urbanspoon':
                self.urbanspoon_scraper(self.menu_link[0])
            elif self.menu_link[1] == 'singleplatform':
                self.singleplatform_scraper(self.menu_link[0])
            elif self.menu_link[1] == 'custom':
                self.scrape_custom_menu(self.menu_link[0])
        except TypeError:
            return

    def urbanspoon_scraper(self, menu_link):
        """
        Urbanspoon-specific menu crawler.
        :param menu_link: str
        :return: None
        """
        with requests.Session() as session:
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'})
            r = session.get(menu_link)
            soup = BeautifulSoup(r.content, 'html.parser')
            full_menu_link = soup.find('a', class_='pt5 ttl zred').get('href')
            r = session.get(full_menu_link)
            soup = BeautifulSoup(r.content, 'html.parser')
            for menu_item in soup.find_all('div', class_='tmi'):
                for div in menu_item.find_all('div'):
                    if 'name' in str(div.get('class')):
                        dish_data = [i.strip() for i in div.text.splitlines() if len(i.strip()) > 1]
                        if len(dish_data) == 2:
                            dish_data.append('')
                        elif len(dish_data) == 1:
                            dish_data.extend(['', ''])
                        mi = MenuItem(dish_name=[i.strip() for i in dish_data[0].splitlines() if len(i.strip()) > 0][0],
                                      dish_size=None,
                                      dish_cals=None,
                                      dish_items=dish_data[2],
                                      dish_price=dish_data[1]
                                      )
                        self.menu.append(mi)

    def scrape_custom_menu(self, menu_link):
        """
        Scrapes a restaurants menu 'the hard way', through custom text parsing.
        :param menu_link: str
        :return: None
        """
        potential_menu_items = []
        with requests.Session() as session:
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'})
            try:
                r = session.get(menu_link)
            except MissingSchema:
                return
            soup = BeautifulSoup(r.content, 'html.parser')
            for tag in soup.find_all():
                try:
                    if 'menu-item' in tag.get('class'):
                        potential_menu_items.append(tag)
                except TypeError:  # no class attribute available for tag
                    pass
            for menu_item in potential_menu_items:
                menu_item = str(menu_item).replace('&amp;dollar;', '$').encode('utf-8')
                menu_item = BeautifulSoup(menu_item, 'html.parser').text.encode('utf-8')
                try:
                    price = re.search('(\$?\d+)', menu_item).group(1)
                except AttributeError:
                    price = 'N/A'
                name = menu_item.replace(price, '')
                mi = MenuItem(dish_name=[i.strip().encode('utf-8') for i in name.splitlines() if len(i.strip()) > 0][0],
                              dish_price=price,
                              dish_items=None,
                              dish_cals=None,
                              dish_size=None)
                self.menu.append(mi)
        pass

    def singleplatform_scraper(self, menu_link):
        """
        Singlepage-specific menu crawler.
        :param menu_link: str
        :return:
        """
        with requests.Session() as session:
            #print(menu_link)
            r = session.get(menu_link)
            soup = BeautifulSoup(r.content, 'html.parser')
            for item in soup.find('div', class_='items').find_all('div'):
                if 'item' in item.get('class'):
                    try:
                        description = item.find('div', class_='description text').text.strip()
                    except AttributeError:
                        description = None
                    try:
                        price = item.find('span', class_='price').text.strip()
                    except AttributeError:
                        price = None
                    mi = MenuItem(dish_name=[i.strip().encode('utf-8') for i in item.find('h4', class_='item-title').text.strip().splitlines() if len(i.strip()) > 1],
                                  dish_size=None,
                                  dish_price=price,
                                  dish_cals=None,
                                  dish_items=description)
                    self.menu.append(mi)
        pass

    def find_menu_link_from_postmates(self, logger, location):
        with requests.Session() as session:
            if location == 'Boston, MA':
                r = session.get('https://order.postmates.com/v1/place_search?lat=42.360406000000005&lng=-71.05799299999998&q={0}'.forNammat(self.name))
                self.menu_link = 'https://order.postmates.com/' + r.json()['places'][0]['web_url'].split('/')[-1]
                r = session.get(self.menu_link)
                soup = BeautifulSoup(r.content, 'html.parser')
                for item in soup.find_all('div', class_='catalog-product'):
                    mi = MenuItem(dish_name=item.find('div', class_='title').text.strip().encode('utf-8'),
                                  dish_size=None,
                                  dish_price=item.find('div', class_='price').text.strip().encode('utf-8'),
                                  dish_cals=None,
                                  dish_items=None)
                    self.menu.append(mi)

    def find_menu_link_from_allmenus(self, logger, location):
        with requests.Session() as session:
            r = session.get('https://www.allmenus.com/custom-results/-/{0}/'.format(self.name))
            soup = BeautifulSoup(r.content, 'html.parser')
            for restaurant in soup.find_all('li', class_='restaurant-list-item clearfix'):
                if self.name.split()[0] in restaurant.find('h4', class_='name').text:
                    self.menu_link = 'https://www.allmenus.com' + restaurant.find('a').get('href')
                    r = session.get(self.menu_link)
                    soup = BeautifulSoup(r.content, 'html.parser')
                    for menu_item in soup.find_all('li', class_='menu-items'):
                        mi = MenuItem(dish_name=menu_item.find('span', class_='item-title').text,
                                      dish_size=None,
                                      dish_price=menu_item.find('span', class_='item-price').text.strip(),
                                      dish_cals=None,
                                      dish_items=None
                                      )
                        self.menu.append(mi)

        pass


def search_for_restaurants(google_places_api, location, browser, logger):
    """
    Uses the Google Places API to search for restaurants in the supplied location.
    :param google_places_api: GooglePlaces
    :param location: str
    :param browser: webdriver
    :return: None
    """
    logger.log(msg='Beginning search for location {0}'.format(location).encode('utf-8'), level=logging.INFO)
    query_results = google_places_api.text_search(
        query='restaurants',
        location='{0}'.format(location).encode('utf-8')
    )
    print("Query results" , query_results)
    for index, place in enumerate(query_results.places):

        gather_data_for_place(index, place, logger, location, browser)
    while True:
        try:
            if query_results.has_next_page_token:
                query_results = google_places_api.nearby_search(
                    pagetoken=query_results.next_page_token)
                for index, place in enumerate(query_results.places):
                    gather_data_for_place(index, place, logger, location, browser)
        except Exception as e:
            print(e)
            break



def get_pictures_for_restaurant(index, place, logger, location, restaurant):
    result = []
    with requests.Session() as session:
        r = session.get(
            'https://www.yelp.com/search?find_desc={0}&find_loc={1}'.format(
                place.name, location
            ))
        soup = BeautifulSoup(r.content, 'html.parser')
        try:
            print("The soup")
            print(soup)
            first_result = soup.find('li', class_='regular-search-result').find('h3', class_='search-result-title')
        except AttributeError:
            return
        first_result_name = ' '.join(first_result.text.split()[1:])
        if SequenceMatcher(None, first_result_name, place.name).ratio() > 0.5:
            logger.log(msg='Match found.', level=logging.INFO)
            #print('https://www.yelp.com' + first_result.find('a').get('href'))
            r = session.get('https://www.yelp.com' + first_result.find('a').get('href'))
            index = 0
            photo_link = r.url.replace('/biz/',
                                       '/biz_photos/')
            for i in range(0,10):
                string = '?start={0}&tab=food'.format(i * 30)
                #print(index)
                #print(photo_link)
                #print(photo_link + string)
                food_photos = session.get(photo_link + string)
                if '?' not in food_photos.url:
                    return result
                soup = BeautifulSoup(food_photos.content, 'html.parser')
                pictures = ['https://www.yelp.com' + i.get('href') for i in soup.find_all('a', attrs={'data-analytics-label': 'biz-photo'})]
                for link in pictures[1:]:
                    r = requests.get(link)
                    pic_soup = BeautifulSoup(r.content, 'html.parser')
                    if len(pic_soup.find('div', class_='caption selected-photo-caption-text').text.strip()) > 1:
                        result.append(
                            (pic_soup.find('div', class_='caption selected-photo-caption-text').text.strip(),
                             pic_soup.find('img', class_='photo-box-img').get('src'))
                        )
                index += 1
    return result


def gather_data_for_place(index, place, logger, location, browser):
    logger.log(msg='Gathering data for search result {0}: Name: {1}'.format(index, place.name), level=logging.INFO)
    place.get_details()
    #  if 'Mooo' not in place.name:
    #    return
    #  The above lines are used for testing only.
    print('---------------')
    print(place.name)
    r = Restaurant(place, location, browser)
    logger.log(msg='Created restaurant object for {0}'.format(place.name), level=logging.INFO)
    print("Created DB account for restaurant")
    myLocation = None
    myName = None
    myAddress = None
    myNumber = None
    myHours = None
    try:
        print("City: " , location)
        myLocation = location
        print("Name: " , place.name)
        myName = place.name
    except:
        pass
    try:
        print("Address:",place.formatted_address)
        myAddress = place.formatted_address
    except:
        pass
    try:
        print("Phone Num:",place.formatted_phone_number)
        myNumber = place.formatted_phone_number
    except:
        pass
    try:
        print("Hours:",place.opening_hours)
        myHours = place.opening_hours
    except:
        pass
    #Now we make it

    rest = RestaurantDB(address=myAddress,name=myName,number=myNumber,city=myLocation,hours=myHours)
    s.add(rest)
    s.commit()

    r.get_menu_link_from_google(logger)
    if r.menu_link is None:
        r.find_menu_link_from_postmates(logger, location)
    if r.menu_link is None:
        r.find_menu_link_from_allmenus(logger, location)
    if r.menu_link is None:
        logger.log(msg='Forced to find menu via site.'.format(index, place.name),
                   level=logging.INFO)
        r.get_menu_link_from_site(logger)
    else:
        logger.log(
            msg='Gathered menu data from google for {0}'.format(place.name),
            level=logging.INFO)
    r.scrape_menu()
    old_dish_name = []
    #print(vars(r))
    for item in r.menu:
        logger.log(msg='Gathering data for MenuItem {0}.'.format(item.dish_name),
                   level=logging.INFO)
        item.gather_dish_cals()
        if item.dish_name in old_dish_name:
            #print(place.name)
            break
        else:
            old_dish_name.append(item.dish_name)
        #break
    pictures = get_pictures_for_restaurant(index, place, logger, location, r)
    logger.log(msg='Finished collecting pictures from Yelp.', level=logging.INFO)
    for item in tqdm(r.menu):
        logger.log(msg='Looking for picture for {0}.'.format(item.dish_name),
                   level=logging.INFO)
        for picture_tuples in pictures:
            similarity_check = SequenceMatcher(None, item.dish_name, picture_tuples[0]).ratio()
            if similarity_check >= 0.6:
                logger.log(
                    msg='Picture match found.'.format(item.dish_name),
                    level=logging.INFO)
                item.image = picture_tuples[1]
                pictures.remove(picture_tuples)
        #break
    for picture_tuple in pictures:
        mi = MenuItem(dish_name=picture_tuple[0],
                      dish_size=None,
                      dish_price=None,
                      dish_cals=None,
                      dish_items=None,
                      image=picture_tuple[1])
        mi.gather_dish_cals()
        r.menu.append(mi)
    print(vars(r))
    #Need to save the variables
    #Okay i need to link the menu items now.
    print(r.menu)
    for item in r.menu:
        print(item)
        print(item.dish_name)
        print(item.dish_price)
        print(item.image)
        print(item.dish_cals)
        #Note that for the price we need to remove (if present, a $). Then we need to multiply by 100 and store.
        #Calorie should be stored as-is
        if (item.dish_price[0]=='$'):
            item.dish_price = item.dish_price[1:]*100

        item = MenuItemDB(name=item.dish_name,cost=int(item.dish_price),picture=item.image,calorie=int(item.dish_cals),restaurant=rest)
        s.add(item)
        s.commit()
    #sys.exit()







    


def initialize_logging():
    """
    Creates the logger, sets logging info level and attaches
    it to a file handler writing to indeedScraper.log
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    with open('restaurant_scraper.log'.format(__name__), 'w'):
        handler = logging.FileHandler('restaurant_scraper.log')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


Base = declarative_base()

class RestaurantDB(Base):
    __tablename__ = 'restaurant'
    id = Column(Integer,primary_key=True)
    address = Column(String(250))
    name = Column(String(250))
    number = Column(String(250))
    city = Column(String(250))
    hours = Column(String(250))

class MenuItemDB(Base):
    __tablename__ = 'menuitem'
    id = Column(Integer, primary_key=True)

    name = Column(String(250))
    cost = Column(Integer)
    picture = Column(String(250))

    calorie = Column(Integer)

    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
    restaurant = relationship(RestaurantDB)



engine = create_engine('sqlite:///data/csv_test2.db')
#Base.metadata.create_all(engine)

#Create the session
session = sessionmaker()
session.configure(bind=engine)
s = session()


def main():
    logger = initialize_logging()
    browser = SessionHandler()
    dotenv_path = ".env"
    load_dotenv(dotenv_path, verbose=True)

    try:
        YOUR_API_KEY = os.environ.get("GOOGLPLACESAPI")
        google_places = GooglePlaces(YOUR_API_KEY)
        for location in ['Springfield, MO']:
            search_for_restaurants(google_places, location, browser, logger)
    finally:
        browser.session.quit()


if __name__ == '__main__':
    main()
