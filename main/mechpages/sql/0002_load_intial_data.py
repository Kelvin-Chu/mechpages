# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def load_data(apps, schema_editor):
    skillchoice = apps.get_model("mechpages", "SkillChoice")
    skillchoice(skill='Air Conditioning').save()
    skillchoice(skill='Batteries').save()
    skillchoice(skill='Belts & Hoses').save()
    skillchoice(skill='Body & Paint').save()
    skillchoice(skill='Brakes').save()
    skillchoice(skill='Clutch & Transmission').save()
    skillchoice(skill='Drivelines').save()
    skillchoice(skill='Electrical Systems').save()
    skillchoice(skill='Engine Diagnostics').save()
    skillchoice(skill='Fuel System').save()
    # the app assumes general issue has the pk of 11 (such as postajobform, post.js, AjaxVerifyPinView, and mconvert)
    # be sure to update the pk of those classes if changing this table
    skillchoice(skill='General Issue').save()
    skillchoice(skill='Ignition').save()
    skillchoice(skill='Mufflers & Exhaust').save()
    skillchoice(skill='Oil, Lube & Filter Services').save()
    skillchoice(skill='Steering & Suspension Systems').save()
    skillchoice(skill='Tune-Ups').save()
    skillchoice(skill='Wheels & Tires').save()


class Migration(migrations.Migration):
    dependencies = [
        ('mechpages', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
