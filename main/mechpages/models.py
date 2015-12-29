import uuid
import os
import urllib.response
import urllib.request
import urllib.parse
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from builtins import Exception, str, super, object
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.deconstruct import deconstructible
from allauth.account.signals import user_signed_up
from pilkit.processors import Transpose, ResizeToFill
from datetime import datetime
from imagekit.models import ProcessedImageField, ImageSpecField
from main import settings

STATE_CHOICES = (
    ('-', 'State'), ('AL', 'AL'), ('AK', 'AK'), ('AZ', 'AZ'), ('AR', 'AR'), ('CA', 'CA'), ('CO', 'CO'), ('CT', 'CT'),
    ('DE', 'DE'), ('DC', 'DC'), ('FL', 'FL'), ('GA', 'GA'), ('HI', 'HI'), ('ID', 'ID'), ('IL', 'IL'), ('IN', 'IN'),
    ('IA', 'IA'), ('KS', 'KS'), ('KY', 'KY'), ('LA', 'LA'), ('ME', 'ME'), ('MD', 'MD'), ('MA', 'MA'), ('MI', 'MI'),
    ('MN', 'MN'), ('MS', 'MS'), ('MO', 'MO'), ('MT', 'MT'), ('NE', 'NE'), ('NV', 'NV'), ('NH', 'NH'), ('NJ', 'NJ'),
    ('NM', 'NM'), ('NY', 'NY'), ('NC', 'NC'), ('ND', 'ND'), ('OH', 'OH'), ('OK', 'OK'), ('OR', 'OR'), ('PA', 'PA'),
    ('RI', 'RI'), ('SC', 'SC'), ('SD', 'SD'), ('TN', 'TN'), ('TX', 'TX'), ('UT', 'UT'), ('VT', 'VT'), ('VA', 'VA'),
    ('WA', 'WA'), ('WV', 'WV'), ('WI', 'WI'), ('WY', 'WY'))


def download_image(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0'}
    r = urllib.request.Request(url, headers=headers)
    request = urllib.request.urlopen(r, timeout=10)
    image_data = BytesIO(request.read())
    img = Image.open(image_data)
    if valid_img(img):
        return img
    else:
        raise Exception('An invalid image was detected when attempting to save a avatar!')


def valid_img(img):
    type = img.format
    if type in ('GIF', 'JPEG', 'JPG', 'PNG'):
        try:
            return True
        except Exception:
            return False
    else:
        return False


@deconstructible
class RandomFileName(object):
    def __init__(self, path):
        self.path = os.path.join(path + datetime.now().strftime("%Y/%m/%d"), "%s%s")

    def __call__(self, _, filename):
        extension = os.path.splitext(filename)[1]
        return self.path % (uuid.uuid4(), extension)


# this model is automatically populated via 0002_load_init_data.py
class SkillChoice(models.Model):
    skill = models.CharField(max_length=100, blank=False)

    def __str__(self):
        return self.skill

    class Meta:
        ordering = ['skill']


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    avatar = ProcessedImageField(upload_to=RandomFileName('avatars/'), processors=[Transpose(Transpose.AUTO)],
                                 format='JPEG', options={'quality': 100}, blank=True)
    avatar_icon = ImageSpecField(source='avatar', processors=[ResizeToFill(50, 50)], format='JPEG',
                                 options={'quality': 75})
    avatar_thumbnail = ImageSpecField(source='avatar', processors=[ResizeToFill(250, 250)], format='JPEG',
                                      options={'quality': 100})
    mobile = models.CharField(max_length=16, unique=True, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=2, choices=STATE_CHOICES, default='-')
    zip = models.CharField(max_length=10, blank=True)
    car_make = models.CharField(max_length=50, blank=True)
    car_model = models.CharField(max_length=50, blank=True)
    car_year = models.CharField(max_length=4, blank=True)
    review_points = models.PositiveIntegerField(default=0, blank=False)
    is_mechanic = models.BooleanField(default=False, blank=False)
    mobile_verified = models.BooleanField(default=False, blank=False)
    short_bio = models.TextField(max_length=160, blank=True)
    add_info = models.TextField(max_length=1000, blank=True)
    skills = models.ManyToManyField(SkillChoice)
    profile_complete = models.BooleanField(default=False, blank=False)
    publish = models.BooleanField(default=False, blank=False)
    project_limit = models.PositiveIntegerField(default=9, blank=False)
    rating = models.PositiveSmallIntegerField(default=0, blank=False)
    rating_count = models.PositiveIntegerField(default=0, blank=False)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return "%s's profile" % self.user

    def save(self, url='', *args, **kwargs):
        if self.avatar == '' and url != '':
            image = download_image(url)
            try:
                filename = urllib.parse.urlparse(url).path.split('/')[-1]
                self.avatar = filename
                tempfile = image
                tempfile_io = BytesIO()
                tempfile.save(tempfile_io, format=image.format)
                self.avatar.save(filename, ContentFile(tempfile_io.getvalue()), save=False)
            except Exception:
                print("Error trying to save model: saving image failed: " + str(Exception))
                pass
        super(UserProfile, self).save(*args, **kwargs)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def handle_user_save(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(user_signed_up)
def user_signed_up_(request, user, sociallogin=None, **kwargs):
    if sociallogin:
        url = urllib.request.urlopen(sociallogin.account.get_avatar_url()).geturl()
        if url:
            try:
                user.userprofile.save(url=url)
            except Exception:
                pass
        if sociallogin.account.provider == 'twitter':
            name = sociallogin.account.extra_data['name']
            user.userprofile.name = '%s' % name

        if sociallogin.account.provider == 'facebook':
            user.userprofile.name = '%s %s' % (
                sociallogin.account.extra_data['first_name'], sociallogin.account.extra_data['last_name'])
    user.userprofile.save()
    user.name = 100000 + user.pk
    user.save()


class MobileNumber(models.Model):
    mobile = models.CharField(max_length=16, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return self.mobile


class ProjectImage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="projectimages")
    title = models.CharField(max_length=50, blank=True)
    image = ProcessedImageField(upload_to=RandomFileName('projects/images/'), processors=[Transpose(Transpose.AUTO)],
                                format='JPEG', options={'quality': 100})
    image_icon = ImageSpecField(source='image', processors=[ResizeToFill(56, 42)], format='JPEG',
                                options={'quality': 75})
    image_thumbnail = ImageSpecField(source='image', processors=[ResizeToFill(640, 480)], format='JPEG',
                                     options={'quality': 100})
    description = models.TextField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return self.image.name


class JobHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="jobhistory")
    company = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    years = models.CharField(max_length=2, blank=True)
    description = models.TextField(max_length=2000, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return "%s at %s" % (self.user, self.company)


class Location(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, related_name="location")
    latitude = models.FloatField(blank=False)
    longitude = models.FloatField(blank=False)
    radius = models.CharField(max_length=20, blank=False)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return "%s at %s,%s with radius %s" % (self.user, self.latitude, self.longitude, self.radius)


class NotifyAvailability(models.Model):
    email = models.EmailField(blank=False, unique=True)
    latitude = models.FloatField(blank=False)
    longitude = models.FloatField(blank=False)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return "%s at %s,%s with radius %s" % (self.user, self.latitude, self.longitude, self.radius)


class Review(models.Model):
    mechanic = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="review", blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="reviewer", blank=False)
    rating = models.PositiveIntegerField(blank=False)
    comment = models.TextField(max_length=2000, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return "%s: %s reviewed %s" % (str(self.id), self.user, self.mechanic)


class PostAJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="postajob")
    latitude = models.FloatField(blank=False)
    longitude = models.FloatField(blank=False)
    car_make = models.CharField(max_length=50, blank=False)
    car_model = models.CharField(max_length=50, blank=False)
    car_year = models.CharField(max_length=4, blank=False)
    comment = models.TextField(max_length=2000, blank=False)
    skill = models.ForeignKey(SkillChoice, blank=False)
    done = models.BooleanField(default=False, blank=False)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        ordering = ['done', '-timestamp']

    def __str__(self):
        return "%s looking for %s" % (self.user, self.skill)

