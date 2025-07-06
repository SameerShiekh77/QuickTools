from django.urls import path, include
from socialmediatool import views

urlpatterns = [
    path("",views.brand_kit, name="brand_kit"),
]
