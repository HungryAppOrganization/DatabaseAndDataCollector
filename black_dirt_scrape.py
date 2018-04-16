#  #######
#  # ### #
#  ### # #
#      # #
#      ###     Hungry LLC
#              Drafted 4/2/2018.
#      ###     Nitin Bhandari

###########    ###        ###  ###       ###  ####       ###      ##########  ###########  ###     ###     ########
###########    ###        ###  ###       ###  ### ##     ###    ############  ###########  ###     ###            ##
###########    ###        ###  ###       ###  ###  ##    ###  ####            ###      ##  ###     ###            ##
###########    ### ###### ###  ###       ###  ###   ##   ###  ####            ###########  ###     ###       ######
###########    ### ###### ###  ###       ###  ###    ##  ###  ####       ###  ###########   ###   ###        ##
###########    ###        ###  ###       ###  ###     ## ###  ####       ###  ### ###          ###           ##
###########    ###        ###   ###     ###   ###      # ###    ############  ###   ###        ###
###########    ###        ###     ######      ###       ####      ##########  ###     ###      ###           ##

import urllib2
from bs4 import BeautifulSoup
import pandas as pd
import csv

class websiteScrapper(object):
    def __init__(self, res_menu_url):
        self.res_url = res_menu_url
        self.page = urllib2.urlopen(self.res_url)
        self.soup = BeautifulSoup(self.page, 'html.parser')

    def menu_scrapper(self):
        dinner = self.soup.find_all('h3',class_="menu-item-name")
        p=self.soup.find_all('p')
        i=1
        iname=[]
        iprice=[]
        idesc=[]
        for dish in dinner:
            print dish.text
            te=dish.text.split("-")
            iname=iname+[te[0].encode('utf-8')]
            iprice=iprice+[te[1].encode('utf-8')]
            idesc=idesc+[p[i].text.encode('utf-8')]
            i=i+1
        # Saving information to the .csv file
        with open('database.csv', 'w') as csvfile:
            fieldnames = ['item_name', 'item_price','item_desc']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            i=0
            for x in iname:
                writer.writerow({'item_name': x, 'item_price': iprice[i],'item_desc':idesc[i]})
                i=i+1

def main():
    res_menu = websiteScrapper('http://www.blackdirtkc.com/dinner')
    res_menu_info = res_menu.menu_scrapper()
    print res_menu_info

if __name__ == '__main__':
    main()
