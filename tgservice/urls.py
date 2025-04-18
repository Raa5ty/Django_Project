from django.contrib import admin
from django.urls import path
from tgservice import views


app_name = 'tgservice'

urlpatterns = [
    path('', views.main_view, name='main'),
    path('search/', views.search_view, name='search'),
    path('projects/', views.projects_view, name='projects'),
    path('database/', views.database_view, name='database'),
    path('empty/', views.empty_view, name='empty'),
]