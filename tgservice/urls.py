from django.contrib import admin
from django.urls import path
from tgservice import views


app_name = 'tgservice'

urlpatterns = [
    path('', views.main_view, name='main'),
]