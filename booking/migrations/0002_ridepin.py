from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RidePin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pin_hash', models.CharField(max_length=128)),
                ('pin_plain', models.CharField(max_length=4)),
                ('attempts', models.IntegerField(default=0)),
                ('locked_until', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ride_pin', to='booking.booking')),
            ],
        ),
    ]

