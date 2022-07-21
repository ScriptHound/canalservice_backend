from django.db import models

# Create your models here.
class Order(models.Model):
    id = models.AutoField(primary_key=True)
    order_NO = models.BigIntegerField(unique=True)
    cost_dollars = models.DecimalField(max_digits=20, decimal_places=2)
    cost_roubles = models.DecimalField(max_digits=21, decimal_places=2)
    delivery_time = models.DateTimeField()
