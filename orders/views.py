from django.http import JsonResponse
from orders.models import Order
from django.db.models import FloatField, TextField
from django.db.models.functions import Cast


def get_all_orders(_):
    """Django serialization isnt appropriate because
    resulting data is more nested and contains unnecesary data
    Resulting data looks like:
    [
        {
            "id": the_numeric_id,
            "ord_id": the_numeric_ord_id,
            "cost_dollars_float": the_numeric_cost,
            "cost_roubles_float": the_numeric_cost,
            "delivery_time_text": the_date_in_text_format,
        },
    ]
    """
    all_orders = Order.objects.annotate(
        cost_dollars_float=Cast("cost_dollars", output_field=FloatField()),
        cost_roubles_float=Cast("cost_roubles", output_field=FloatField()),
        delivery_time_text=Cast("delivery_time", TextField()),
    )

    all_orders = all_orders.values(
        "id", "ord_id", "cost_dollars_float", "cost_roubles_float", "delivery_time_text"
    )

    return JsonResponse(list(all_orders), safe=False)
