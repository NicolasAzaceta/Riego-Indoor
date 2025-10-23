from django.urls import path
from .views import home, index_view, add_view, detail_view, login_view, register_view, privacy_view, terms_view


urlpatterns = [
    # La raíz del sitio (riegoindoor.com/) muestra la bienvenida
    path('', home, name='home'),

    path('dashboard/', index_view, name='dashboard'),
    path('add/', add_view, name='add_plant'),
    path('detail/', detail_view, name='detail_plant'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('privacy/', privacy_view, name='privacy'),
    path('terms/', terms_view, name='terms'),
]