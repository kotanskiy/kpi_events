# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-05 11:24
from __future__ import unicode_literals

import cuser.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('events_calendar', '0016_auto_20171005_1018'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proposedevent',
            name='category',
        ),
        migrations.RemoveField(
            model_name='proposedevent',
            name='creator',
        ),
        migrations.AddField(
            model_name='event',
            name='creator_user',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Юзер', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='published',
            field=models.BooleanField(default=True, verbose_name='Опублікований'),
        ),
        migrations.DeleteModel(
            name='ProposedEvent',
        ),
    ]