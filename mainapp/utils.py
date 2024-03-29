from django.db import models

def recalc_cart(cart):
    cart_data = cart.products.aggregate(models.Sum('total_price'), models.Count('id'))
    if cart_data.get('total_price__sum', None):
        cart.total_price = cart_data['total_price__sum']
    else:
        cart.total_price = 0
    cart.total_products = cart_data['id__count']
    cart.save()