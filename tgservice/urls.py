from django.contrib import admin
from django.urls import path
from tgservice import views # FBV
from .views import MainView, ProjectsView, ChannelsView # CBV


app_name = 'tgservice'

urlpatterns = [
    path('', MainView.as_view(), name='main'), # CBV
    path('search/', views.search_view, name='search'),
    path('projects/', ProjectsView.as_view(), name='projects'),
    path('channels/', ChannelsView.as_view(), name='channels'),
    path('empty/', views.empty_view, name='empty'),
]