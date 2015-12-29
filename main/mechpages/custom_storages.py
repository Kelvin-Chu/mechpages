# https://www.caktusgroup.com/blog/2014/11/10/Using-Amazon-S3-to-store-your-Django-sites-static-and-media-files/
# http://stackoverflow.com/questions/31357353/using-cloudfront-with-django-s3boto
from builtins import super
from django.conf import settings
from storages.backends.s3boto import S3BotoStorage


# class StaticStorage(S3BotoStorage):
#     location = settings.STATICFILES_LOCATION


class MediaStorage(S3BotoStorage):
    location = settings.MEDIAFILES_LOCATION

    ## PRODUCTION SETTINGS
    # def __init__(self, *args, **kwargs):
    #     kwargs['custom_domain'] = settings.AWS_CLOUDFRONT_DOMAIN
    #     super(MediaStorage, self).__init__(*args, **kwargs)
