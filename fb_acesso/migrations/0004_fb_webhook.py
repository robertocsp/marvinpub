# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-12-23 00:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fb_acesso', '0003_fb_acesso_app_scoped_user_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fb_webhook',
            fields=[
                ('app_id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('webhook_url', models.CharField(max_length=50)),
            ],
        ),
    ]
