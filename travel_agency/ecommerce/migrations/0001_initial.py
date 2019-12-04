# Generated by Django 2.2.5 on 2019-10-29 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.IntegerField()),
                ('attribute', models.TextField(max_length=75)),
                ('value', models.TextField(blank=True, max_length=3000)),
            ],
        ),
    ]