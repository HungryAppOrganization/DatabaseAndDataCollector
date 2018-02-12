#  #######
#  # ### #
#  ### # #
#      # #
#      ###        Hungry LLC 
#                 Drafted 2/6/2018.
#      ###        Nitin Bhandari

# This code is responsible for fetching the tags/ingridents of the food items. Input is a .csv db file where we pick up the food item
# name the restuarant name and use a web scrapper/API to accomplish the task

import numpy as np
import pandas as pd
import requests
import urllib
import json
import googlemaps
from datetime import datetime
import time


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

	# This method id responsible to get the coordinates of the restuarants using GoogleMapsAPI
	def getlatLng(self, api):
		base_url = "https://maps.googleapis.com/maps/api/geocode/json?"
		addressList = [x for x in self.res_add]
		coord = []
		latlng = []
		for i in range(0, 2):			#Change the loop to for address in addresses and replace the addressList[i] with address in GeoURL
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
	
	# This method is responsible for getting the menu of the restuarant
	def getMenu(self, coord):
		FOOD_CAT = '4d4b7105d754a06374d81259'
		CLIENT_ID = 'OXOP1HNDEV0NQOXJ3R5RC5GZWSKIFXOJOGA1KDHZXMNNFEJL'
		CLIENT_SEC = '1OCNH4GAHSM1OIVYZHISHRRVPM0BSF0OP2PYDQXTCSG4KMLD'

		search_url = "https://api.foursquare.com/v2/venues/search?"
		base_menu_url = "https://api.foursquare.com/v2/venues/"
		ll = []
		
		
		for i in coord:
			ll.append(str(i[0])+","+str(i[1]))
		ll = pd.Series(ll)
		print ll
		
		res_id = []

		for i in ll:
			venue_url = search_url + "ll=" + i + "&client_id=" + CLIENT_ID + "&client_secret=" + CLIENT_SEC + "&category_id=" + FOOD_CAT+ "&v=20170801"
			print venue_url
			response = urllib.urlopen(venue_url)
			jsonRaw = response.read()
			jsonData = json.loads(jsonRaw)
			id_res = str(jsonData['response']['venues'][0]['id'])
			res_id.append(id_res)
			print res_id
			menu_url = base_menu_url + id_res + '/menu?' + "&client_id=" + CLIENT_ID + "&client_secret=" + CLIENT_SEC + "&v=20170801"
			print menu_url
			resp = urllib.urlopen(menu_url)
			jsonRaw2 = resp.read()
			jsonData2 = json.loads(jsonRaw2)
			
			
	    


if __name__ == "__main__":
	des = GetDescriptorWords()
	coord_latlng = des.getlatLng("AIzaSyAIA51ih8GL9xuWoUCCwwz_y1DIcPPAO5M")
	print coord_latlng
	des.getMenu(coord_latlng)
