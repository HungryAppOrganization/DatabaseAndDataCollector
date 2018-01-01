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
webSiteLink = "data/all_of_website.html"

dotenv_path = ".env"
load_dotenv(dotenv_path, verbose=True)

API_KEY = os.environ.get("GOOGLPLACESAPI")


#Or all_of_website_kc.html

filer = open(webSiteLink, 'r')
text = filer.read()
filer.close()

from trans_db import *

myDb = TransDBConnector()
myDb.connect()
print("Connected")

def GoogPlac(address,city,state,key=API_KEY):
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
  print "Address::::::",jsonData['results'][0]['formatted_address']
  return jsonData['results'][0]['formatted_address']

  #print jsonData['results']
  #return jsonData
def addGooglePlaceToDB(addressStr,cityStr,stateStr,placeName):
	myVal = GoogPlac(addressStr,cityStr,stateStr).split(',')
	#5 is if just 1, 6 is 2, 7 is three
	a = 0
	add1 = ""
	add2 = ""
	add3 = ""
	if len(myVal) >= 4:
		add1 = myVal[0]
		print("add1: " , add1)
		a = 1
	if len(myVal) >= 5:
		add2 = myVal[1]
		print("add2: " , add2)
		a = 2
	if len(myVal) >= 6:
		add3 = myVal[2]
		print("add3: " , add3)
		a = 3
	city = myVal[a]
	state = myVal[a+1].split(" ")[-2]
	zipa = myVal[a+1].split(" ")[-1]

	print("Add1:",add1,city,state,zipa,add2,add3)


	return myDb.addAddress(add1,city,state,zipa,add2,add3,name=placeName)


parsed_html = BeautifulSoup(html)
#print(parsed_html.body.find('div',{'class':'sightinglist clearfix'}))
myBody = parsed_html.body.find('div',{'class':'sightinglist clearfix'})
limit = 5
i = 0
for food_item in myBody.findAll('div',{'class':'show-card'}):
	#break
	#print food_item
	#print("Round two")
	adId = 0
	try:
		picLink = food_item.find('img',{'class':"photo"})['src']
	except:
		picLink = ""
	try:
		foodName = food_item.find('a',{'class':'food'})['title']
	except:
		foodName = ""
	try:
		placeName = food_item.find('a',{'class':'place'})['title']
	except:
		placeName = ""
	try:
		addressName = food_item.find('span',{'class':'tooltip'})['data-title']
		address = addressName.split('<br>')[0]
		city = addressName.split('<br>')[1].split(", ")[0]
		state = addressName.split('<br>')[1].split(", ")[1][0:2]
	#If this all exists, we are going to save the address.

	#self.addAddress(address,city,state)
	#try:
		print("Adding rest id...")
		restId = addGooglePlaceToDB(address,city,state,placeName)
		print('RestID: ' , restId)
		

	except Exception as e:
		addressName = ""
		address = ""
		city = ""
		state = ""
		print("Unexpected error:", sys.exc_info()[0])
		print(e)
	    	#raise

	print("Foodname\n")
	print(foodName)
	print(picLink)
	print(placeName)
	print(address)
	print(city)
	print(state)
	i += 1
	#if (i >= limit):
	#	break
	restPlaceId = myDb.addRestaurant(placeName,restId,"")

	myDb.addFoodItem(foodName,picLink,restPlaceId)
	#Add the restaurant.



	#print food_item.find('div',{"class":'guide'})
	#break





























