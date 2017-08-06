import datetime

from cuser.fields import CurrentUserField
from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import User
from django.db import models
# Create your models here.
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms import ModelForm


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    description = models.TextField('Описание')
    image = models.ImageField(upload_to='images/events_calendar', blank=True, default='images/events_calendar/default.png')
    creator = CurrentUserField(add_only=True, related_name='Event_creator')
    start_date = models.DateTimeField('Дата начала')
    end_date = models.DateTimeField(verbose_name='Дата окончания', blank=True, null=True)
    category = models.ForeignKey(Category, verbose_name='Категория')
    place_of_event = models.CharField(max_length=100, verbose_name='Место события', blank=True, null=True)
    vk_link = models.CharField(max_length=50, verbose_name='Ссылка в Вк', blank=True, null=True)
    fb_link = models.CharField(max_length=50, verbose_name='Ссылка в Фэйсбук', blank=True, null=True)


    def __str__(self):
        return self.name

class Comment(models.Model):
    creator = CurrentUserField(add_only=True, related_name='Comment_creator')
    text = models.TextField('Комментарий')
    event = models.ForeignKey(Event, verbose_name='Событие', null=True)
    time = models.DateTimeField(auto_now=True, verbose_name='Дата оставленного комментария')

    def __str__(self):
        return self.creator.username

class Organization(models.Model):
    name = models.CharField(max_length=50, verbose_name='Наименование', null=False)
    image = models.ImageField(upload_to='images/organization', blank=True, default='images/organization/default.jpg')

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/users', blank=True, default='images/users/default.png')
    organization = models.ForeignKey(Organization, related_name='organization', verbose_name='Организация', null=True, blank=True)
    signed_organizations = models.ManyToManyField(Organization, related_name='organizations', blank=True, verbose_name='Организации')

    def __str__(self):
        return self.user.username

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()





