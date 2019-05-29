# Generated by Django 2.2.1 on 2019-05-29 11:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('email', models.CharField(max_length=30)),
                ('password', models.CharField(max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('filename', models.TextField()),
                ('url', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='seonbi.User')),
            ],
        ),
        migrations.CreateModel(
            name='Censor',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('cause', models.CharField(max_length=20)),
                ('src_video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='seonbi.Video')),
            ],
        ),
    ]