from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0008_riderequest_distance_duration"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="cancelled_by",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="cancellation_reason",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="cancellation_stage",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="booking",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Pending", "Pending"),
                    ("Confirmed", "Confirmed"),
                    ("Arrived", "Arrived"),
                    ("Ongoing", "Ongoing"),
                    ("Completed", "Completed"),
                    ("Cancelled", "Cancelled"),
                    ("CancelledByDriver", "Cancelled by Driver"),
                    ("CancelledByPassenger", "Cancelled by Passenger"),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]

