from django.urls import path
from . import views

app_name = 'search_app'  # Add namespace

urlpatterns = [
    path('', views.search_view, name='search'),
    path('search/<str:query>', views.search_view, name='search_with_query'),
    path('search/doc/<str:doc_id>', views.document_view, name='document_detail'),
    # You can add more URL patterns here
]