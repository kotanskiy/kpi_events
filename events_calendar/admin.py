from django.contrib import admin

# Register your models here.
from django.contrib.auth.models import User

from events_calendar.models import Event, Category, Comment, Profile, Organization

#Пример
#@admin.register(User)
#class AdminUser(admin.ModelAdmin):
#    list_display = ['username', 'first_name', 'last_name']

@admin.register(Event)
class AdminEvent(admin.ModelAdmin):
    list_display = [
        'name',
        'description',
        'start_date',
        'creator',
    ]


admin.site.register(Category)

@admin.register(Comment)
class AdminComment(admin.ModelAdmin):
    list_display = [
        'creator',
        'text',
        'event',
        'time',
    ]
admin.site.register(Profile)
admin.site.register(Organization)
