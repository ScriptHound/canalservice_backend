from django.http import JsonResponse
from orders.models import Order
from django.db.models import FloatField, TextField
from django.db.models.functions import Cast


def get_all_orders(request):
    all_orders = Order.objects.annotate(
        cost_dollars_float=Cast("cost_dollars", output_field=FloatField()),
        cost_roubles_float=Cast("cost_roubles", output_field=FloatField()),
        delivery_time_text=Cast("delivery_time", TextField()),
    )

    all_orders = all_orders.values(
        "id", "ord_id", "cost_dollars_float", "cost_roubles_float", "delivery_time_text"
    )

    return JsonResponse(list(all_orders), safe=False)
