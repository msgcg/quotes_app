from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_random_quote, name='random_quote'),
    path('random/', views.get_random_quote, name='random_quote'),
    path('popular/', views.get_popular_quotes, name='popular_quotes'),
    path('add_quote/', views.add_quote, name='add_quote'),
    path('add_source/', views.add_source, name='add_source'),
    path('like/<int:quote_id>/', views.like_quote, name='like_quote'),
    path('dislike/<int:quote_id>/', views.dislike_quote, name='dislike_quote'),
    path('dashboard/', views.dashboard, name='dashboard'),
]