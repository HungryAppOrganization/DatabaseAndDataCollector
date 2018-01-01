import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()
 
class RestaurantDB(Base):
    __tablename__ = 'restaurant'
    id = Column(Integer,primary_key=True)
    address = Column(String(250))
    name = Column(String(250))
    number = Column(String(250))
    city = Column(String(250))
    hours = Column(String(250))

class MenuItemDB(Base):
    __tablename__ = 'menuitem'
    id = Column(Integer, primary_key=True)

    name = Column(String(250))
    cost = Column(Integer)
    picture = Column(String(250))

    calorie = Column(Integer)

    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
    restaurant = relationship(RestaurantDB)
# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite:///data/csv_test2.db')
 
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)