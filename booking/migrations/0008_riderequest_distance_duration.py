from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0007_alter_booking_status_alter_ridepin_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="riderequest",
            name="distance_km",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="riderequest",
            name="duration_min",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]

