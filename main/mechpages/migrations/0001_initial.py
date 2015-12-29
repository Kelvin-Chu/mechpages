# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mechpages.models
import imagekit.models.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('authtools', '0003_auto_20151105_1414'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JobHistory',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('company', models.CharField(max_length=100, blank=True)),
                ('position', models.CharField(max_length=100, blank=True)),
                ('years', models.CharField(max_length=2, blank=True)),
                ('description', models.TextField(max_length=2000, blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('user', models.OneToOneField(related_name='location', serialize=False, to=settings.AUTH_USER_MODEL, primary_key=True)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('radius', models.CharField(max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='MobileNumber',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('mobile', models.CharField(unique=True, max_length=16)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='NotifyAvailability',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('email', models.EmailField(unique=True, max_length=254)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='PostAJob',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('car_make', models.CharField(max_length=50)),
                ('car_model', models.CharField(max_length=50)),
                ('car_year', models.CharField(max_length=4)),
                ('comment', models.TextField(max_length=2000)),
                ('done', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['done', '-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='ProjectImage',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('title', models.CharField(max_length=50, blank=True)),
                ('image', imagekit.models.fields.ProcessedImageField(upload_to=mechpages.models.RandomFileName('projects/images/'))),
                ('description', models.TextField(max_length=100, blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('rating', models.PositiveIntegerField()),
                ('comment', models.TextField(max_length=2000, blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='SkillChoice',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('skill', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['skill'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('user', models.OneToOneField(serialize=False, to=settings.AUTH_USER_MODEL, primary_key=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('avatar', imagekit.models.fields.ProcessedImageField(upload_to=mechpages.models.RandomFileName('avatars/'), blank=True)),
                ('mobile', models.CharField(unique=True, null=True, max_length=16, blank=True)),
                ('address', models.CharField(max_length=100, blank=True)),
                ('city', models.CharField(max_length=50, blank=True)),
                ('state', models.CharField(default='-', choices=[('-', 'State'), ('AL', 'AL'), ('AK', 'AK'), ('AZ', 'AZ'), ('AR', 'AR'), ('CA', 'CA'), ('CO', 'CO'), ('CT', 'CT'), ('DE', 'DE'), ('DC', 'DC'), ('FL', 'FL'), ('GA', 'GA'), ('HI', 'HI'), ('ID', 'ID'), ('IL', 'IL'), ('IN', 'IN'), ('IA', 'IA'), ('KS', 'KS'), ('KY', 'KY'), ('LA', 'LA'), ('ME', 'ME'), ('MD', 'MD'), ('MA', 'MA'), ('MI', 'MI'), ('MN', 'MN'), ('MS', 'MS'), ('MO', 'MO'), ('MT', 'MT'), ('NE', 'NE'), ('NV', 'NV'), ('NH', 'NH'), ('NJ', 'NJ'), ('NM', 'NM'), ('NY', 'NY'), ('NC', 'NC'), ('ND', 'ND'), ('OH', 'OH'), ('OK', 'OK'), ('OR', 'OR'), ('PA', 'PA'), ('RI', 'RI'), ('SC', 'SC'), ('SD', 'SD'), ('TN', 'TN'), ('TX', 'TX'), ('UT', 'UT'), ('VT', 'VT'), ('VA', 'VA'), ('WA', 'WA'), ('WV', 'WV'), ('WI', 'WI'), ('WY', 'WY')], max_length=2)),
                ('zip', models.CharField(max_length=10, blank=True)),
                ('car_make', models.CharField(max_length=50, blank=True)),
                ('car_model', models.CharField(max_length=50, blank=True)),
                ('car_year', models.CharField(max_length=4, blank=True)),
                ('review_points', models.PositiveIntegerField(default=0)),
                ('is_mechanic', models.BooleanField(default=False)),
                ('mobile_verified', models.BooleanField(default=False)),
                ('short_bio', models.TextField(max_length=160, blank=True)),
                ('add_info', models.TextField(max_length=1000, blank=True)),
                ('profile_complete', models.BooleanField(default=False)),
                ('publish', models.BooleanField(default=False)),
                ('project_limit', models.PositiveIntegerField(default=9)),
                ('rating', models.PositiveSmallIntegerField(default=0)),
                ('rating_count', models.PositiveIntegerField(default=0)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('skills', models.ManyToManyField(to='mechpages.SkillChoice')),
            ],
        ),
        migrations.AddField(
            model_name='review',
            name='mechanic',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='review'),
        ),
        migrations.AddField(
            model_name='review',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='reviewer'),
        ),
        migrations.AddField(
            model_name='projectimage',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='projectimages'),
        ),
        migrations.AddField(
            model_name='postajob',
            name='skill',
            field=models.ForeignKey(to='mechpages.SkillChoice'),
        ),
        migrations.AddField(
            model_name='postajob',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='postajob'),
        ),
        migrations.AddField(
            model_name='jobhistory',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='jobhistory'),
        ),
    ]
