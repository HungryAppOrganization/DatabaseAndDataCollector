#This file prints out all the DB entries.


import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_scrapper_vers_1 import RestaurantDB, MenuItemDB

# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite:///data/csv_test2.db')
 
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.

session = sessionmaker()
session.configure(bind=engine)
s = session()

vals = s.query(RestaurantDB).all()
print("Restaurants:")
for ele in vals:
	print "\t",ele.name
print("Menu Items:")
vals = s.query(MenuItemDB).all()
for ele in vals:
	print "\t",ele.name, ele.picture