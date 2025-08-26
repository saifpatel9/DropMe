from django.db import models
from passenger.models import User

class Wallet(models.Model):
    wallet_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    used_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)



    def __str__(self):
        return f"Wallet of {self.user.user_name}" if self.user else "Wallet"
    
class WalletPayment(models.Model):
    wallet_payment_id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_id',
        db_column='user_id',
        null=True,
        blank=True
    )

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        to_field='wallet_id',
        db_column='wallet_id',
        null=True,
        blank=True
    )

    title = models.CharField(max_length=255, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    payment_mode = models.CharField(max_length=50, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'wallet_payment'
        managed = True 

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"