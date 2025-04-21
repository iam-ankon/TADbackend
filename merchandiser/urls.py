from django.urls import path
from . import views

urlpatterns = [
    # Customer URLs
    path('customers/', views.CustomerListCreateView.as_view(), name='customer-list'),
    path('customers/<int:pk>/', views.CustomerRetrieveUpdateDestroyView.as_view(), name='customer-detail'),
    
    # Agent URLs
    path('agents/', views.AgentListCreateView.as_view(), name='agent-list'),
    path('agents/<int:pk>/', views.AgentRetrieveUpdateDestroyView.as_view(), name='agent-detail'),
    
    # Supplier URLs
    path('suppliers/', views.SupplierListCreateView.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', views.SupplierRetrieveUpdateDestroyView.as_view(), name='supplier-detail'),

    # Buyer URLs
    path('buyers/', views.BuyerListCreateView.as_view(), name='buyer-list'),
    path('buyers/<int:pk>/', views.BuyerRetrieveUpdateDestroyView.as_view(), name='buyer-detail'),

]