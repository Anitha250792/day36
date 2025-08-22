from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Category, Product, Order
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    OrderSerializer
)
from .permissions import IsAdminOrReadOnly
from .filters import ProductFilter

# ===== HTML Views =====

class ProductListPage(ListView):
    model = Product
    template_name = "shop/product_list.html"
    context_object_name = "products"
    paginate_by = 8

    def get_queryset(self):
        qs = Product.objects.select_related("category").filter(is_active=True)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(name__icontains=q)
        cat = self.request.GET.get("category")
        if cat:
            qs = qs.filter(category_id=cat)
        return qs


class ProductDetailPage(DetailView):
    model = Product
    template_name = "shop/product_detail.html"
    context_object_name = "product"


def register(request):
    from .forms import RegisterForm
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("product_list_page")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


# ===== API ViewSets =====

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = (
        Product.objects.select_related("category")
        .filter(is_active=True)
        .all()
    )
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrReadOnly()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action in ["list"]:
            return ProductListSerializer
        return ProductDetailSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # optimize
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items__product__category")
            .all()
        )

    @action(detail=False, methods=["get"])
    def my(self, request, *args, **kwargs):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)
