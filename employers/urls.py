from django.urls import path

from .views import EmployerDetailView, MeEmployerView

urlpatterns = [
    path('me/', MeEmployerView.as_view(), name='employer-me'),
    path('<int:pk>/', EmployerDetailView.as_view(), name='employer-detail'),
]
