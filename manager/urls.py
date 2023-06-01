from django.urls import path
from manager import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login", views.signin, name="login"),
    path("register", views.signup, name="register"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("profil", views.profil, name="profil"),
    path('logout', views.logout_user, name='logout'),
]