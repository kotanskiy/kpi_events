from django.contrib import admin

# Register your models here.
from django.contrib.auth.models import User, Permission, PermissionsMixin, Group

from events_calendar.models import Event, Category, Comment, Profile, Organization, ProposedEvent


#Пример
#@admin.register(User)
#class AdminUser(admin.ModelAdmin):
#    list_display = ['username', 'first_name', 'last_name']
admin.site.unregister(User)

class AdminProfileInline(admin.StackedInline):
    model = Profile
    fields = ['organization']

@admin.register(User)
class AdminUser(admin.ModelAdmin):
    fields = [
        'is_staff',
        'is_active',
        'date_joined',
        'last_login',
        'email',
        'first_name',
        'last_name',
        'groups',
    ]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    filter_horizontal = ('groups',)
    inlines = [
        AdminProfileInline,
    ]

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


admin.site.register(Organization)
admin.site.register(ProposedEvent)