# coding=utf-8
#This parses the foodspotter website.
try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup
from googleplaces import GooglePlaces
import urllib2
import json
import sys
import os
from dotenv import load_dotenv

#Load old site

dotenv_path = ".env"
load_dotenv(dotenv_path, verbose=True)


from trans_db import *

myDb = TransDBConnector()
myDb.connect()
print("Connected")

API_KEY = os.environ.get("GOOGLPLACESAPI")
print("API Key: " , API_KEY)


#This is going to connect to the DB. and compile all records into a new table foods_kc
def collectAndPutIntoFoods():
	# This gets all the food items (I want this whole thing as a list)
	getAllFoodItems = getFoodItems()
	print("All food items: " , getAllFoodItems)
	completeList = []
	#For each food item object
	for foodItem in getAllFoodItems:
		print("Evaluating foodItem: " , foodItem)
		print("gett rest: " , foodItem.id)
		foodRestaurant = myDb.get_restaurant(foodItem.restidLink)
		print("Restaurant:")
		print(foodRestaurant)
		foodAddress = myDb.get_address(foodItem.restidLink)
		print("Address:")
		print(foodAddress)
		#deliveryInfo = get_del_info() #This should get the info. We are going to feed in the food name, rest name, 
		#Ignoring this for right now.
		# id, foodname, foodpic, address (complete), 

		phone = getPhoneFromAddress(foodAddress.add1,foodAddress.city,foodAddress.state,foodRestaurant.name.split(' ')[0])
		print("Phone num: " , phone)

		myFood = FoodComplete(foodItem.id,foodItem.name,foodItem.picLink,foodAddress.getString(),foodRestaurant.name,0,0,0)

		myDb.add_complete_food(myFood.descrip,myFood.foodPic,myFood.location,myFood.name,myFood.price,myFood.delivery,phone)

#Keyword is just the first word in the rest name. 
def getPhoneFromAddress(address,city,state,keyword,key=API_KEY):
	try:
		restId = getPlaceID(address,city,state,keyword,key=key)
		print("Restaurant id: " , restId)
		return getPhoneNumberFromPlaceID(restId,key=key)
	except:
		return ""
def getPhoneNumberFromPlaceID(placeId,key=API_KEY):
	print("placeID",placeId)
	AUTH_KEY = key
	MyUrl = ('https://maps.googleapis.com/maps/api/place/details/json'
	           '?placeid=%s'
	           '&key=%s') % (placeId, AUTH_KEY)
	print(MyUrl)
	#grabbing the JSON result
	response = urllib2.urlopen(MyUrl,timeout=10)
	jsonRaw = response.read()
	jsonData = json.loads(jsonRaw)
	print("data1:")
	print(jsonData)
	print("Phone number:")
	print(jsonData['result'])
	print "Address::::::",jsonData['result']['formatted_phone_number']
	return jsonData['result']['formatted_phone_number'].replace("(","").replace(")","").replace(" ","").replace("-","")
	#return "4176934622"


#https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=39.0527512,-94.59118&radius=10&type=restaurant&keyword=beer&key=AIzaSyBi7krdji6Ys6sSNSdw2z5FeyCfR1iNimA


def getPlaceID(address,city,state,keyword,key=API_KEY):
	#making the url
	AUTH_KEY = key
	LOCATION = address.replace(' ','+')+","+str(city).replace(' ','+')+","+str(state)
	print("Location:", LOCATION)
	MyUrl = ('https://maps.googleapis.com/maps/api/geocode/json'
	           '?address=%s'
	           '&key=%s') % (LOCATION, AUTH_KEY)

	print(MyUrl)
	#grabbing the JSON result
	response = urllib2.urlopen(MyUrl,timeout=10)
	jsonRaw = response.read()
	jsonData = json.loads(jsonRaw)

	print("First results:")
	print(jsonData['results'][0])
	print(jsonData['results'][0]['geometry'])

	latPos = jsonData['results'][0]['geometry']['location']['lat']
	lngPos = jsonData['results'][0]['geometry']['location']['lng']
	myPos = str(latPos)+","+str(lngPos)

	MyUrl = ('https://maps.googleapis.com/maps/api/place/nearbysearch/json'
	           '?location=%s'
	           '&radius=10&type=restaurant&keyword=%s'
	           '&key=%s') % (myPos, keyword,AUTH_KEY)
	print(MyUrl)

	response = urllib2.urlopen(MyUrl,timeout=10)
	jsonRaw = response.read()
	jsonData = json.loads(jsonRaw)

	print("Second results:")
	print(jsonData)
	print(jsonData['results'][0]['place_id'])

	placeId = jsonData['results'][0]['place_id']


	return placeId

#This should return a list of foodItem objects.
def getFoodItems():
	#print myDb.db.child("fooditem").get().val()
	#print list(myDb.db.child("fooditem").get().val())
	all_users = myDb.db.child("fooditem").get()
	retVal = []
	for user in all_users.each():
	    #print(user.key()) # Morty
	    #print(user.val()) # {name": "Mortimer 'Morty' Smith"}
	    foodRec = FoodItem()
	    foodRec.unpack(user.val())
	    retVal.append(foodRec)
	print retVal
	return retVal
	#print [FoodItem().unpack(user.val()) for user in myDb.db.child("fooditem").get().each()]
	#return [FoodItem().unpack(user.val()) for user in myDb.db.child("fooditem").get().each()]


#This should make a query into eatstreet and get the API Key and cost associated with this. Note that we need to see for things like minCost as well here
def get_del_info():
	#Okay so the question is how to find the record in the DB. 
	
	pass

if __name__ == "__main__":
	print("Testing method....")
	collectAndPutIntoFoods()

























