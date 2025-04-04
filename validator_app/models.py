from django.db import models

class ClientValidation(models.Model):
    client_id = models.CharField(max_length=255)
    is_registered = models.BooleanField(default=False)
    reg_date = models.DateTimeField(null=True, blank=True)
    client_account = models.CharField(max_length=255, blank=True, null=True)
    client_account_type = models.CharField(max_length=50, blank=True, null=True)
    volume_lots = models.FloatField(default=0)
    volume_mln_usd = models.FloatField(default=0)
    reward = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reward_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.client_id} - {'Registered' if self.is_registered else 'Not Registered'}" 