import json, requests
#import pyfoursquare as fs

url = 'https://api.foursquare.com/v2/venues/search?'

params = dict(
  categoryId='4d4b7105d754a06374d81259',
  client_id='OXOP1HNDEV0NQOXJ3R5RC5GZWSKIFXOJOGA1KDHZXMNNFEJL',
  client_secret='1OCNH4GAHSM1OIVYZHISHRRVPM0BSF0OP2PYDQXTCSG4KMLD',
  near='Kansas+City',
  v='20170801',
  limit=100
)

resp = requests.get(url=url, params=params)
data = json.loads(resp.text)
data = json.dumps(data)
print data