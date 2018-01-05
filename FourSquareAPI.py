#  ╔═══╗
#  ║╔═╗║
#  ╚╝╔╝║
#  ──║╔╝
#  ──╔╗
#  ──╚╝    Hungry LLC 
#            Drafted 1/4/2018.
#            Nitin Bhandari

# This method is responsible for pulling restaurants from the FourSquare API and gathering their information as well as menu and inputting them into a backend database.
# It is intended to be run as a single script to gather restaurant/menu information.
# Foursquare API Link: https://developer.foursquare.com/docs/api/

import urllib2
import json, requests
import io

###################################################
############# HyperSetting and Params #############
###################################################

FOOD_CAT = '4d4b7105d754a06374d81259'
CLIENT_ID = 'OXOP1HNDEV0NQOXJ3R5RC5GZWSKIFXOJOGA1KDHZXMNNFEJL'
CLIENT_SEC = '1OCNH4GAHSM1OIVYZHISHRRVPM0BSF0OP2PYDQXTCSG4KMLD'

#############################################
############# Support Functions #############
#############################################

#This returns in a list all the ids of restaurants in a city. 
def getAllRestIdsInCity(areasToConsider,lim=1):
	search_url = 'https://api.foursquare.com/v2/venues/search?'
	retVal = []

	for places in areasToConsider:
	    params = dict(
	      categoryId=FOOD_CAT,
	      client_id=CLIENT_ID,
	      client_secret=CLIENT_SEC,
	      near=places,
	      v='20170801',
	      limit=lim
	    )
	    resp = requests.get(url=search_url, params=params)
	    data = json.loads(resp.text)
	    print data
	    print("Option...")
	    retVal = data['response']['venues']
	    #Now each of the ID's are contained in the list here under id
	    #Eg: print data['response']['venues'][0]['id']
	    with io.open('resturant_data.json', 'a+') as outfile:
	        outfile.write(resp.text +"\n") 

	return retVal
  
#############################################
############# Test Functions    #############
#############################################


res_places = ["Kansas City"]#, "Wichita", "Topeka", "Overland Park", "Lawrence", "Olathe", "Lenexa", "Shawnee"
#This gets all the IDs.
resIds = getAllRestIdsInCity(res_places)
#Now use these URLS:
#rest_url = 'https://api.foursquare.com/v2/venues/'4adb44c6f964a520672521e3'
#menu_url = 'https://api.foursquare.com/v2/venues/'4adb44c6f964a520672521e3/menu'

#Use these to get the data for the restaurant as well as the menu data, and ordering information (if possible). 

#Then store all this associated data. 











