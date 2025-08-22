from django.urls import path
from django.contrib.auth import views as auth_views
from .views import ProductListPage, ProductDetailPage, register

urlpatterns = [
    path("", ProductListPage.as_view(), name="product_list_page"),
    path("products/<int:pk>/", ProductDetailPage.as_view(), name="product_detail_page"),

    # Auth (session for HTML pages)
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="product_list_page"), name="logout"),
    path("register/", register, name="register"),
]
