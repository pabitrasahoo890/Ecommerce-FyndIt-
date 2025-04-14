from .models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class CustomUserResource(resources.ModelResource):
    class Meta:
        model = CustomUser
        exclude = ('password',)  # Optional: exclude password if not used
        import_id_fields = ['phone']  # Or 'email' if it's your unique field

@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin):
    resourse_class = CustomUserResource
    list_display = ("phone", "name", "email", "is_active", "is_staff")  # Columns in admin
    search_fields = ("phone", "name", "email")  # Enables search functionality
    list_filter = ("is_active", "is_staff", "country", "state")  # Sidebar filters
    ordering = ("-id",)  # Orders by latest user
    

    fieldsets = (
        ("Basic Info", {"fields": ("phone", "name", "email")}),
        ("Address", {"fields": ("country", "state", "city", "pincode")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Security", {"fields": ("otp",)}),  # OTP field for admin reference
        ("Groups & Permissions", {"fields": ("groups", "user_permissions")}),
    )

    # Custom user creation (removes password fields)
    add_fieldsets = (
        (
            "Register New User",
            {"fields": ("phone", "name", "email", "is_active", "is_staff")},
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Removes password fields from the form"""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields.pop("password", None)  # Removes password from form
        return form


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")              # Shows ID and name in list view
    search_fields = ("name",)                  # Enables search by name
    ordering = ("name",) 


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "category")   # Display fields in list view
    list_filter = ("category",)                         # Filter by category
    search_fields = ("name", "slug")                    # Search by name or slug
    prepopulated_fields = {"slug": ("name",)}           # Auto-generate slug from name
    ordering = ("name",)


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        import_id_fields = ['slug']

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = (
        "id", "name", "subcategory", "price", "stock", "is_featured", "created_at"
    )
    list_filter = ("subcategory", "is_featured", "created_at")
    search_fields = ("name", "slug", "subcategory__name")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {
            "fields": ("name", "slug", "subcategory", "image", "price", "stock", "is_featured")
        }),
        ("Description", {
            "fields": ("description",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "product", "quantity", "total_price_display", "added_at"
    )
    list_filter = ("added_at", "product")
    search_fields = ("user__phone", "product__name")
    ordering = ("-added_at",)

    readonly_fields = ("added_at", "total_price_display")

    def total_price_display(self, obj):
        return f"₹{obj.total_price()}"
    total_price_display.short_description = "Total Price"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "product", "added_at"
    )
    list_filter = ("added_at", "product")
    search_fields = ("user__phone", "product__name")
    ordering = ("-added_at",)
    readonly_fields = ("added_at",)


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "full_name", "phone_number", "city", "state", "country", "postal_code", "is_default"
    )
    list_filter = ("is_default", "country", "state")
    search_fields = ("user__phone", "full_name", "city", "state", "country")
    ordering = ("-id",)

class OrderResource(resources.ModelResource):
    class Meta:
        model = Order
        import_id_fields = ['unique_order_id']

@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    order_class = OrderResource
    list_display = (
        'unique_order_id', 'user', 'total_amount', 'status', 'payment_method', 'created_at', 'updated_at'
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('unique_order_id', 'user__phone', 'user__email')
    readonly_fields = ('unique_order_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    autocomplete_fields = ['user', 'shipping_address']
    list_per_page = 20

    fieldsets = (
        (None, {
            'fields': ('unique_order_id', 'user', 'shipping_address')
        }),
        ('Order Info', {
            'fields': ('total_amount', 'status', 'payment_method')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'total_price')
    list_filter = ('order__status', 'product__subcategory', 'product__name')
    search_fields = ('order__unique_order_id', 'product__name')
    autocomplete_fields = ['order', 'product']
    list_select_related = ('order', 'product')
    list_per_page = 25

    def total_price(self, obj):
        return obj.quantity * obj.price
    total_price.short_description = 'Total Price'


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
    ordering = ('-created_at',)
