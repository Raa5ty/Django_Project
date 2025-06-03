from django.contrib import admin
from django.urls import path, reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from tgservice.views import MainView, ProjectsView, ChannelsView # CBV
from tgservice import views # FBV

app_name = 'tgservice'

urlpatterns = [
    path('login/', LoginView.as_view(template_name='tgservice/login.html'), name='login'),
    path('', MainView.as_view(), name='main'), # CBV
    
    path('download-excel/<int:project_id>/', views.download_excel, name='download_excel'),

    path('search/', views.search_view, name='search'),
    path('projects/', ProjectsView.as_view(), name='projects'),
    path('channels/', ChannelsView.as_view(), name='channels'),
    path('empty/', views.empty_view, name='empty'),
    path('logout/', LogoutView.as_view(), name='logout'),
   
]