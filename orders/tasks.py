from datetime import datetime
from typing import List

import pandas as pd

from django.db import connection

from canalservice.celery import app
from orders.logic import (
    authorize,
    get_file_from_google_drive,
    download_file)
from orders.models import Order


def get_current_revenue_data():
    conn = connection.cursor().connection
    current_data = pd.read_sql(
        "select * from orders_order",
        conn)
    return current_data


def timezone_column_to_date(delivery_time):
    date = datetime.fromisoformat(str(delivery_time))
    date = str(date.date())
    return date


def compare_google_and_db_data():
    curdata = get_current_revenue_data()
    credentials = authorize('credentials.json')
    _, file_id = get_file_from_google_drive(
        'canalservice_test',
        credentials)
    file_contents = download_file(file_id, credentials)
    
    google_data = pd.read_excel(file_contents)
    google_data.drop(columns=['№'], inplace=True)
    google_data.rename(
        columns={
            "заказ №": "order_NO",
            "стоимость,$": "cost_dollars",
            "срок поставки": "delivery_time"
        }, inplace=True)
    
    curdata.drop(columns=['id', 'cost_roubles'], inplace=True)
    curdata['delivery_time'] = curdata['delivery_time']\
        .apply(timezone_column_to_date)
    google_data['delivery_time'] = curdata['delivery_time']\
        .apply(timezone_column_to_date)
    google_data['cost_dollars'] = google_data['cost_dollars']\
        .apply(lambda x: float(x))
    curdata['cost_dollars'] = curdata['cost_dollars']\
        .apply(lambda x: float(x))

    if google_data.equals(curdata):
        return pd.DataFrame()

    difference = pd.concat([google_data, curdata, curdata]).drop_duplicates(keep=False)
    return difference


@app.task()
def update_database_records():
    difference = compare_google_and_db_data()

    if difference.empty:
        return

    order_numbers = list(difference['order_NO'])
    orders: List[Order] = Order.objects.filter(order_NO__in=order_numbers)
    to_update = []
    for order in orders:
        order_NO = order.order_NO
        update_data = difference[difference['order_NO'] == order_NO]
        delivery_time = update_data['delivery_time'].astype(str)
        cost_dollars = update_data['cost_dollars'].astype(float)

        order.delivery_time = list(delivery_time)[0]
        order.cost_dollars = list(cost_dollars)[0]
        to_update.append(order)
    
    Order.objects.bulk_update(to_update, ['cost_dollars', 'delivery_time'])
