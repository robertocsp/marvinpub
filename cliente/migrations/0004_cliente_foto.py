# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-06 16:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cliente', '0003_cliente_chave_facebook'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='foto',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True, verbose_name=b'foto'),
        ),
    ]
