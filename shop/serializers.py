from rest_framework import serializers
from .models import Category, Product, Order, OrderItem

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "parent", "children", "created_at"]

    def get_children(self, obj):
        return CategorySerializer(obj.children.all(), many=True).data


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "category", "category_name", "price", "stock", "is_active", "created_at"]


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "price", "stock", "image",
            "is_active", "created_at", "category", "category_id",
        ]


class OrderItemWriteSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product"
    )

    class Meta:
        model = OrderItem
        fields = ["product_id", "quantity"]


class OrderItemReadSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "unit_price", "subtotal"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemWriteSerializer(many=True, write_only=True)
    items_detail = OrderItemReadSerializer(source="items", many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "status", "shipping_address", "created_at", "items", "items_detail", "total_amount"]
        read_only_fields = ["user", "status", "created_at"]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("An order must contain at least one item.")
        for item in items:
            if item["quantity"] <= 0:
                raise serializers.ValidationError("Quantity must be positive.")
        return items

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        user = self.context["request"].user
        order = Order.objects.create(user=user, **validated_data)

        # Check stock & create items
        for it in items_data:
            product = it["product"]
            qty = it["quantity"]
            if product.stock < qty:
                raise serializers.ValidationError(f"Insufficient stock for {product.name}")
            # lock price at order time
            OrderItem.objects.create(
                order=order, product=product, quantity=qty, unit_price=product.price
            )
            # reduce stock
            product.stock -= qty
            product.save(update_fields=["stock"])

        return order
