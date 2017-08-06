from django.contrib import admin

# Register your models here.
from events_calendar.models import Event, Category, Comment, Profile, Organization

admin.site.register(Event)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Profile)
admin.site.register(Organization)
