from django.urls import path
from manager import views

urlpatterns = [
    path("", views.signin, name="login"),
    path("login", views.signin, name="login"),
    # path("register", views.signup, name="register"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("account-bank", views.accountBank, name="account-bank"),
    path("statements-account-bank", views.statementsAccountBank, name="statements-account-bank"),
    path("profil", views.profil, name="profil"),
    path("portfolio", views.portfolio, name="portfolio"),
    path("my-bakery", views.myBakery, name="my-bakery"),
    path("lep", views.lep, name="lep"),
    path('logout', views.logout_user, name='logout'),
    path("add-card", views.addCard, name="add-card"),
    path("update-card", views.updateCard, name="update-card"),
    path("delete-card", views.deleteCard, name="delete-card"),
    path("add-doc", views.addDoc, name="add-doc"),
]