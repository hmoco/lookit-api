# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-05 19:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0010_study_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='contact_info',
            field=models.TextField(default="don't"),
            preserve_default=False,
        ),
    ]