# Generated by Django 2.2.5 on 2019-11-08 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField()),
                ('object_id', models.IntegerField()),
                ('last_modified', models.TextField(max_length=50, blank=True)),
            ],
        ),
    ]
