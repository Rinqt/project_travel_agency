from django.contrib import admin
from .models import Item

admin.site.site_header = "Ecommerce Inventory"
admin.site.site_title = "Travel Agency Admin"


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['item_attribute', 'value']
    search_fields = ['object_id', 'attribute']
    list_filter = ['object_id']

    def item_attribute(self, obj):
        item_id = obj.object_id
        item_attribute = obj.attribute
        res = 'Item: ' + str(item_id) + ' - ' + item_attribute
        return res
