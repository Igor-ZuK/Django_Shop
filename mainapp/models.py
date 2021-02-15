from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.utils import timezone

# Create your models here.

User = get_user_model()


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


class LatestProductsManager:

    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to), reverse=True
                    )
        return products


class LatestProducts:

    objects = LatestProductsManager()


class CategoryManager(models.Manager):

    CATEGORY_NAME_COUNT_NAME = {
        'Ноутбуки': 'notebook__count',
        'Смартфоны': 'smartphone__count',
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_sidebar(self):
        models = get_models_for_count('notebook', 'smartphone')
        qs = list(self.get_queryset().annotate(*models))
        data = [
                dict(name=c.name, url=c.get_absolute_url(), count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
                for c in qs
        ]
        return data


class Category(models.Model):

    name = models.CharField("Имя категории", max_length=250)
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):

    class Meta:
        abstract = True

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


class Notebook(Product):

    diagonal = models.CharField("Диагональ", max_length=255)
    display_type = models.CharField("Тип дисплея", max_length=255)
    processor_freq = models.CharField("Частота процессора", max_length=255)
    ram = models.CharField("Оперативная память", max_length=255)
    video = models.CharField("Видеокарта", max_length=255)
    time_without_charge = models.CharField("Время работы аккумулятора", max_length=255)

    def __str__(self):
        return f'{self.category.name} : {self.title}'

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class Smartphone(Product):

    SD_VOLUME = {
        ('8', '8 Gb'),
        ('16', '16 Gb'),
        ('32', '32 Gb'),
        ('64', '64 Gb'),
        ('128', '128 Gb'),
    }

    diagonal = models.CharField("Диагональ", max_length=255)
    display_type = models.CharField("Тип дисплея", max_length=255)
    resolution = models.CharField("Разрешение", max_length=255)
    accum_volume = models.CharField("Объём батареи", max_length=255)
    ram = models.CharField("Оперативная память", max_length=255)
    sd = models.BooleanField("Наличие SD карты", default=True)
    sd_volume_max = models.CharField(
        "Максимальный объём памяти", max_length=255, null=True,
        blank=True, choices=SD_VOLUME, default='8'
    )
    main_cam = models.CharField("Главная камера", max_length=255)
    frontal_cam = models.CharField("Фронтальная камера", max_length=255)

    def __str__(self):
        return f'{self.category.name} : {self.title}'

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class CartProduct(models.Model):

    user = models.ForeignKey("Customer", verbose_name="Покупатель", on_delete=models.CASCADE)
    cart = models.ForeignKey("Cart", verbose_name="Корзина", on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField("Общая цена", max_digits=12, decimal_places=3)

    def __str__(self):
        return f'Продукт: {self.content_object.title}'

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.content_object.price
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
