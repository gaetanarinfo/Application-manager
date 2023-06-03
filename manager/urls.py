from django.urls import path
from manager import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login", views.signin, name="login"),
    path("register", views.signup, name="register"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("account-bank", views.accountBank, name="account-bank"),
    path("statements-account-bank", views.statementsAccountBank, name="statements-account-bank"),
    path("profil", views.profil, name="profil"),
    path("portfolio", views.portfolio, name="portfolio"),
    path('logout', views.logout_user, name='logout'),
]