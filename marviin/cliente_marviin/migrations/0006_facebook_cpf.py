# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-12-16 12:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cliente_marviin', '0005_auto_20161215_1008'),
    ]

    operations = [
        migrations.AddField(
            model_name='facebook',
            name='cpf',
            field=models.CharField(blank=True, max_length=11, null=True, verbose_name='cpf'),
        ),
    ]