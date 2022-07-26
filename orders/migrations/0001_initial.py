# Generated by Django 4.0.6 on 2022-07-21 12:53

from decimal import Decimal
from django.db import migrations, models
import pandas as pd

from orders.models import Order
from orders.logic import (
    authorize,
    get_file_from_google_drive,
    download_file,
    get_dollar_exchange_rate,
)


def populate_with_initial_data(apps, schema_editor):
    credentials = authorize("credentials.json")
    _, file_id = get_file_from_google_drive("canalservice_test", credentials)
    file_contents = download_file(file_id, credentials)
    df = pd.read_excel(file_contents)
    orders = []
    exchange_rate = get_dollar_exchange_rate()
    for _, row in df.iterrows():
        cost_dollars = Decimal(row["стоимость,$"])
        order = Order(
            order_NO=row["заказ №"],
            cost_dollars=cost_dollars,
            cost_roubles=cost_dollars * exchange_rate,
            delivery_time=row["срок поставки"],
        )
        orders.append(order)
    Order.objects.bulk_create(orders)


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("order_NO", models.BigIntegerField(unique=True)),
                ("cost_dollars", models.DecimalField(decimal_places=2, max_digits=20)),
                ("cost_roubles", models.DecimalField(decimal_places=2, max_digits=21)),
                ("delivery_time", models.DateTimeField()),
            ],
        ),
        migrations.RunPython(populate_with_initial_data),
    ]
