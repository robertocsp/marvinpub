# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-11-10 11:30
from __future__ import unicode_literals

from django.db import migrations
from loja.models import *


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0008_bigint_20161110_0004'),
        ('dashboard', '0005_auto_20161110_0001')
    ]

    operations = [
        migrations.RunSQL(
            'alter table dashboard_dashboard add constraint dashboard_dashboard_loja_id_e8d3c45f_fk_loja_loja_id FOREIGN KEY (loja_id) REFERENCES loja_loja (id);')
    ]
