# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-11-27 00:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estados', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='estado',
            name='sigla_uf',
            field=models.CharField(blank=True, max_length=2, null=True, verbose_name='sigla_uf'),
        ),
    ]
