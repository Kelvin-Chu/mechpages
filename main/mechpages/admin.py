from django.contrib import admin
from .models import UserProfile, MobileNumber, ProjectImage, JobHistory, SkillChoice, Location, Review, PostAJob

admin.site.register(UserProfile)
admin.site.register(MobileNumber)
admin.site.register(ProjectImage)
admin.site.register(JobHistory)
admin.site.register(SkillChoice)
admin.site.register(Location)
admin.site.register(Review)
admin.site.register(PostAJob)
