from cuser.fields import CurrentUserField
from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from oauth2client.contrib.django_util.models import CredentialsField


class Index(models.Model):
    word = models.TextField(max_length=50)
    links = models.TextField(null=True)  # change on SET()

    def __str__(self):
        return self.links

class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name='Назва')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'

class Organization(models.Model):
    name = models.CharField(max_length=50, verbose_name='Найменування', null=False)
    image = models.ImageField(upload_to='images/organization', blank=True, default='images/organization/default.jpg')
    access_to_the_offer = models.BooleanField(default=False, blank=True)
    link_to_organization = models.CharField(max_length=50, verbose_name='Посилання на організацію', blank=True, null=True, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Організація'
        verbose_name_plural = 'Організації'

class Event(models.Model):
    name = models.CharField(max_length=100, verbose_name='Назва')
    description = models.TextField('Опис', blank=True, null=True)
    image = models.ImageField(upload_to='images/events_calendar', blank=True, default='images/events_calendar/default.png')
    creator_user = CurrentUserField(add_only=True, related_name='Юзер')
    creator = models.ForeignKey(Organization, verbose_name='Організація', null=True)
    start_date = models.DateTimeField('Дата початку')
    end_date = models.DateTimeField(verbose_name='Дата закінчення', blank=True, null=True)
    category = models.ForeignKey(Category, verbose_name='Категорія')
    place_of_event = models.CharField(max_length=100, verbose_name='Місце події', blank=True, null=True)
    fb_link = models.CharField(max_length=50, verbose_name='Посилання в fb', blank=True, null=True)
    web_site = models.CharField(max_length=50, verbose_name='Посилання на сайт події', blank=True, null=True)
    published = models.BooleanField(default=True, verbose_name='Опублікований')

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        from events_calendar.utils import add_index
        add_index(self.pk)

    class Meta:
        ordering = [
            '-start_date',
        ]
        verbose_name = 'Подія'
        verbose_name_plural = 'Події'

class Comment(models.Model):
    creator = CurrentUserField(add_only=True, related_name='Comment_creator')
    text = models.TextField('Коментар')
    event = models.ForeignKey(Event, verbose_name='Подія', null=True)
    time = models.DateTimeField(auto_now=True, verbose_name='Дата залишеного коментаря')

    def __str__(self):
        return self.creator.username

    class Meta:
        verbose_name = 'Коментар'
        verbose_name_plural = 'Коменти'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/users', blank=True, default='images/users/default.jpg')
    organization = models.ForeignKey(Organization, related_name='organization', verbose_name='Організація', null=True, blank=True)
    signed_organizations = models.ManyToManyField(Organization, related_name='organizations', blank=True, verbose_name='Організації')
    google_calendar_events = models.ManyToManyField(Event, blank=True, verbose_name='Події додані в гугл календар юзера')
    signed_events = models.ManyToManyField(Event, related_name='signed_events', blank=True, verbose_name='Події, які додані в "Мої події"')

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'Профіль'
        verbose_name_plural = 'Профілі'

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()


