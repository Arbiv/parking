import datetime
import time
import hashlib
import random

#############
# Constants #
#############

INSIDE_SPOTS_COUNT = 5
OUTSIDE_SPOTS_COUNT = 11
GUEST_PLATE = 9999999

############
# Timezone #
############

class Ist(datetime.tzinfo):
    def dst(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "IST-02IDT"

    def utcoffset(self, dt):
        return datetime.timedelta(hours=2)


##############
# Exceptions #
##############

class ParkingException(Exception):
    pass

class DoubleBookingException(ParkingException):
    pass

class NoFreeSpaceException(ParkingException):
    pass

class SpotTakenException(ParkingException):
    pass

class SpotNotTakenException(ParkingException):
    pass

class SpotReservedException(ParkingException):
    pass

class SpotNotReservedException(ParkingException):
    pass

#############
# Functions #
#############

def make_name(user):
    return user.nickname().split('@')[0].replace('.', ' ').title()
    
def is_downtime():
    current_time = datetime.datetime.now(Ist())
    minimum_time = current_time.replace(hour=5, minute=45, second=0, microsecond=0)
    seed_base = current_time.strftime("Year: %Y Month: %m Day:%d")
    seed = int(hashlib.new("md5", seed_base).hexdigest(), 16) % 1024
    randomizer = random.Random(seed)
    return not (current_time - minimum_time).total_seconds() > 60 * randomizer.randint(0,60)
