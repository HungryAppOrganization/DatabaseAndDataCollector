import urllib2
import json, requests
import io

url = 'https://api.foursquare.com/v2/venues/search?'

res_places = ["Kansas City", "Wichita", "Topeka", "Overland Park", "Lawrence", "Olathe", "Lenexa", "Shawnee"]

for places in res_places:
	
	params = dict(
  	categoryId='54135bf5e4b08f3d2429dfe1',
  	client_id='OXOP1HNDEV0NQOXJ3R5RC5GZWSKIFXOJOGA1KDHZXMNNFEJL',
  	client_secret='1OCNH4GAHSM1OIVYZHISHRRVPM0BSF0OP2PYDQXTCSG4KMLD',
  	near=places,
  	v='20170801',
  	limit=50
	)
	resp = requests.get(url=url, params=params)
	data = json.loads(resp.text)
	print data
	with io.open('resturant_data.json', 'a+') as outfile:
		outfile.write(resp.text) 
	
