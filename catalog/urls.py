from django.urls import path
from . import views, api_views, wompi_views

app_name = 'catalog'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('tienda/', views.ProductListView.as_view(), name='product_list'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('brand/<slug:slug>/', views.BrandDetailView.as_view(), name='brand_detail'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('search/', views.ProductSearchView.as_view(), name='product_search'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.CartAddView.as_view(), name='cart_add'),
    path('cart/remove/<int:item_id>/', views.CartRemoveView.as_view(), name='cart_remove'),
    path('cart/update/<int:item_id>/', views.CartUpdateView.as_view(), name='cart_update'),
    path('login/', views.FrontendLoginView.as_view(), name='login'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('checkout/login/', views.CheckoutLoginView.as_view(), name='checkout_login'),
    path('checkout/register/', views.CheckoutRegisterView.as_view(), name='checkout_register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('checkout/success/<int:order_id>/', views.CheckoutSuccessView.as_view(), name='checkout_success'),
    path('checkout/wompi/create/<int:order_id>/', views.WompiCreateTransactionView.as_view(), name='wompi_create_transaction'),
    path('wompi/webhook/', wompi_views.wompi_webhook, name='wompi_webhook'),
    
    # API URLs
    path('api/products/', api_views.product_list_api, name='api_products'),
    path('api/locations/countries/', api_views.location_countries_api, name='api_location_countries'),
    path('api/locations/departments/', api_views.location_departments_api, name='api_location_departments'),
    path('api/locations/cities/', api_views.location_cities_api, name='api_location_cities'),
]


