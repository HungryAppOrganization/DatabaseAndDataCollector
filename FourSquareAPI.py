#  #######
#  # ### #
#  ### # #
#      # #
#      ###        Hungry LLC 
#                 Drafted 1/4/2018.
#      ###        Nitin Bhandari

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

#This returns in a list all the ids, names, contact, address of restaurants in a city. 
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
	    venList = data['response']['venues']
	    
	    retVal = []
	    names = [] 
	    contact = []
	    loc = []
	    latlong =[]

	    for item in venList:
	    	retVal.append(item['id'])
	    	names.append(item['name'])
	    	contact.append(item['contact']['formattedPhone'])
	    	loc.append(item['location']['formattedAddress'])
	    	latlong.append(str(item['location']['lat']) + ',' + str(item['location']['lng']))
	    #Now each of the ID's are contained in the list here under id
	    #Eg: print data['response']['venues'][0]['id']
	    with io.open('resturant_data.json', 'a+') as outfile:
	        outfile.write(resp.text +"\n")

		return retVal,names,contact,loc,latlong

#This returns menu of the resturants

def getResMenu(res_ID):

	res_Menu = []
	for ID in res_ID:
		menu_url = 'https://api.foursquare.com/v2/venues/'+res_ID+'/menu'
		params = dict(
	      categoryId=FOOD_CAT,
	      client_id=CLIENT_ID,
	      client_secret=CLIENT_SEC,
	      v='20170801'
	    )
		resp = requests.get(url=menu_url, params=params)
		data = json.loads(resp.text)
		menuList = data['response']['menu']['menus']
		res_Menu.append(menuList)
	return res_Menu


#############################################
############# Test Functions    #############
#############################################


res_places = ["Kansas City"]#, "Wichita", "Topeka", "Overland Park", "Lawrence", "Olathe", "Lenexa", "Shawnee"
#This gets all the IDs.
resIds, resNames, resContact, resAddress, resLatLong = getAllRestIdsInCity(res_places)
print("My venue ids I can use: ")
for i in resIds:
	print(i)
	resMenu = getResMenu(i)
	print resMenu

#Now use these URLS:
#rest_url = 'https://api.foursquare.com/v2/venues/'4adb44c6f964a520672521e3'           								DONE
#menu_url = 'https://api.foursquare.com/v2/venues/'4adb44c6f964a520672521e3/menu'	   								DONE

#Use these to get the data for the restaurant as well as the menu data, and ordering information (if possible). 	DONE

#Then store all this associated data. 																				????











