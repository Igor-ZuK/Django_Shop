from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone

# Create your models here.

User = get_user_model()


class Category(models.Model):

    name = models.CharField("Имя категории", max_length=250)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):

    title = models.CharField("Наименование", max_length=255)
    category = models.ForeignKey(Category, verbose_name="Категория", on_delete=models.CASCADE)
    price = models.DecimalField("Цена", max_digits=12, decimal_places=2)
    image = models.ImageField("Изображение")
    description = models.TextField("Описание", max_length=5000, null=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title

    def get_model_name(self):
        return self.__class__.__name__.lower()


class CartProduct(models.Model):

    user = models.ForeignKey("Customer", verbose_name="Покупатель", on_delete=models.CASCADE)
    cart = models.ForeignKey("Cart", verbose_name="Корзина", on_delete=models.CASCADE, related_name='related_products')
    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField("Общая цена", max_digits=12, decimal_places=3)

    def __str__(self):
        return f'Продукт: {self.product.title}'

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.product.price
        super().save(*args, **kwargs)


class Cart(models.Model):

    owner = models.ForeignKey("Customer", null=True, verbose_name="Владелец", on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    total_price = models.DecimalField("Общая цена", default=0, max_digits=12, decimal_places=3)
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Customer(models.Model):

    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    phone = models.CharField("Номер телефона", max_length=20, null=True, blank=True)
    address = models.CharField("Адрес", max_length=255, null=True, blank=True)
    orders = models.ManyToManyField("Order", verbose_name="Заказы покупателя", related_name="related_customer")

    def __str__(self):
        return f'Покупатель: {self.user.first_name} {self.user.last_name}'


class Order(models.Model):

    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'in_ready'
    STATUS_COMPLETED = 'completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW, 'Новый заказ'),
        (STATUS_NEW, 'Заказ в обработке'),
        (STATUS_READY, 'Заказ готов'),
        (STATUS_COMPLETED, 'Заказ выполнен')
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка'),
    )

    customer = models.ForeignKey(Customer, verbose_name="Покупатель", related_name="related_orders", on_delete=models.CASCADE)
    first_name = models.CharField("Имя", max_length=255)
    last_name = models.CharField("Фамилия", max_length=255)
    phone = models.CharField("Телефон", max_length=20)
    cart = models.ForeignKey(Cart, verbose_name="Корзина", on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField("Адрес", max_length=255, null=True, blank=True)
    status = models.CharField("Статус заказа", max_length=100, choices=STATUS_CHOICES, default=STATUS_NEW)
    buying_type = models.CharField("Тип заказа", max_length=100, choices=BUYING_TYPE_CHOICES, default=BUYING_TYPE_SELF)
    comment = models.TextField("Комментарий к заказу", max_length=5000, null=True, blank=True)
    created_at = models.DateTimeField("Дата создания заказа", auto_now=True)
    order_date = models.DateField("Дата получения заказа", default=timezone.now)

    def __str__(self):
        return str(self.id)
