#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import shared
from datamodel import *
from random import shuffle
from google.appengine.api import mail

mail_sender = "C4 Parking <c4-parking@appspot.gserviceaccount.com>"
class Clear(webapp2.RequestHandler):
    def get(self):
        if not shared.is_weekend():
            for spot in Spot.all().filter("future = ", False):
                spot.Release()
            self.tossReservationForTomorrow()
		
    def tossReservationForTomorrow(self):
        carMustGetSpot = []
        carInToss = []
        
        #create two list of cars - must get spot and not
        for reservation in TossReservation.all():
            if reservation.car is not None:
                if UserData.all().filter("user =", reservation.car.owner).get().mustGetSpot:
                    carMustGetSpot.append((reservation.car, reservation.preferSpotOutside))
                else:
                    carInToss.append((reservation.car, reservation.preferSpotOutside))
        
        # random the list of all cars don't must get spot
        shuffle(carInToss)
        
        #allocate spots for all users
        for spot in Spot.all().filter("future = ", False).order("outside"):
            if spot.free:
                if len(carMustGetSpot) != 0:
                    index = 0 #index of car in toss
                    while((spot.outside == False) and (index < len(carMustGetSpot)) and (carMustGetSpot[index][1])):
                        index = index + 1
                    if index < len(carMustGetSpot): # if the we found index of car in carMustGetSpot
                        spot.Take(carMustGetSpot.pop(index)[0])
                elif len(carInToss) != 0:
                    index = 0 #index of car in toss
                    while((spot.outside == False) and (index < len(carInToss)) and (carInToss[index][1])):
                        index = index + 1
                    if index < len(carInToss): # if we found index of car in carInToss
                        spot.Take(carInToss.pop(index)[0])
                        
        #delete all TossReservation
        for toss in TossReservation.all():
            if toss.car is not None:
                toss.Reserve(False)
        
        #send mails for users that have spot
        for spot in Spot.all().filter("future = ", False):
            if not spot.free and spot.car is not None and spot.car.plate != GUEST_PLATE:
                msgSubject = ""
                msgBody = ""
                if spot.outside:
                    msgSubject = "Parking Reservation - Accepted (Outside)"
                    msgBody = """
                    Congratulations!
                    Your spot reservation for today was accepted.
                    Please park outside at 'Moshe Salti' Parking Lot.
                    
                    Have a nice day! :)
                    """
                else:
                    msgSubject = "Parking Reservation - Accepted (Inside)"
                    msgBody = """
                    Congratulations!
                    Your spot reservation for today was accepted.
                    Please park inside. Authorized your car number before coming, lobby phone#: 03-607-1812.
                    
                    Have a nice day! :)
                    """
                mail.send_mail(sender=mail_sender, to=spot.car.owner, subject=msgSubject, body=msgBody)
        
        #send mails for users that don't have spots       
        for car in carInToss:
            msgSubject = "Parking Reservation - Rejected!"
            msgBody = """
            Sorry!
            Your spot reservation for today was rejected.
            Try next time.
            
            Have a nice day! :)
            """
            mail.send_mail(sender=mail_sender, to=car.owner, subject=msgSubject, body=msgBody)
            

class InitSpots(webapp2.RequestHandler):
    def get(self):

        self.response.out.write('Removing all spots...')
        for spot in Spot.all():
            spot.delete()
        self.response.out.write(' OK!\r\n<br>')

        self.response.out.write('Creating %d inside spots...' % shared.INSIDE_SPOTS_COUNT)
        for i in xrange(shared.INSIDE_SPOTS_COUNT):
            spot = Spot.get_or_insert(str(i+1), number=i+1, free=True, reserved=None, car=None, comments='', future=False, outside=False)
            spot.put()
        self.response.out.write(' OK!\r\n<br>')

        self.response.out.write('Creating %d outside spots...' % shared.OUTSIDE_SPOTS_COUNT)
        for j in xrange(shared.OUTSIDE_SPOTS_COUNT):
            i = shared.INSIDE_SPOTS_COUNT + j
            spot = Spot.get_or_insert(str(i+1), number=i+1, free=True, reserved=None, car=None, comments='', future=False, outside=True)
            spot.put()
        self.response.out.write(' OK!\r\n<br>')

class InitCars(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('Removing all cars...')
        for car in Car.all():
            car.delete()
        self.response.out.write(' OK!\r\n<br>')

class MigrateConfigSchema(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('Upgrading configurations...')
        updated = UserData.MigrateUserDataSchema()
        self.response.out.write(' OK!\r\n<br>')
        self.response.out.write('Upgraded %d configurations!' % updated)

class TestTime(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(shared.get_current_time())

app = webapp2.WSGIApplication([
                               ('/tasks/clear', Clear),
                               ('/tasks/initspots', InitSpots),
                               ('/tasks/initcars', InitCars),
                               ('/tasks/migrateconfigschema', MigrateConfigSchema),
                               ('/tasks/testtime', TestTime),
                               ],
                              debug=True)
