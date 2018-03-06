#  #######
#  # ### #
#  ### # #
#      # #
#      ###        Hungry LLC 
#                 Drafted 2/6/2018.
#      ###        Nitin Bhandari

###########    ###        ###  ###       ###  ####       ###      ##########  ###########  ###     ###     ########
###########    ###        ###  ###       ###  ### ##     ###    ############  ###########  ###     ###            ## 
###########    ###        ###  ###       ###  ###  ##    ###  ####            ###      ##  ###     ###            ##
###########    ### ###### ###  ###       ###  ###   ##   ###  ####            ###########  ###     ###       ######  
###########    ### ###### ###  ###       ###  ###    ##  ###  ####       ###  ###########   ###   ###        ## 
###########    ###        ###  ###       ###  ###     ## ###  ####       ###  ### ###          ###           ##
###########    ###        ###   ###     ###   ###      # ###    ############  ###   ###        ###           
###########    ###        ###     ######      ###       ####      ##########  ###     ###      ###           ## 


# This code is responsible for fetching the tags/ingridents of the food items. 
# Input is a .csv db file where we pick up the name of food, restaurant name, address 
# and use a Food Square API to accomplish the task
# API's used: GoogleMapsAPI, FourSquare API, (Single Platform API)

import numpy as np
import pandas as pd
import requests
import urllib
import json
import googlemaps
from datetime import datetime
import time
from collections import Counter
import re
import math
import pyrebase
import os
from dotenv import load_dotenv
import keys


class GetDescriptorWords(object):

    # Constructor: The variables defined in here will be accessed by the supporter methods in this class
    # All the data extrtacted using pandas to create a DataFrame will have the same indices to maintain the order 
    # and will be helpful in merging them later after processing has been done

    def __init__(self):
        self.data = pd.read_csv("Rest_DB_2 - New_DB.csv")                   
        self.ind = list(range(1, len(self.data)+1))
        self.food_items = pd.Series([x.replace('_', ' ') for x in self.data['|__descrip']], index=self.ind)
        self.res_names = pd.Series(self.data['|__name'], index=self.ind)
        self.res_add = pd.Series([x.replace(' ','+').rstrip(x[-6:]) for x in self.data['|__location']], index=self.ind)
    
    ##########################################
    ######## Supporter Methods ###############
    ##########################################

    ##################################################################################################
    #### This method id responsible to get the coordinates of the restuarants using GoogleMapsAPI ####
    ##################################################################################################

    def getlatLng(self, api):
        base_url = "https://maps.googleapis.com/maps/api/geocode/json?"
        addressList = [x for x in self.res_add]
        UniqueAddresses = set(addressList)
        UniqueList = list(UniqueAddresses)
        #print UniqueList
        coord = []
        latlng = []
        for i in range(0, 4):      ## Change loop to for address in addresses & replace addressList[i] with address in GeoURL
            #print addressList[i]
            GeoUrl = base_url + 'address=' + addressList[i] + "&key=" + api
            #print GeoUrl
            response = urllib.urlopen(GeoUrl)
            jsonRaw = response.read()
            jsonData = json.loads(jsonRaw)
            if jsonData['status'] == 'OK':
                resu =  jsonData['results'][0]
                latlng.append([resu['geometry']['location']['lat'], resu['geometry']['location']['lng']])
            else:
                latlng.append([None, None])
        #print len(latlng)
        coord = pd.Series(latlng)  # Add parameter index=self.ind to start indices from 1 instead of 0
        return coord

    ##########################################################################################################################
    ###### The following three supporter are used by getMenu method is returns similarity between names of food items ########
    ##########################################################################################################################

    def get_cosine(self, vec1, vec2):
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        if not denominator:
            return 0.0
        else:
            return float(numerator) / denominator

    def text_to_vector(self, text):
        word = re.compile(r'\w+')
        words = word.findall(text)
        return Counter(words)

    def getCosineSimilarity(self, content_a, content_b):
        text1 = content_a
        text2 = content_b

        vector1 = self.text_to_vector(text1)
        vector2 = self.text_to_vector(text2)

        cosine_result = self.get_cosine(vector1, vector2)
        return cosine_result

    ###########################################################################
    #### This method is responsible for getting the menu of the restuarant ####
    ###########################################################################

    def getMenu(self, coord):
        FOOD_CAT = FourSquare_FOOD_CAT
        CLIENT_ID = FourSquare_CLIENT_ID
        CLIENT_SEC = FourSquare_CLIENT_SECRET

        search_url = "https://api.foursquare.com/v2/venues/search?"
        base_menu_url = "https://api.foursquare.com/v2/venues/"

        ### List to store latitude and lognitude of the resturant address
        ll = []
        
        for i in coord:
            ll.append(str(i[0])+","+str(i[1]))

        ## Converting all lists into pandas Series(with only one column) DataFrame and merging all series DF to one DF and
        ## converting that DF back to a csv file

        ll = pd.Series(ll)
        #print ll
        
        res_id = []

        for i in ll:
            venue_url = search_url + "ll=" + i + "&client_id=" + CLIENT_ID + "&client_secret=" + CLIENT_SEC + "&category_id=" + FOOD_CAT+ "&v=20170801"
            response = urllib.urlopen(venue_url)
            jsonRaw = response.read()
            jsonData = json.loads(jsonRaw)          
            id_res = str(jsonData["response"]["venues"][0]["id"])
            res_id.append(id_res)
            #print res_id
            menu_url = base_menu_url + id_res + '/menu?' + "&client_id=" + CLIENT_ID + "&client_secret=" + CLIENT_SEC + "&v=20170801"
            #print menu_url
            resp = urllib.urlopen(menu_url)
            jsonRaw2 = resp.read()
            jsonData2 = json.loads(jsonRaw2)

            #### Lists to store description, price, entry_name and entry_id of the food_item and later
            #### converting them into DataFrame using pandas and the same index as every other database
            
            description = []
            price = []
            entry_name = []
            entry_id = []

            #### Storing info. for new food_item 

            new_item_name = []
            new_item_description = []
            new_item_price = []
            new_item_entry_name = []
            new_item_entry_id = []
            new_item_res = []

            if  jsonData2['response']['menu']['menus']['count'] == 0:
                print 'Menu not found'

            else: # Menu has been found
                path = jsonData2['response']['menu']['menus']['items'][0]['entries']
                num_entries = path['count']
                self.food_items = self.food_items[:4]  ## Just a few data points to test the code

                for i,l in zip(self.food_items, self.res_names):
                    for j in range(num_entries):
                        num_items = path['items'][j]['entries']['count']
                        for k in range(num_items):
                            if i == path['items'][j]['entries']['items'][k]['name']:
                                try:
                                    description.append(path['items'][j]['entries']['items'][k]['description'])
                                    price.append(path['items'][j]['entries']['items'][k]['price'])
                                    entry_id.append(path['items'][j]['entries']['items'][k]['entryId'])
                                except Exception as e:
                                    raise e
                                else:
                                    description.append('Not Available')
                                    price.append(path['items'][j]['entries']['items'][k]['price'])
                                    entry_id.append(path['items'][j]['entries']['items'][k]['entryId'])
                            elif (self.getCosineSimilarity(i, path['items'][j]['entries']['items'][k]['name'])) > 0.7:
                                try:
                                    description.append(path['items'][j]['entries']['items'][k]['description'])
                                    price.append(path['items'][j]['entries']['items'][k]['price'])
                                    entry_name.append(path['items'][j]['name'])
                                    entry_id.append(path['items'][j]['entries']['items'][k]['entryId'])
                                except Exception as e:
                                    raise e
                                else:
                                    description.append('Not Available')
                                    price.append(path['items'][j]['entries']['items'][k]['price'])
                                    entry_name.append(path['items'][j]['name'])
                                    entry_id.append(path['items'][j]['entries']['items'][k]['entryId'])
                            else:
                                try:
                                    print '{} is NOT EQUAL to {}'.format(i, path['items'][j]['entries']['items'][k]['name'])
                                    print 'STORING NEW FOOD ITEM INFORMATION........'
                                    print type(path['items'][j]['entries']['items'][k]['name'])
                                    new_item_description.append(path['items'][j]['entries']['items'][k]['description'])
                                    new_item_price.append(path['items'][j]['entries']['items'][k]['price'])
                                    new_item_entry_name.append(path['items'][j]['name'])
                                    new_item_entry_id.append(path['items'][j]['entries']['items'][k]['entryId'])
                                    new_item_name.append(path['items'][j]['entries']['items'][k]['name'])
                                    new_item_res.append(l) # To keep track of food item belonging to what restaurant
                                except Exception as e:
                                    pass
                                else:
                                    new_item_description.append('Not Available')
                                    new_item_price.append(path['items'][j]['entries']['items'][k]['price'])
                                    new_item_entry_name.append(path['items'][j]['name'])
                                    new_item_entry_id.append(path['items'][j]['entries']['items'][k]['entryId'])
                                    new_item_name.append(path['items'][j]['entries']['items'][k]['name'])
                                    new_item_res.append(l)
                            
                
                        
if __name__ == "__main__":
    des = GetDescriptorWords()
    coord_latlng = des.getlatLng(Google_API_KEY)
    des.getMenu(coord_latlng)
