# Generated by Django 4.2.4 on 2024-02-16 06:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stationaryapp', '0011_item'),
    ]

    operations = [
        migrations.AddField(
            model_name='faculty',
            name='faculty_email',
            field=models.CharField(default='email', max_length=100),
        ),
    ]
