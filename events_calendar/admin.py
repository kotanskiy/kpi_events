from django.contrib import admin

# Register your models here.
from django.contrib.auth.models import User

from events_calendar.models import Event, Category, Comment, Profile, Organization

#Пример
#@admin.register(User)
#class AdminUser(admin.ModelAdmin):
#    list_display = ['username', 'first_name', 'last_name']

admin.site.register(Event)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Profile)
admin.site.register(Organization)
