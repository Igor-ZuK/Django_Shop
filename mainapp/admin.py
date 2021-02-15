from django.forms import ModelChoiceField, ModelForm
from django.contrib import admin
from django.utils.html import mark_safe
from .models import Category, Notebook, CartProduct, \
    Cart, Customer, Smartphone, Order

# Register your models here.


class SmartphoneAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and not instance.sd:
            self.fields['sd_volume_max'].widget.attrs.update({
                'readonly': True, 'style': 'background: lightgray;'
            })

    def clean(self):
        if not self.cleaned_data['sd']:
            self.cleaned_data['sd_volume_max'] = None
        return self.cleaned_data


class ProductAdminForm(ModelForm):

    MIN_RESOLUTION = (400, 400)
    MAX_RESOLUTION = (4000, 4000)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = mark_safe(
            '<span style="color: red; font-family: Arial sens-serif; font-size: 16px;">Загружайте изображение с'
            ' мин. разрешением {}x{}, и макс. {}x{}</style>'.format(*self.MIN_RESOLUTION, *self.MAX_RESOLUTION)
        )


class SmartphoneAdminAllForm(SmartphoneAdminForm, ProductAdminForm):
    pass


@admin.register(Smartphone)
class SmartphoneAdmin(admin.ModelAdmin):

    change_form_template = 'mainapp/admin.html'

    list_display = ('title', 'price', 'get_image', 'slug')
    readonly_fields = ('get_image',)
    list_editable = ('price',)
    list_filter = ('title', 'price')
    form = SmartphoneAdminAllForm
    save_as = True
    save_on_top = True
    save_as_continue = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='smartphones'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src={obj.image.url} width="50" height="60" style="background-size: cover;">')
        return '-'

    get_image.short_description = "Изображение"


@admin.register(Notebook)
class NotebookAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'get_image', 'slug')
    readonly_fields = ('get_image',)
    list_editable = ('price',)
    list_filter = ('title', 'price')
    form = ProductAdminForm
    save_as = True
    save_on_top = True
    save_as_continue = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='notebooks'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src={obj.image.url} width="50" height="60" style="background-size: cover;">')
        return '-'

    get_image.short_description = "Изображение"


admin.site.register(Category)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Order)
