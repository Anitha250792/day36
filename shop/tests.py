from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, Product

class ProductApiTests(APITestCase):
    def setUp(self):
        cat = Category.objects.create(name="Cat1")
        Product.objects.create(category=cat, name="A", price=100, stock=5)
        Product.objects.create(category=cat, name="B", price=200, stock=0)

    def test_list_products(self):
        url = "/api/v1/products/"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("results", res.data)
        self.assertGreaterEqual(len(res.data["results"]), 1)

class OrderApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ani", password="pass12345")
        self.cat = Category.objects.create(name="Cat1")
        self.p = Product.objects.create(category=self.cat, name="A", price=100, stock=5)

    def auth(self):
        resp = self.client.post("/api/v1/token/", {"username": "ani", "password": "pass12345"})
        self.assertEqual(resp.status_code, 200)
        token = resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_order(self):
        self.auth()
        payload = {
            "shipping_address": "Chennai",
            "items": [{"product_id": self.p.id, "quantity": 2}]
        }
        res = self.client.post("/api/v1/orders/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["items_detail"][0]["quantity"], 2)
