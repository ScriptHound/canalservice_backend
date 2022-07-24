from datetime import datetime
from decimal import Decimal
from typing import List

import pandas as pd

from django.db import connection

from canalservice.celery import app
from orders.logic import (
    authorize,
    get_dollar_exchange_rate,
    get_file_from_google_drive,
    download_file,
)
from orders.models import Order


def get_current_revenue_data():
    conn = connection.cursor().connection
    current_data = pd.read_sql("select * from orders_order order by ord_id", conn)
    return current_data


def timezone_column_to_date(delivery_time):
    date = datetime.fromisoformat(str(delivery_time))
    date = str(date.date())
    return date


def compare_google_and_db_data():
    curdata = get_current_revenue_data()
    credentials = authorize("credentials.json")
    _, file_id = get_file_from_google_drive("canalservice_test", credentials)
    file_contents = download_file(file_id, credentials)

    google_data = pd.read_excel(file_contents)
    google_data.dropna(inplace=True)
    google_data.drop(columns=["№"], inplace=True)
    google_data.rename(
        columns={
            "заказ №": "ord_id",
            "стоимость,$": "cost_dollars",
            "срок поставки": "delivery_time",
        },
        inplace=True,
    )

    curdata.drop(columns=["id", "cost_roubles"], inplace=True)
    curdata["delivery_time"] = curdata["delivery_time"].apply(timezone_column_to_date)
    google_data["delivery_time"] = google_data["delivery_time"].apply(
        timezone_column_to_date
    )
    google_data["cost_dollars"] = google_data["cost_dollars"].apply(lambda x: float(x))
    curdata["cost_dollars"] = curdata["cost_dollars"].apply(lambda x: float(x))

    google_data.set_index("ord_id", inplace=True, drop=False)
    curdata.set_index("ord_id", inplace=True, drop=False)
    google_data.sort_index(inplace=True)
    curdata.sort_index(inplace=True)

    if google_data.equals(curdata):
        return pd.DataFrame(), pd.DataFrame()

    difference = pd.concat([google_data, curdata, curdata]).drop_duplicates(keep=False)
    delete_difference = pd.concat([curdata, google_data, google_data]).drop_duplicates(
        keep=False
    )
    difference_ids = difference["ord_id"]
    delete_difference = delete_difference[
        ~delete_difference["ord_id"].isin(difference_ids)
    ]
    return difference, delete_difference


@app.task(bind=True, name="googlesheet_check")
def update_database_records(_):
    difference, delete_difference = compare_google_and_db_data()

    if difference.empty:
        return

    order_numbers = list(difference["ord_id"])
    existing_orders = list(Order.objects.values_list("ord_id", flat=True))
    new_ord_ids = filter(lambda id: id not in existing_orders, order_numbers)
    new_ord_ids = list(new_ord_ids)
    new_orders = difference[difference["ord_id"].isin(new_ord_ids)]

    orders: List[Order] = Order.objects.filter(ord_id__in=order_numbers)
    exchange_rate = get_dollar_exchange_rate()
    to_update = []
    for order in orders:
        ord_id = order.ord_id
        update_data = difference[difference["ord_id"] == ord_id]
        delivery_time = update_data["delivery_time"].astype(str)
        cost_dollars = update_data["cost_dollars"].astype(float)
        cost_dollars = list(cost_dollars)[0]
        cost_rubles = exchange_rate * Decimal(cost_dollars)

        order.delivery_time = list(delivery_time)[0]
        order.cost_dollars = cost_dollars
        order.cost_roubles = cost_rubles
        to_update.append(order)

    to_create = []
    for _, order in new_orders.iterrows():
        ord_id = order["ord_id"]
        cost_dollars = Decimal(order["cost_dollars"])
        cost_rubles = exchange_rate * cost_dollars
        delivery_time = str(order["delivery_time"])

        order_obj = Order(
            cost_dollars=cost_dollars,
            ord_id=ord_id,
            cost_roubles=cost_rubles,
            delivery_time=delivery_time,
        )
        to_create.append(order_obj)

    Order.objects.bulk_create(to_create)
    Order.objects.bulk_update(
        to_update, ["cost_dollars", "delivery_time", "cost_roubles"]
    )

    if delete_difference.empty:
        return

    to_delete = list(delete_difference["ord_id"].astype(int))
    Order.objects.filter(ord_id__in=to_delete).delete()
