# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-18 16:06
from __future__ import unicode_literals

from django.db import migrations
import utils.bigint


class Migration(migrations.Migration):

    dependencies = [
        ('cliente', '0004_cliente_foto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='id',
            field=utils.bigint.BigAutoField(editable=False, primary_key=True, serialize=False),
        ),
    ]
