# Generated by Django 3.2.4 on 2021-06-23 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Topology',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(default='none', verbose_name='Description')),
                ('name', models.TextField(default='noname', verbose_name='name')),
                ('json', models.TextField(verbose_name='json')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
            ],
            options={
                'verbose_name': 'Topology',
                'verbose_name_plural': 'topologies',
            },
        ),
    ]
