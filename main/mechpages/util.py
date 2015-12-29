from django.core.validators import validate_email
from ipware.ip import get_ip
from django.contrib.staticfiles.templatetags.staticfiles import static
import numpy as np
import random
import string
import requests
from geopy.distance import vincenty
from main import settings
from builtins import range, len, dict, ord, Exception, str, min, int, map, sum
from math import radians, cos, sin, asin, sqrt
from scipy import spatial
from django.http import HttpResponse
from django.core.cache import cache
from mechpages.models import UserProfile, Location, NotifyAvailability, Review, PostAJob


class Del:
    def __init__(self, keep=string.digits):
        self.comp = dict((ord(c), c) for c in keep)

    def __getitem__(self, k):
        return self.comp.get(k)


DD = Del()


def trim_mobile(mobile_number):
    if mobile_number is not None:
        mobile_digits_only = mobile_number.translate(DD)
        if len(mobile_digits_only) == 11:
            return mobile_digits_only
        elif len(mobile_digits_only) == 10:
            mobile_digits_only = '1' + mobile_digits_only
            return mobile_digits_only
        else:
            return None
    else:
        return None


def check_mobile(user, mobile_number):
    if mobile_number is None:
        return HttpResponse("Invalid mobile number<br>(eg: 1 (123) 123-4567)", status=403)
    if mobile_number == user.userprofile.mobile:
        return HttpResponse("Already verified", status=403)
    userprofile = UserProfile.objects.filter(mobile=mobile_number)
    if userprofile.exists():
        return HttpResponse("Mobile number used by another account", status=403)
    type = cache.get(mobile_number + "_type")
    if type is None:
        try:
            url = "https://lookups.twilio.com/v1/PhoneNumbers/" + mobile_number
            r = requests.get(url, dict({'Type': 'carrier'}),
                             auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN))
            cache.set(mobile_number + "_type", r.json().get('carrier').get('type'))
            if r.json().get('carrier').get('type') == 'voip':
                return HttpResponse("Voip numbers not allowed.", status=403)
        except Exception:
            pass
    elif type == 'voip':
        return HttpResponse("Voip numbers not allowed.", status=403)


def get_pin(length=5):
    """ Return a numeric PIN with length digits """
    return random.sample(range(10 ** (length - 1), 10 ** length), 1)[0]


def check_send_attempts(user):
    count = cache.get(str(user) + "_sendpin")
    timeout = cache.get(str(user) + "_sendpin_timeout")
    if count is None:
        cache.set(str(user) + "_sendpin", 1, 12 * 3600)
        count = 1
    if count > 6:
        if timeout is not None:
            return HttpResponse("6 attempts exceeded, please wait 1 hour", status=403)
    elif count > 3:
        if timeout is not None:
            return HttpResponse("3 attempts exceeded, please wait 30 seconds", status=403)


def verify_pin(user, mobile_number, pin):
    count = cache.incr(str(user) + "_verifypin")
    if count > 3:
        cache.set(str(user) + "_verifypin_timeout", 1, 300)
    return pin == cache.get(mobile_number + "_pin")


def check_verify_attempts(user):
    count = cache.get(str(user) + "_verifypin")
    timeout = cache.get(str(user) + "_verifypin_timeout")
    if count is None:
        cache.set(str(user) + "_verifypin", 1, 12 * 3600)
    if timeout is not None:
        return HttpResponse("3 attempts exceeded,<br>please wait 5 minutes", status=404)


def _range(array, lower, upper):
    keys = [r[0] for r in array]
    start = np.searchsorted(keys, lower, side="left")
    end = np.searchsorted(keys, upper, side="right")
    return array[start:end]


# sort only against the first column to increase performance, sorting the pk provides no value
def _sort(array):
    if array.size > 0:
        return array[array[:, 0].argsort()]
    else:
        return array


# there is a good chance this section gets executed needlessly multiple times (ex: when the cache expires and
# multiple threads request for get_all_mechanics_lat_list). might be better to do this via some sort of task service
# Bench Result: Float - 1st. Numpy, 2nd. sorted, 3rd. sortedcontainer
# Bench Result: Decimal - 1st. sorted, 2nd. Numpy, 3rd. sortedcontainer
# Bench Result: Float 10x faster than Decimal
def get_all_mechanics_lat_list():
    all_mechanics_lat_list = cache.get("_all_mechanics_lat_list")
    if all_mechanics_lat_list is None:
        lat_list = Location.objects.values_list('latitude', 'pk').filter(user__userprofile__profile_complete=True)
        all_mechanics_lat_list = _sort(np.array(lat_list))
        # to be enabled when performance is needed
        # cache.set("_all_mechanics_lat_list", all_mechanics_lat_list, 12 * 3600)
        # cache.set("_all_mechanics_lat_list", all_mechanics_lat_list, 600)
    return all_mechanics_lat_list


def get_mechanics_lng_list(list):
    return _sort(np.array(Location.objects.filter(pk__in=[x[1] for x in list]).values_list('longitude', 'pk')))


def get_mechanics_list(sw_lat, sw_lng, ne_lat, ne_lng, skill):
    bound = ne_lat - sw_lat + ne_lng - sw_lng
    if bound <= 8:
        all_mechanics_lat_list = get_all_mechanics_lat_list()
        bounded_mechanics_lat_list = _range(all_mechanics_lat_list, sw_lat, ne_lat)
        bounded_mechanics_list = _range(get_mechanics_lng_list(bounded_mechanics_lat_list), sw_lng, ne_lng)
        bounded_mechanics_objects = Location.objects.filter(pk__in=[x[1] for x in bounded_mechanics_list])
        if skill:
            bounded_with_skill_objects = bounded_mechanics_objects.filter(user__userprofile__skills__pk=skill)
            return bounded_with_skill_objects.values_list('pk', 'latitude', 'longitude', 'radius', 'user')
        return bounded_mechanics_objects.values_list('pk', 'latitude', 'longitude', 'radius', 'user')
    else:
        return []


def get_icon_url_from_user(user):
    try:
        url = user.userprofile.avatar_icon.url
        if url:
            return url
        else:
            print(static('img/profile_default.png'))
            return static('img/profile_default.png')
    except Exception:
        return static('img/profile_default.png')


def get_thumbnail_url_from_user(user):
    print(user)
    try:
        url = user.userprofile.avatar_thumbnail.url
        if url:
            return url
        else:
            print(static('img/profile_default.png'))
            return static('img/profile_default.png')
    except Exception:
        return static('img/profile_default.png')


def get_name_from_user(user):
    name = user.userprofile.name
    if name:
        return name
    else:
        return 'Anonymous'


def get_mechanics_profile(pk):
    user = Location.objects.get(pk=pk).user
    userprofile = user.userprofile
    skills = []
    jobhistory = []
    images = []
    try:
        thumbnail = userprofile.avatar_thumbnail.url
    except Exception:
        thumbnail = static('img/profile_default.png')
    for skill in userprofile.skills.all():
        skills.append(skill.skill)
    for job in user.jobhistory.all():
        jobhistory.append(
            {"company": job.company, "position": job.position, "years": job.years, "description": job.description})
    for image in user.projectimages.all():
        images.append(
            {"title": image.title, "thumbnail": image.image_thumbnail.url, "icon": image.image_icon.url,
             "description": image.description})
    result = [user.name, thumbnail, userprofile.name, skills, userprofile.short_bio, jobhistory, images,
              userprofile.rating, userprofile.rating_count]
    return result


# Calculate the great circle distance between two points on the earth (specified in decimal degrees)
def geopy_vincenty(lat1, lng1, lat2, lng2):
    print(lat1, lng1, lat2, lng2)
    loc1 = (lat1, lng1)
    loc2 = (lat2, lng2)
    # multiplying by 1.3 is the poor people's way to convert to travel distance as opposed to direct distance
    return vincenty(loc1, loc2).miles * 1.3


def get_mechanics_nearest(lat, lng, skill):
    result = []
    # Get mechanics list within a boundary of .5 around the point
    sw_lat = lat - 1.5
    sw_lng = lng - 1.5
    ne_lat = lat + 1.5
    ne_lng = lng + 1.5
    mechanics_list = get_mechanics_list(sw_lat, sw_lng, ne_lat, ne_lng, skill)
    if mechanics_list:
        if len(mechanics_list) == 1:
            nearest = [0]
        else:
            array = [(x[1], x[2]) for x in mechanics_list]
            kd_tree = spatial.cKDTree(array)
            nearest = kd_tree.query((lat, lng), min(5, len(array)))[1]
        for i in nearest:
            skills = []
            pk = mechanics_list[int(i)][0]
            user = Location.objects.get(pk=mechanics_list[int(i)][0]).user
            userprofile = user.userprofile
            name = get_name_from_user(user)
            miles = "%.1f" % geopy_vincenty(lat, lng, mechanics_list[int(i)][1], mechanics_list[int(i)][2])
            bio = userprofile.short_bio
            icon = get_icon_url_from_user(user)
            for skill in userprofile.skills.all():
                skills.append(skill.skill)
            rating = userprofile.rating
            ratingcount = userprofile.rating_count
            result.append((pk, name, miles, bio, icon, skills, rating, ratingcount))
    return result


def check_email(email):
    try:
        validate_email(email)
        if NotifyAvailability.objects.filter(email=email).exists():
            return HttpResponse("Already subscribed", status=403)
    except Exception:
        return HttpResponse("Not a valid e-mail", status=404)


def check_send_rate(request, send_event=False):
    ip = get_ip(request)
    if ip is not None:
        name = str(ip)
    else:
        return False
    count = cache.get(name + "_email_count", 0)
    timeout = cache.get(name + "_email_timeout")
    if timeout:
        return False
    if send_event:
        count += 1
        cache.set(name + "_email_count", count, 10 * 60)
    if count >= 5 and send_event:
        cache.set(name + "_email_timeout", 1, 10 * 60)
    return True


def get_rating_average_and_count(pk):
    ratings = Review.objects.filter(mechanic=pk).values_list('rating', flat=True)
    count = len(ratings)
    return [int(sum(ratings) / count / 5 * 100), count]


def get_name_icon(user):
    if user.userprofile.name:
        name = user.userprofile.name
    else:
        name = "Anonymous"
    if user.userprofile.avatar:
        icon = user.userprofile.avatar_icon.url
    else:
        icon = static('img/profile_default.png')
    return {"name": name, "icon": icon}


def get_all_requests_lat_list():
    all_requests_lat_list = cache.get("_all_requests_lat_list")
    if all_requests_lat_list is None:
        lat_list = PostAJob.objects.values_list('latitude', 'pk').filter(done=False)
        all_requests_lat_list = _sort(np.array(lat_list))
        # to be enabled when performance is needed
        # cache.set("_all_requests_lat_list", all_requests_lat_list, 600)
    return all_requests_lat_list


def get_requests_lng_list(list):
    return _sort(np.array(PostAJob.objects.filter(pk__in=[x[1] for x in list]).values_list('longitude', 'pk')))


def get_requests_list(sw_lat, sw_lng, ne_lat, ne_lng, skill):
    bound = ne_lat - sw_lat + ne_lng - sw_lng
    if bound <= 8:
        all_requests_lat_list = get_all_requests_lat_list()
        bounded_requests_lat_list = _range(all_requests_lat_list, sw_lat, ne_lat)
        bounded_requests_list = _range(get_requests_lng_list(bounded_requests_lat_list), sw_lng, ne_lng)
        bounded_requests_objects = PostAJob.objects.filter(pk__in=[x[1] for x in bounded_requests_list])
        if skill:
            bounded_with_skill_objects = bounded_requests_objects.filter(skill__pk=skill)
            return bounded_with_skill_objects.values_list('pk', 'latitude', 'longitude', 'user')
        return bounded_requests_objects.values_list('pk', 'latitude', 'longitude', 'user')
    else:
        return []


def get_requests_nearest(lat, lng, skill):
    result = []
    # Get request list within a boundary of 1.5 around the point
    sw_lat = lat - 1.5
    sw_lng = lng - 1.5
    ne_lat = lat + 1.5
    ne_lng = lng + 1.5
    requests_list = get_requests_list(sw_lat, sw_lng, ne_lat, ne_lng, skill)
    if requests_list:
        if len(requests_list) == 1:
            nearest = [0]
        else:
            array = [(x[1], x[2]) for x in requests_list]
            kd_tree = spatial.cKDTree(array)
            nearest = kd_tree.query((lat, lng), min(5, len(array)))[1]
        for i in nearest:
            pk = requests_list[int(i)][0]
            obj = PostAJob.objects.get(pk=requests_list[int(i)][0])
            name = get_name_from_user(obj.user)
            miles = "%.1f" % geopy_vincenty(lat, lng, requests_list[int(i)][1], requests_list[int(i)][2])
            icon = get_icon_url_from_user(obj.user)
            car = obj.car_year + " - " + obj.car_make + " " + obj.car_model
            result.append((pk, name, miles, obj.comment[:300], icon, obj.skill.skill, car))
    return result


def get_request(pk):
    obj = PostAJob.objects.get(pk=pk)
    user = obj.user
    try:
        thumbnail = user.userprofile.avatar_thumbnail.url
    except Exception:
        thumbnail = static('img/profile_default.png')
    car = obj.car_year + " - " + obj.car_make + " " + obj.car_model
    result = [user.name, get_name_from_user(user), obj.comment, thumbnail, obj.skill.skill, car]
    return result
