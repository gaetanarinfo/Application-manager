# import Http Response from django
from getpass import getuser
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.models import Projets, UsersOthers, ProjetsUsers
from django.contrib import messages
import requests
from requests.structures import CaseInsensitiveDict
from dotenv import load_dotenv
import os
from .forms import UpdateUserForm
import json

load_dotenv()


# Home page
def home(request):
    context = {"title": "Applications manager"}
    return render(request, "pages/home.html", context)


def sort_by_key(list):
    return list["created_at"]


def update_by_key(list):
    return list["settled_at"].strftime("%d/%m/%Y")


# Dashboard page
def dashboard(request):
    if request.user.is_authenticated:
        # Github
        url = "https://api.github.com/users/gaetanarinfo/repos"
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json; charset=utf-8"
        headers["Authorization"] = "Bearer " + os.environ.get("KEY_GITHUB")
        resp = requests.get(url, headers=headers)
        data_json = resp.json()
        url2 = "https://api.github.com/users/gaetanarinfo"
        resp2 = requests.get(url2, headers=headers)
        data_json2 = resp2.json()

        # Qonto
        url2 = "https://thirdparty.qonto.com/v2/organization"
        headers2 = CaseInsensitiveDict()
        headers2["Accept"] = "application/json; charset=utf-8"
        headers2["Authorization"] = os.environ.get("KEY_QONTO")
        resp2 = requests.get(url2, headers=headers2)
        data_json3 = resp2.json()
        url3 = (
            "https://thirdparty.qonto.com/v2/transactions?iban="
            + data_json3["organization"]["bank_accounts"][0]["iban"]
        )
        headers3 = CaseInsensitiveDict()
        headers3["Accept"] = "application/json; charset=utf-8"
        headers3["Authorization"] = os.environ.get("KEY_QONTO")
        resp3 = requests.get(url3, headers=headers3)
        data_json4 = resp3.json()

        # Manage in models.py
        projets = (
            Projets.objects.using("portfolio_db")
            .filter(active=1)
            .order_by("-created_at")
            .all()
        )
        projetsCount = Projets.objects.using("portfolio_db").filter(active=1).count()
        userProjetsCount = UsersOthers.objects.using("portfolio_db").count()
        userLepCount = UsersOthers.objects.using("lep_db").count()
        userMyBakeryCount = UsersOthers.objects.using("mybakery_db").count()
        websiteCount = (
            Projets.objects.using("portfolio_db")
            .filter(categorie="template", appart_dev72=1)
            .count()
        )
        websites = (
            Projets.objects.using("portfolio_db")
            .filter(categorie="template", appart_dev72=1)
            .order_by("-created_at")
            .all()
        )

        # create a dictionary to pass
        # data to the template
        context = {
            "title": "Applications manager",
            "projets": projets,
            "counterProjets": projetsCount,
            "userProjetsCount": userProjetsCount + userLepCount + userMyBakeryCount,
            "websiteCount": websiteCount,
            "githubs": sorted(data_json, key=sort_by_key, reverse=True),
            "githubsCount": data_json2["public_repos"],
            "githubProfil": data_json2,
            "balanceQonto": data_json3["organization"]["bank_accounts"][0][
                "authorized_balance"
            ],
            "qontoList": data_json4["transactions"][0:12],
            "staffUser": request.user.is_staff,
            "page": "Accueil",
            "websites": websites,
        }
        # return response with template and context
        return render(request, "pages/dashboard.html", context)
    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


# Profil page
def profil(request):
    # Manage in models.py
    projets = (
        Projets.objects.using("portfolio_db")
        .filter(active=1, author=request.user.username)
        .order_by("-created_at")
        .all()
    )

    if request.user.is_authenticated:
        list = []
        for i in range(21):
            list.append(i)

        number = request.user.banner.replace("curved", "")
        number = number.replace(".jpg", "")

        # return response with template and context
        context = {
            "title": "Mon profil - Applications manager",
            "page": "Profil",
            "list": list,
            "number": int(number),
            "projets": projets,
        }

        if request.method == "POST":
            user_form = UpdateUserForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                msg = "Votre profil a bien été modifiée !"
                context = {
                    "title": "Mon profil - Applications manager",
                    "page": "Profil",
                    "msg": msg,
                    "list": list,
                    "number": int(number),
                    "msg_status": "success",
                }
                return render(request, "pages/profil.html", context)
            else:
                msg = "Une erreur est survenu sur votre profil !"
                context = {
                    "title": "Mon profil - Applications manager",
                    "page": "Profil",
                    "msg": msg,
                    "list": list,
                    "number": int(number),
                    "msg_status": "danger",
                }
                return render(request, "pages/profil.html", context)

        return render(request, "pages/profil.html", context)
    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


# Login page
def signin(request):
    if request.user.is_authenticated:
        context = {"title": "Applications manager", "page": "Accueil"}
        # return response with template and context
        return render(request, "pages/dashboard.html", context)
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            context = {"title": "Applications manager", "page": "Accueil"}
            # return response with template and context
            return redirect("/dashboard", context)
        else:
            msg = "Votre identifiant ou votre mot de passe est incorrect !"
            form = AuthenticationForm(request.POST)
            context = {
                "title": "Connexion - Applications manager",
                "form": form,
                "msg": msg,
            }
            return render(request, "pages/sign-in.html", context)
    # In the `signup` function, the `else` block is executed when the HTTP request method is not
    # `POST`. It renders the sign-up page with an empty `UserCreationForm` and a context dictionary
    # containing the page title and the form.
    else:
        form = AuthenticationForm()
        context = {"title": "Connexion - Applications manager", "form": form}
        return render(request, "pages/sign-in.html", context)


# Register page
def signup(request):  # sourcery skip: extract-method, remove-unnecessary-else
    if request.user.is_authenticated:
        return redirect("/login")

    if request.method == "POST":
        user = User.objects.exists()

        if user:
            username = request.POST["username"]
            password = request.POST["password1"]

            user_email = user.email
            user_username = user.username
            if (
                user_username != request.POST["username"]
                and user.get_email() != request.POST["email"]
            ):
                form = UserCreationForm(request.POST)

                form.save()

                return redirect("/login")
            elif user_email == request.POST["email"]:
                msg = "Votre adresse email est déjà présent dans notre base !"
                form = UserCreationForm(request.POST)
                context = {
                    "title": "Inscription - Applications manager",
                    "form": form,
                    "msg": msg,
                }
                return render(request, "pages/sign-up.html", context)
            else:
                msg = "Votre identifiant est déjà présent dans notre base !"
                form = UserCreationForm(request.POST)
                context = {
                    "title": "Inscription - Applications manager",
                    "form": form,
                    "msg": msg,
                }
                return render(request, "pages/sign-up.html", context)
        else:
            form = UserCreationForm(request.POST)
            form.save()
            context = {
                "title": "Inscription - Applications manager",
                "form": form,
            }
            return redirect("/login")
    else:
        context = {
            "title": "Inscription - Applications manager",
        }
        return render(request, "pages/sign-up.html", context)


# Logout page
def logout_user(request):
    logout(request)
    messages.info(request, "Vous vous êtes déconnecté avec succès.")
    return redirect("/")


# 404 page
def handler404(request):
    context = {"title": "404 - Applications manager", "page": "404", "reponse": "404"}
    return render(request, "pages/404.html", context)


# 500 page
def handler500(request):
    context = {"title": "404 - Applications manager", "page": "404", "reponse": "404"}
    return render(request, "pages/404.html", context)


def portfolio(request):
    arrayPortfolioConfig = {}
    arrayPortfolioConfigClient = {}
    
    # File .env in portfolio
    path = "/var/www/portfolio-back/.env"
    with open(path) as fn:
        for line in fn:
            key, desc = line.strip().split("=", 1)
            desc = desc.replace('"', "")
            arrayPortfolioConfig[key] = desc.strip()

    path = "/var/www/portfolio/.env"
    with open(path) as fn:
        for line in fn:
            key, desc = line.strip().split("=", 1)
            arrayPortfolioConfigClient[key] = desc.strip()
            
    projets = (
        Projets.objects.using("portfolio_db")
        .filter(active=1)
        .order_by("-created_at")
        .all()
    )
    
    projetsCount = (
        Projets.objects.using("portfolio_db")
        .filter(active=1, author=request.user.username)
        .count()
    )
    
    usersProjets = (
        ProjetsUsers.objects.using("portfolio_db")
        .filter(active=1)
        .order_by("-created_at")
        .all()
    )

    context = {
        "title": "Portfolio - Applications manager",
        "page": "Portfolio",
        "counterProjets": projetsCount,
        "projets": projets,
        "usersProjets": usersProjets,
        "configPortfolio": arrayPortfolioConfig,
        "configPortfolioClient": arrayPortfolioConfigClient,
    }
    return render(request, "pages/portfolio.html", context)
