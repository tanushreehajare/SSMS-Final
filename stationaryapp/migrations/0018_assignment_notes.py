# Generated by Django 4.2.4 on 2024-02-20 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stationaryapp', '0017_alter_stationarybill_caption_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='notes',
            field=models.CharField(default='DEPT', max_length=50),
        ),
    ]
