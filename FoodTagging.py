#  #######
#  # ### #
#  ### # #
#      # #
#      ###        Hungry LLC 
#                 Drafted 2/6/2018.
#      ###        Nitin Bhandari

###########    ###        ###  ###       ###  ####       ###      ##########  ###########  ###     ###     ########
###########    ###		  ###  ###		 ###  ### ##     ###    ############  ###########  ###     ###            ## 
###########	   ###		  ###  ###		 ###  ###  ##    ###  ####  		  ###      ##  ###     ###            ##
###########	   ### ###### ###  ###       ###  ###	##   ###  ####            ###########  ###     ###       ######  
###########	   ### ###### ###  ###       ###  ###	 ##  ###  ####       ###  ###########   ###   ###        ## 
###########	   ###		  ###  ###  	 ###  ###	  ## ###  ####       ###  ### ###		   ###	         ##
###########	   ###		  ###   ###     ###   ###	   # ###    ############  ###   ###		   ###	         
###########	   ###		  ###     ######      ###    	####      ##########  ###     ###      ###           ## 


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


class GetDescriptorWords(object):

	# Constructor: The variables defined in here will be accessed by the supporter methods in this class
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
		coord = []
		latlng = []
		for i in range(0, 4):			############Change the loop to for address in addresses and replace the addressList[i] with address in GeoURL
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
	#### This method is return the cosine similarity between two strings #####################################################
	##########################################################################################################################
	### Source: https://stackoverflow.com/questions/15173225/calculate-cosine-similarity-given-2-sentence-strings/15173821 ###
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
		FOOD_CAT = '4d4b7105d754a06374d81259'
		CLIENT_ID = 'OXOP1HNDEV0NQOXJ3R5RC5GZWSKIFXOJOGA1KDHZXMNNFEJL'
		CLIENT_SEC = '1OCNH4GAHSM1OIVYZHISHRRVPM0BSF0OP2PYDQXTCSG4KMLD'

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
			#jsonData2 = json.dumps(jsonRaw2)

			#########################################################
			###### UNABLE TO ACCESS ITEMS(LIST) FROM JSON DATA ######
			################# But works inside the loop #############
			######################### Line 154 ######################
			#################### HELP REQ. ##########################
			#########################################################


			#print jsonData2['response']['menu']['menus']['items'][0]['name']

			#### Lists to store description, price, entry_name and entry_id of the food_item
			
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

			#########################################################
			###### UNABLE TO ACCESS DESCRIPTION FROM JSON DATA ######
			######################### Line 204 ######################
			#################### HELP REQ. ##########################
			#########################################################

			
			if  jsonData2['response']['menu']['menus']['count'] == 0:
				print 'Menu not found'
			else:
				num_entries = jsonData2['response']['menu']['menus']['items'][0]['entries']['count']
				#print type(num_entries)
				self.food_items = self.food_items[:4]
				for i,l in zip(self.food_items, self.res_names):
					for j in range(num_entries):
						num_items = jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['count']
						for k in range(num_items):
							if i == jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['name']:
								try:
									description.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['description'])
									price.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['price'])
									entry_id.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['entryId'])
								except Exception as e:
									raise e
								else:
									description.append('Not Available')
									price.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['price'])
									entry_id.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['entryId'])
							elif (self.getCosineSimilarity(i, jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['name'])) > 0.7:
								try:
									description.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['description'])
									price.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['price'])
									entry_name.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['name'])
									entry_id.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['entryId'])
								except Exception as e:
									raise e
								else:
									description.append('Not Available')
									price.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['price'])
									entry_name.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['name'])
									entry_id.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['entryId'])
							else:
								try:
									print '{} is NOT EQUAL to {}'.format(i, jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['name'])
									print 'STORING NEW FOOD ITEM INFORMATION........'
									print type(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['name'])
									new_item_description.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['description'])
									new_item_price.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['price'])
									new_item_entry_name.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['name'])
									new_item_entry_id.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['entryId'])
									new_item_name.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['name'])
									new_item_res.append(l) # To keep track of food item belonging to what restaurant
								except Exception as e:
									raise e
								else:
									new_item_description.append('Not Available')
									new_item_price.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['price'])
									new_item_entry_name.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['name'])
									new_item_entry_id.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['entryId'])
									new_item_name.append(jsonData2['response']['menu']['menus']['items'][0]['entries']['items'][j]['entries']['items'][k]['name'])
									new_item_res.append(l)
							
			
				
			
			

if __name__ == "__main__":
	des = GetDescriptorWords()
	coord_latlng = des.getlatLng("AIzaSyAIA51ih8GL9xuWoUCCwwz_y1DIcPPAO5M")
	des.getMenu(coord_latlng)
