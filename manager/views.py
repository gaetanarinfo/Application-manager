# import Http Response from django
from getpass import getuser
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, CreateCardForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.models import (
    Projets,
    UsersOthers,
    ProjetsUsers,
    News,
    UsersCards,
    usersStatements,
    Orders,
    Products,
    NewsBakery,
    RatingsBakery,
    NewsLEP,
    Salarys,
)
from django.contrib import messages
import requests
from requests.structures import CaseInsensitiveDict
from dotenv import load_dotenv
import os
from .forms import UpdateUserForm
from .forms import UpdateCardForm
from .forms import CreateDocForm
from .forms import CreateDocSalarysForm
from datetime import datetime
from django.utils import timezone
from django.db import connections
import pytz
from django.core.files.storage import FileSystemStorage
from django.db.models import Avg, Max, Min, Sum
import json
import math

load_dotenv()


def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


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
        return redirect("/dashboard")
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
# def signup(request):  # sourcery skip: extract-method, remove-unnecessary-else
#     if request.user.is_authenticated:
#         return redirect("/login")

#     if request.method == "POST":
#         user = User.objects.exists()

#         if user:
#             username = request.POST["username"]
#             password = request.POST["password1"]

#             user_email = user.email
#             user_username = user.username
#             if (
#                 user_username != request.POST["username"]
#                 and user.get_email() != request.POST["email"]
#             ):
#                 form = UserCreationForm(request.POST)

#                 form.save()

#                 return redirect("/login")
#             elif user_email == request.POST["email"]:
#                 msg = "Votre adresse email est déjà présent dans notre base !"
#                 form = UserCreationForm(request.POST)
#                 context = {
#                     "title": "Inscription - Applications manager",
#                     "form": form,
#                     "msg": msg,
#                 }
#                 return render(request, "pages/sign-up.html", context)
#             else:
#                 msg = "Votre identifiant est déjà présent dans notre base !"
#                 form = UserCreationForm(request.POST)
#                 context = {
#                     "title": "Inscription - Applications manager",
#                     "form": form,
#                     "msg": msg,
#                 }
#                 return render(request, "pages/sign-up.html", context)
#         else:
#             form = UserCreationForm(request.POST)
#             form.save()
#             context = {
#                 "title": "Inscription - Applications manager",
#                 "form": form,
#             }
#             return redirect("/login")
#     else:
#         context = {
#             "title": "Inscription - Applications manager",
#         }
#         return render(request, "pages/sign-up.html", context)


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
    if request.user.is_authenticated:
        if request.user.is_staff:
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

            news = (
                News.objects.using("portfolio_db")
                .filter(active=1)
                .order_by("-created_at")
                .all()
            )

            # Projects Portfolio
            counterPaiementOk = (
                Orders.objects.using("portfolio_db").filter(status="COMPLETED").count()
            )
            counterPaiementCancel = (
                Orders.objects.using("portfolio_db").filter(status="CANCELED").count()
            )
            counterPaiementRefund = (
                Orders.objects.using("portfolio_db").filter(status="REFUND").count()
            )
            totalProjectOrders = (
                Orders.objects.using("portfolio_db")
                .filter(status="COMPLETED")
                .aggregate(Sum("price", distinct=True))
            )
            cursor = connections["portfolio_db"].cursor()
            cursor.execute("call OrdersView()")
            orders = dictfetchall(cursor)
            products = (
                Products.objects.using("portfolio_db").order_by("-product_id").all()
            )

            # Forum Portfolio
            cursor = connections["portfolio_db"].cursor()
            cursor.execute("call Forums()")
            forums = dictfetchall(cursor)

            cursor = connections["portfolio_db"].cursor()
            cursor.execute("call ForumsTopics()")
            forums_topics = dictfetchall(cursor)

            context = {
                "title": "Portfolio - Applications manager",
                "page": "Portfolio",
                "counterProjets": projetsCount,
                "projets": projets,
                "usersProjets": usersProjets,
                "configPortfolio": arrayPortfolioConfig,
                "configPortfolioClient": arrayPortfolioConfigClient,
                "news": news,
                "counterPaiementOk": counterPaiementOk,
                "counterPaiementCancel": counterPaiementCancel,
                "counterPaiementRefund": counterPaiementRefund,
                "totalProjectOrders": totalProjectOrders["price__sum"],
                "orders": orders,
                "products": products,
                "forums": forums,
                "forums_topics": forums_topics,
            }
            return render(request, "pages/portfolio.html", context)
        else:
            return redirect("/dashboard")
    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


def accountBank(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            usersCards = (
                UsersCards.objects.using("auth_db")
                .filter(user_id=request.user.id)
                .order_by("-id")
                .all()
            )

            if usersCards.count() != 0:
                userCard = (
                    UsersCards.objects.using("auth_db")
                    .filter(user_id=request.user.id)
                    .order_by("-id")
                    .all()
                )
            else:
                userCard = []

            usersStatement = (
                usersStatements.objects.using("auth_db")
                .filter(user_id=request.user.id)
                .order_by("-created_at")
                .all()
            )

            month = [
                "janvier",
                "février",
                "mars",
                "avril",
                "mai",
                "juin",
                "juillet",
                "août",
                "septembre",
                "octobre",
                "noveambre",
                "décembre",
            ]
            dataEntrees = []
            dataSorties = []

            if request.GET.get("year"):
                year = request.GET.get("year")
            else:
                today = timezone.now()
                year = today.strftime("%Y")

            for value in month:
                if usersStatements.objects.filter(date=value + " " + year).exists():
                    usersEntreesChart = (
                        usersStatements.objects.using("auth_db")
                        .values("entrees")
                        .filter(user_id=request.user.id, date=value + " " + year)
                        .annotate(entree=Avg("entrees"))
                        .order_by("date")
                        .get()
                    )
                    dataEntrees.append(usersEntreesChart["entree"])
                else:
                    dataEntrees.append(0)
                    None

                if usersStatements.objects.filter(date=value + " " + year).exists():
                    usersSortiesChart = (
                        usersStatements.objects.using("auth_db")
                        .values("sorties")
                        .filter(user_id=request.user.id, date=value + " " + year)
                        .annotate(entree=Avg("sorties"))
                        .order_by("date")
                        .get()
                    )
                    dataSorties.append(usersSortiesChart["entree"])
                else:
                    dataSorties.append(0)
                    None

                pass

            if request.GET.get("page") != None:
                page_get = request.GET.get("page")
            else:
                page_get = "1"

            # Qonto
            url = "https://thirdparty.qonto.com/v2/organization"
            headers = CaseInsensitiveDict()
            headers["Accept"] = "application/json; charset=utf-8"
            headers["Authorization"] = os.environ.get("KEY_QONTO")
            resp = requests.get(url, headers=headers)
            data_json = resp.json()
            url3 = (
                "https://thirdparty.qonto.com/v2/transactions?iban="
                + data_json["organization"]["bank_accounts"][0]["iban"]
                + "&per_page=100&current_page="
                + page_get
            )
            headers3 = CaseInsensitiveDict()
            headers3["Accept"] = "application/json; charset=utf-8"
            headers3["Authorization"] = os.environ.get("KEY_QONTO")
            resp3 = requests.get(url3, headers=headers3)
            data_json4 = resp3.json()

            totalPage = (data_json4["meta"]["total_count"]) / 100

            list = []
            for i in range(round(totalPage) + 1):
                if i != 0:
                    list.append(i)

            page_number = page_get
            page_before_number = int(page_get) - 1
            page_after_number = int(page_get) + 1

            userCardCount = UsersCards.objects.using("auth_db").count()

            context = {
                "title": "Compte bancaire - Applications manager",
                "page": "Compte bancaire",
                "usersCards": usersCards,
                "userCard": userCard,
                "userCardCcaount": userCardCount,
                "balanceQonto": data_json["organization"]["bank_accounts"][0][
                    "authorized_balance"
                ],
                "usersStatement": usersStatement[0:5],
                "qontoList": data_json4["transactions"][0:100],
                "qontoListPaginationTotalPage": list,
                "page_number": int(page_number),
                "page_before_number": page_before_number,
                "page_after_number": page_after_number,
                "total_page": round(totalPage),
                "dataEntrees": dataEntrees,
                "dataSorties": dataSorties,
            }

            return render(request, "pages/account-bank.html", context)
        else:
            return redirect("/dashboard")
    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


def statementsAccountBank(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            usersStatement = (
                usersStatements.objects.using("auth_db")
                .filter(user_id=request.user.id)
                .order_by("-created_at")
                .all()
            )

            context = {
                "title": "Relevés de compte bancaire - Applications manager",
                "page": "Relevés de compte bancaire",
                "usersStatement": usersStatement,
            }
            return render(request, "pages/statements-account-bank.html", context)
        else:
            return redirect("/dashboard")
    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


def addCard(request):
    if request.user.is_staff:
        usersCards = (
            UsersCards.objects.using("auth_db")
            .filter(user_id=request.user.id)
            .order_by("-id")
            .all()
        )

        if usersCards.count() != 0:
            userCard = (
                UsersCards.objects.using("auth_db")
                .filter(user_id=request.user.id)
                .order_by("-id")
                .all()
            )
        else:
            userCard = []

        usersStatement = (
            usersStatements.objects.using("auth_db")
            .filter(user_id=request.user.id)
            .order_by("-created_at")
            .all()
        )

        if request.GET.get("page") != None:
            page_get = request.GET.get("page")
        else:
            page_get = "1"

        month = [
            "janvier",
            "février",
            "mars",
            "avril",
            "mai",
            "juin",
            "juillet",
            "août",
            "septembre",
            "octobre",
            "noveambre",
            "décembre",
        ]
        dataEntrees = []
        dataSorties = []

        if request.GET.get("year"):
            year = request.GET.get("year")
        else:
            today = timezone.now()
            year = today.strftime("%Y")

        for value in month:
            if usersStatements.objects.filter(date=value + " " + year).exists():
                usersEntreesChart = (
                    usersStatements.objects.using("auth_db")
                    .values("entrees")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("entrees"))
                    .order_by("date")
                    .get()
                )
                dataEntrees.append(usersEntreesChart["entree"])
            else:
                dataEntrees.append(0)
                None

            if usersStatements.objects.filter(date=value + " " + year).exists():
                usersSortiesChart = (
                    usersStatements.objects.using("auth_db")
                    .values("sorties")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("sorties"))
                    .order_by("date")
                    .get()
                )
                dataSorties.append(usersSortiesChart["entree"])
            else:
                dataSorties.append(0)
                None

            pass

        if request.GET.get("page") != None:
            page_get = request.GET.get("page")
        else:
            page_get = "1"

        # Qonto
        url = "https://thirdparty.qonto.com/v2/organization"
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json; charset=utf-8"
        headers["Authorization"] = os.environ.get("KEY_QONTO")
        resp = requests.get(url, headers=headers)
        data_json = resp.json()
        url3 = (
            "https://thirdparty.qonto.com/v2/transactions?iban="
            + data_json["organization"]["bank_accounts"][0]["iban"]
            + "&per_page=100&current_page="
            + page_get
        )
        headers3 = CaseInsensitiveDict()
        headers3["Accept"] = "application/json; charset=utf-8"
        headers3["Authorization"] = os.environ.get("KEY_QONTO")
        resp3 = requests.get(url3, headers=headers3)
        data_json4 = resp3.json()

        totalPage = (data_json4["meta"]["total_count"]) / 100

        list = []
        for i in range(round(totalPage) + 1):
            if i != 0:
                list.append(i)

        page_number = page_get
        page_before_number = int(page_get) - 1
        page_after_number = int(page_get) + 1

        userCardCount = UsersCards.objects.using("auth_db").count()

        context = {
            "title": "Compte bancaire - Applications manager",
            "page": "Compte bancaire",
            "usersCards": usersCards,
            "userCard": userCard,
            "userCardCcaount": userCardCount,
            "balanceQonto": data_json["organization"]["bank_accounts"][0][
                "authorized_balance"
            ],
            "usersStatement": usersStatement[0:5],
            "qontoList": data_json4["transactions"][0:100],
            "qontoListPaginationTotalPage": list,
            "page_number": int(page_number),
            "page_before_number": page_before_number,
            "page_after_number": page_after_number,
            "total_page": round(totalPage),
            "dataEntrees": dataEntrees,
            "dataSorties": dataSorties,
        }

        if request.method == "POST":
            card_form = CreateCardForm(request.POST)
            if card_form.is_valid():
                card_form.save()
                msg = "Votre carte a bien été ajoutée !"
                context = {
                    "title": "Compte bancaire - Applications manager",
                    "page": "Compte bancaire",
                    "usersCards": usersCards,
                    "userCardCcaount": userCardCount,
                    "userCard": userCard,
                    "balanceQonto": data_json["organization"]["bank_accounts"][0][
                        "authorized_balance"
                    ],
                    "usersStatement": usersStatement[0:5],
                    "qontoList": data_json4["transactions"][0:100],
                    "qontoListPaginationTotalPage": list,
                    "page_number": int(page_number),
                    "page_before_number": page_before_number,
                    "page_after_number": page_after_number,
                    "total_page": round(totalPage),
                    "msg": msg,
                    "msg_status": "success",
                    "dataEntrees": dataEntrees,
                    "dataSorties": dataSorties,
                }
                return render(request, "pages/account-bank.html", context)
            else:
                msg = "Une erreur est survenu !"
                context = {
                    "title": "Compte bancaire - Applications manager",
                    "page": "Compte bancaire",
                    "usersCards": usersCards,
                    "userCardCcaount": userCardCount,
                    "userCard": userCard,
                    "balanceQonto": data_json["organization"]["bank_accounts"][0][
                        "authorized_balance"
                    ],
                    "usersStatement": usersStatement[0:5],
                    "qontoList": data_json4["transactions"][0:100],
                    "qontoListPaginationTotalPage": list,
                    "page_number": int(page_number),
                    "page_before_number": page_before_number,
                    "page_after_number": page_after_number,
                    "total_page": round(totalPage),
                    "msg": msg,
                    "msg_status": "danger",
                    "dataEntrees": dataEntrees,
                    "dataSorties": dataSorties,
                }
                return render(request, "pages/account-bank.html", context)

    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


def updateCard(request):
    if request.user.is_staff:
        usersCards = (
            UsersCards.objects.using("auth_db")
            .filter(user_id=request.user.id)
            .order_by("-id")
            .all()
        )

        if usersCards.count() != 0:
            userCard = (
                UsersCards.objects.using("auth_db")
                .filter(user_id=request.user.id)
                .order_by("-id")
                .all()
            )
        else:
            userCard = []

        usersStatement = (
            usersStatements.objects.using("auth_db")
            .filter(user_id=request.user.id)
            .order_by("-created_at")
            .all()
        )

        if request.GET.get("page") != None:
            page_get = request.GET.get("page")
        else:
            page_get = "1"

        month = [
            "janvier",
            "février",
            "mars",
            "avril",
            "mai",
            "juin",
            "juillet",
            "août",
            "septembre",
            "octobre",
            "noveambre",
            "décembre",
        ]
        dataEntrees = []
        dataSorties = []

        if request.GET.get("year"):
            year = request.GET.get("year")
        else:
            today = timezone.now()
            year = today.strftime("%Y")

        for value in month:
            if usersStatements.objects.filter(date=value + " " + year).exists():
                usersEntreesChart = (
                    usersStatements.objects.using("auth_db")
                    .values("entrees")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("entrees"))
                    .order_by("date")
                    .get()
                )
                dataEntrees.append(usersEntreesChart["entree"])
            else:
                dataEntrees.append(0)
                None

            if usersStatements.objects.filter(date=value + " " + year).exists():
                usersSortiesChart = (
                    usersStatements.objects.using("auth_db")
                    .values("sorties")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("sorties"))
                    .order_by("date")
                    .get()
                )
                dataSorties.append(usersSortiesChart["entree"])
            else:
                dataSorties.append(0)
                None

            pass

        if request.GET.get("page") != None:
            page_get = request.GET.get("page")
        else:
            page_get = "1"

        # Qonto
        url = "https://thirdparty.qonto.com/v2/organization"
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json; charset=utf-8"
        headers["Authorization"] = os.environ.get("KEY_QONTO")
        resp = requests.get(url, headers=headers)
        data_json = resp.json()
        url3 = (
            "https://thirdparty.qonto.com/v2/transactions?iban="
            + data_json["organization"]["bank_accounts"][0]["iban"]
            + "&per_page=100&current_page="
            + page_get
        )
        headers3 = CaseInsensitiveDict()
        headers3["Accept"] = "application/json; charset=utf-8"
        headers3["Authorization"] = os.environ.get("KEY_QONTO")
        resp3 = requests.get(url3, headers=headers3)
        data_json4 = resp3.json()

        totalPage = (data_json4["meta"]["total_count"]) / 100

        list = []
        for i in range(round(totalPage) + 1):
            if i != 0:
                list.append(i)

        page_number = page_get
        page_before_number = int(page_get) - 1
        page_after_number = int(page_get) + 1

        userCardCount = UsersCards.objects.using("auth_db").count()

        context = {
            "title": "Compte bancaire - Applications manager",
            "page": "Compte bancaire",
            "usersCards": usersCards,
            "userCard": userCard,
            "userCardCcaount": userCardCount,
            "balanceQonto": data_json["organization"]["bank_accounts"][0][
                "authorized_balance"
            ],
            "usersStatement": usersStatement[0:5],
            "qontoList": data_json4["transactions"][0:100],
            "qontoListPaginationTotalPage": list,
            "page_number": int(page_number),
            "page_before_number": page_before_number,
            "page_after_number": page_after_number,
            "total_page": round(totalPage),
            "dataEntrees": dataEntrees,
            "dataSorties": dataSorties,
        }

        if request.method == "POST":
            band = UsersCards.objects.get(id=request.POST["id"])

            card_form = UpdateCardForm(request.POST, instance=band)
            print(request.POST["id"])
            if card_form.is_valid():
                card_form.save()
                msg = "Votre carte a bien été mise à jour !"
                context = {
                    "title": "Compte bancaire - Applications manager",
                    "page": "Compte bancaire",
                    "usersCards": usersCards,
                    "userCardCcaount": userCardCount,
                    "userCard": userCard,
                    "balanceQonto": data_json["organization"]["bank_accounts"][0][
                        "authorized_balance"
                    ],
                    "usersStatement": usersStatement[0:5],
                    "qontoList": data_json4["transactions"][0:100],
                    "qontoListPaginationTotalPage": list,
                    "page_number": int(page_number),
                    "page_before_number": page_before_number,
                    "page_after_number": page_after_number,
                    "total_page": round(totalPage),
                    "msg": msg,
                    "msg_status": "success",
                    "dataEntrees": dataEntrees,
                    "dataSorties": dataSorties,
                }
                return render(request, "pages/account-bank.html", context)
            else:
                msg = "Une erreur est survenu !"
                context = {
                    "title": "Compte bancaire - Applications manager",
                    "page": "Compte bancaire",
                    "usersCards": usersCards,
                    "userCardCcaount": userCardCount,
                    "userCard": userCard,
                    "balanceQonto": data_json["organization"]["bank_accounts"][0][
                        "authorized_balance"
                    ],
                    "usersStatement": usersStatement[0:5],
                    "qontoList": data_json4["transactions"][0:100],
                    "qontoListPaginationTotalPage": list,
                    "page_number": int(page_number),
                    "page_before_number": page_before_number,
                    "page_after_number": page_after_number,
                    "total_page": round(totalPage),
                    "msg": msg,
                    "msg_status": "danger",
                    "dataEntrees": dataEntrees,
                    "dataSorties": dataSorties,
                }
                return render(request, "pages/account-bank.html", context)

        return render(request, "pages/account-bank.html", context)
    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


def deleteCard(request):
    if request.user.is_staff:
        usersCards = (
            UsersCards.objects.using("auth_db")
            .filter(user_id=request.user.id)
            .order_by("-id")
            .all()
        )

        if usersCards.count() != 0:
            userCard = (
                UsersCards.objects.using("auth_db")
                .filter(user_id=request.user.id)
                .order_by("-id")
                .all()
            )
        else:
            userCard = []

        usersStatement = (
            usersStatements.objects.using("auth_db")
            .filter(user_id=request.user.id)
            .order_by("-created_at")
            .all()
        )

        if request.GET.get("page") != None:
            page_get = request.GET.get("page")
        else:
            page_get = "1"

        month = [
            "janvier",
            "février",
            "mars",
            "avril",
            "mai",
            "juin",
            "juillet",
            "août",
            "septembre",
            "octobre",
            "noveambre",
            "décembre",
        ]
        dataEntrees = []
        dataSorties = []

        if request.GET.get("year"):
            year = request.GET.get("year")
        else:
            today = timezone.now()
            year = today.strftime("%Y")

        for value in month:
            if usersStatements.objects.filter(date=value + " " + year).exists():
                usersEntreesChart = (
                    usersStatements.objects.using("auth_db")
                    .values("entrees")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("entrees"))
                    .order_by("date")
                    .get()
                )
                dataEntrees.append(usersEntreesChart["entree"])
            else:
                dataEntrees.append(0)
                None

            if usersStatements.objects.filter(date=value + " " + year).exists():
                usersSortiesChart = (
                    usersStatements.objects.using("auth_db")
                    .values("sorties")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("sorties"))
                    .order_by("date")
                    .get()
                )
                dataSorties.append(usersSortiesChart["entree"])
            else:
                dataSorties.append(0)
                None

            pass

        if request.GET.get("page") != None:
            page_get = request.GET.get("page")
        else:
            page_get = "1"

        # Qonto
        url = "https://thirdparty.qonto.com/v2/organization"
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json; charset=utf-8"
        headers["Authorization"] = os.environ.get("KEY_QONTO")
        resp = requests.get(url, headers=headers)
        data_json = resp.json()
        url3 = (
            "https://thirdparty.qonto.com/v2/transactions?iban="
            + data_json["organization"]["bank_accounts"][0]["iban"]
            + "&per_page=100&current_page="
            + page_get
        )
        headers3 = CaseInsensitiveDict()
        headers3["Accept"] = "application/json; charset=utf-8"
        headers3["Authorization"] = os.environ.get("KEY_QONTO")
        resp3 = requests.get(url3, headers=headers3)
        data_json4 = resp3.json()

        totalPage = (data_json4["meta"]["total_count"]) / 100

        list = []
        for i in range(round(totalPage) + 1):
            if i != 0:
                list.append(i)

        page_number = page_get
        page_before_number = int(page_get) - 1
        page_after_number = int(page_get) + 1

        userCardCount = UsersCards.objects.using("auth_db").count()

        context = {
            "title": "Compte bancaire - Applications manager",
            "page": "Compte bancaire",
            "usersCards": usersCards,
            "userCard": userCard,
            "userCardCcaount": userCardCount,
            "balanceQonto": data_json["organization"]["bank_accounts"][0][
                "authorized_balance"
            ],
            "usersStatement": usersStatement[0:5],
            "qontoList": data_json4["transactions"][0:100],
            "qontoListPaginationTotalPage": list,
            "page_number": int(page_number),
            "page_before_number": page_before_number,
            "page_after_number": page_after_number,
            "total_page": round(totalPage),
            "dataEntrees": dataEntrees,
            "dataSorties": dataSorties,
        }

        band = UsersCards.objects.get(id=request.POST["id"])

        if band != False:
            UsersCards.objects.filter(id=request.POST["id"]).delete()
            msg = "Votre carte a bien été supprimer !"
            context = {
                "title": "Compte bancaire - Applications manager",
                "page": "Compte bancaire",
                "usersCards": usersCards,
                "userCardCcaount": userCardCount,
                "userCard": userCard,
                "balanceQonto": data_json["organization"]["bank_accounts"][0][
                    "authorized_balance"
                ],
                "usersStatement": usersStatement[0:5],
                "qontoList": data_json4["transactions"][0:100],
                "qontoListPaginationTotalPage": list,
                "page_number": int(page_number),
                "page_before_number": page_before_number,
                "page_after_number": page_after_number,
                "total_page": round(totalPage),
                "msg": msg,
                "msg_status": "success",
                "dataEntrees": dataEntrees,
                "dataSorties": dataSorties,
            }
            return render(request, "pages/account-bank.html", context)
        else:
            msg = "Une erreur est survenu !"
            context = {
                "title": "Compte bancaire - Applications manager",
                "page": "Compte bancaire",
                "usersCards": usersCards,
                "userCardCcaount": userCardCount,
                "userCard": userCard,
                "balanceQonto": data_json["organization"]["bank_accounts"][0][
                    "authorized_balance"
                ],
                "usersStatement": usersStatement[0:5],
                "qontoList": data_json4["transactions"][0:100],
                "qontoListPaginationTotalPage": list,
                "page_number": int(page_number),
                "page_before_number": page_before_number,
                "page_after_number": page_after_number,
                "total_page": round(totalPage),
                "msg": msg,
                "msg_status": "danger",
                "dataEntrees": dataEntrees,
                "dataSorties": dataSorties,
            }
            return render(request, "pages/account-bank.html", context)

    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


def addDoc(request):
    if request.user.is_staff:
        usersCards = (
            UsersCards.objects.using("auth_db")
            .filter(user_id=request.user.id)
            .order_by("-id")
            .all()
        )

        if usersCards.count() != 0:
            userCard = (
                UsersCards.objects.using("auth_db")
                .filter(user_id=request.user.id)
                .order_by("-id")
                .all()
            )
        else:
            userCard = []

        usersStatement = (
            usersStatements.objects.using("auth_db")
            .filter(user_id=request.user.id)
            .order_by("-created_at")
            .all()
        )

        if request.GET.get("page") != None:
            page_get = request.GET.get("page")
        else:
            page_get = "1"

        month = [
            "janvier",
            "février",
            "mars",
            "avril",
            "mai",
            "juin",
            "juillet",
            "août",
            "septembre",
            "octobre",
            "noveambre",
            "décembre",
        ]
        dataEntrees = []
        dataSorties = []

        if request.GET.get("year"):
            year = request.GET.get("year")
        else:
            today = timezone.now()
            year = today.strftime("%Y")

        for value in month:
            if usersStatements.objects.filter(date=value + " " + year).exists():
                usersEntreesChart = (
                    usersStatements.objects.using("auth_db")
                    .values("entrees")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("entrees"))
                    .order_by("date")
                    .get()
                )
                dataEntrees.append(usersEntreesChart["entree"])
            else:
                dataEntrees.append(0)
                None

            if usersStatements.objects.filter(date=value + " " + year).exists():
                usersSortiesChart = (
                    usersStatements.objects.using("auth_db")
                    .values("sorties")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("sorties"))
                    .order_by("date")
                    .get()
                )
                dataSorties.append(usersSortiesChart["entree"])
            else:
                dataSorties.append(0)
                None

            pass

        if request.GET.get("page") != None:
            page_get = request.GET.get("page")
        else:
            page_get = "1"

        # Qonto
        url = "https://thirdparty.qonto.com/v2/organization"
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json; charset=utf-8"
        headers["Authorization"] = os.environ.get("KEY_QONTO")
        resp = requests.get(url, headers=headers)
        data_json = resp.json()
        url3 = (
            "https://thirdparty.qonto.com/v2/transactions?iban="
            + data_json["organization"]["bank_accounts"][0]["iban"]
            + "&per_page=100&current_page="
            + page_get
        )
        headers3 = CaseInsensitiveDict()
        headers3["Accept"] = "application/json; charset=utf-8"
        headers3["Authorization"] = os.environ.get("KEY_QONTO")
        resp3 = requests.get(url3, headers=headers3)
        data_json4 = resp3.json()

        totalPage = (data_json4["meta"]["total_count"]) / 100

        list = []
        for i in range(round(totalPage) + 1):
            if i != 0:
                list.append(i)

        page_number = page_get
        page_before_number = int(page_get) - 1
        page_after_number = int(page_get) + 1

        userCardCount = UsersCards.objects.using("auth_db").count()

        context = {
            "title": "Compte bancaire - Applications manager",
            "page": "Compte bancaire",
            "usersCards": usersCards,
            "userCard": userCard,
            "userCardCcaount": userCardCount,
            "balanceQonto": data_json["organization"]["bank_accounts"][0][
                "authorized_balance"
            ],
            "usersStatement": usersStatement[0:5],
            "qontoList": data_json4["transactions"][0:100],
            "qontoListPaginationTotalPage": list,
            "page_number": int(page_number),
            "page_before_number": page_before_number,
            "page_after_number": page_after_number,
            "total_page": round(totalPage),
            "dataEntrees": dataEntrees,
            "dataSorties": dataSorties,
        }

        if request.method == "POST":
            doc_form = CreateDocForm(request.POST, request.FILES)
            if doc_form.is_valid():
                myfile = request.FILES["doc"]
                fs = FileSystemStorage()
                fs.save("static/statements/" + myfile.name, myfile)
                doc_form.save()
                msg = "Votre document a bien été ajoutée !"
                context = {
                    "title": "Compte bancaire - Applications manager",
                    "page": "Compte bancaire",
                    "usersCards": usersCards,
                    "userCardCcaount": userCardCount,
                    "userCard": userCard,
                    "balanceQonto": data_json["organization"]["bank_accounts"][0][
                        "authorized_balance"
                    ],
                    "usersStatement": usersStatement[0:5],
                    "qontoList": data_json4["transactions"][0:100],
                    "qontoListPaginationTotalPage": list,
                    "page_number": int(page_number),
                    "page_before_number": page_before_number,
                    "page_after_number": page_after_number,
                    "total_page": round(totalPage),
                    "msg": msg,
                    "msg_status": "success",
                    "dataEntrees": dataEntrees,
                    "dataSorties": dataSorties,
                }
                return render(request, "pages/account-bank.html", context)
            else:
                msg = "Une erreur est survenu !"
                context = {
                    "title": "Compte bancaire - Applications manager",
                    "page": "Compte bancaire",
                    "usersCards": usersCards,
                    "userCardCcaount": userCardCount,
                    "userCard": userCard,
                    "balanceQonto": data_json["organization"]["bank_accounts"][0][
                        "authorized_balance"
                    ],
                    "usersStatement": usersStatement[0:5],
                    "qontoList": data_json4["transactions"][0:100],
                    "qontoListPaginationTotalPage": list,
                    "page_number": int(page_number),
                    "page_before_number": page_before_number,
                    "page_after_number": page_after_number,
                    "total_page": round(totalPage),
                    "msg": msg,
                    "msg_status": "danger",
                    "dataEntrees": dataEntrees,
                    "dataSorties": dataSorties,
                }
                return render(request, "pages/account-bank.html", context)

    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


def myBakery(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            # Blog
            news = NewsBakery.objects.using("mybakery_db").order_by("-created_at").all()

            # Rating
            bakeryRatings = (
                RatingsBakery.objects.using("mybakery_db").order_by("-created_at").all()
            )

            if request.GET.get("page") != None:
                page_get = request.GET.get("page")
            else:
                page_get = int(1)

            parPage = 100
            premier = int(int(page_get) * parPage) - parPage

            cursor = connections["mybakery_db"].cursor()
            cursor.execute("call Bakerys(" + str(premier) + ", 100)")
            bakerys = dictfetchall(cursor)

            cursor.execute("call BakerysCount()")
            bakerysCount = dictfetchall(cursor)

            totalPage = math.ceil((bakerysCount[0]["counter"]) / 100)

            list = []
            for i in range(totalPage + 1):
                if i != 0:
                    list.append(i)

            page_number = page_get
            page_before_number = int(page_get) - 1
            page_after_number = int(page_get) + 1

            context = {
                "title": "My bakery - Applications manager",
                "page": "My bakery",
                "news": news,
                "bakerys": bakerys,
                "bakeryListPaginationTotalPage": list,
                "page_number": int(page_number),
                "page_before_number": page_before_number,
                "page_after_number": page_after_number,
                "total_page": totalPage,
                "bakeryRatings": bakeryRatings,
            }
            return render(request, "pages/my-bakery.html", context)

        else:
            return redirect("/dashboard")
    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


def lep(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            # Blog
            news = NewsLEP.objects.using("lep_db").order_by("-created_at").all()

            context = {
                "title": "LEP - Applications manager",
                "page": "LEP Location entre particulier",
                "news": news,
            }
            return render(request, "pages/lep.html", context)
        else:
            return redirect("/dashboard")
    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


def salarys(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            # Salaires
            salarysList = Salarys.objects.using("auth_db").order_by("-id").all()

            month = [
                "janvier",
                "février",
                "mars",
                "avril",
                "mai",
                "juin",
                "juillet",
                "août",
                "septembre",
                "octobre",
                "noveambre",
                "décembre",
            ]
            dataEntrees = []
            dataSorties = []

            if request.GET.get("year"):
                year = request.GET.get("year")
            else:
                today = timezone.now()
                year = today.strftime("%Y")

            for value in month:
                if Salarys.objects.filter(date=value + " " + year).exists():
                    usersEntreesChart = (
                        Salarys.objects.using("auth_db")
                        .values("brut")
                        .filter(user_id=request.user.id, date=value + " " + year)
                        .annotate(entree=Avg("brut"))
                        .order_by("date")
                        .get()
                    )
                    dataEntrees.append(usersEntreesChart["brut"])
                else:
                    dataEntrees.append(0)
                    None

                if Salarys.objects.filter(date=value + " " + year).exists():
                    usersSortiesChart = (
                        Salarys.objects.using("auth_db")
                        .values("net")
                        .filter(user_id=request.user.id, date=value + " " + year)
                        .annotate(entree=Avg("net"))
                        .order_by("date")
                        .get()
                    )
                    dataSorties.append(usersSortiesChart["net"])
                else:
                    dataSorties.append(0)
                    None

                pass

            dataEntrees2 = []
            dataSorties2 = []

            if request.GET.get("year"):
                year = request.GET.get("year")
            else:
                today = timezone.now()
                year = today.strftime("%Y")

            for value in month:
                if Salarys.objects.filter(date=value + " " + year).exists():
                    usersEntreesChart = (
                        Salarys.objects.using("auth_db")
                        .values("hours")
                        .filter(user_id=request.user.id, date=value + " " + year)
                        .annotate(entree=Avg("hours"))
                        .order_by("date")
                        .get()
                    )
                    dataEntrees2.append(usersEntreesChart["hours"])
                else:
                    dataEntrees2.append(0)
                    None

                if Salarys.objects.filter(date=value + " " + year).exists():
                    usersSortiesChart = (
                        Salarys.objects.using("auth_db")
                        .values("total_hours")
                        .filter(user_id=request.user.id, date=value + " " + year)
                        .annotate(entree=Avg("total_hours"))
                        .order_by("date")
                        .get()
                    )
                    dataSorties2.append(usersSortiesChart["total_hours"])
                else:
                    dataSorties2.append(0)
                    None

                pass
            
            # Total par année
            totalHours = (
                Salarys.objects.using("auth_db")
                .filter(date__contains=year)
                .aggregate(Sum("hours", distinct=False))
            )
            
            totalBrut = (
                Salarys.objects.using("auth_db")
                .filter(date__contains=year)
                .aggregate(Sum("brut", distinct=False))
            )
            
            totalNet = (
                Salarys.objects.using("auth_db")
                .filter(date__contains=year)
                .aggregate(Sum("net", distinct=False))
            )

            context = {
                "title": "Salaires - Applications manager",
                "page": "Salaires",
                "salarysList": salarysList,
                "dataEntrees": dataEntrees,
                "dataSorties": dataSorties,
                "dataEntrees2": dataEntrees2,
                "dataSorties2": dataSorties2,
                "totalHours": totalHours["hours__sum"],
                "totalBrut": totalBrut["brut__sum"],
                "totalNet": totalNet["net__sum"],
                "year": year,
            }
            return render(request, "pages/salarys.html", context)
        else:
            return redirect("/dashboard")
    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)


def addDocSalarys(request):
    if request.user.is_staff:
        # Salaires
        salarysList = Salarys.objects.using("auth_db").order_by("-id").all()

        month = [
            "janvier",
            "février",
            "mars",
            "avril",
            "mai",
            "juin",
            "juillet",
            "août",
            "septembre",
            "octobre",
            "noveambre",
            "décembre",
        ]
        dataEntrees = []
        dataSorties = []

        if request.GET.get("year"):
            year = request.GET.get("year")
        else:
            today = timezone.now()
            year = today.strftime("%Y")

        for value in month:
            if Salarys.objects.filter(date=value + " " + year).exists():
                usersEntreesChart = (
                    Salarys.objects.using("auth_db")
                    .values("brut")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("brut"))
                    .order_by("date")
                    .get()
                )
                dataEntrees.append(usersEntreesChart["brut"])
            else:
                dataEntrees.append(0)
                None

            if Salarys.objects.filter(date=value + " " + year).exists():
                usersSortiesChart = (
                    Salarys.objects.using("auth_db")
                    .values("net")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("net"))
                    .order_by("date")
                    .get()
                )
                dataSorties.append(usersSortiesChart["net"])
            else:
                dataSorties.append(0)
                None

            pass

        dataEntrees2 = []
        dataSorties2 = []

        if request.GET.get("year"):
            year = request.GET.get("year")
        else:
            today = timezone.now()
            year = today.strftime("%Y")

        for value in month:
            if Salarys.objects.filter(date=value + " " + year).exists():
                usersEntreesChart = (
                    Salarys.objects.using("auth_db")
                    .values("hours")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("hours"))
                    .order_by("date")
                    .get()
                )
                dataEntrees2.append(usersEntreesChart["hours"])
            else:
                dataEntrees2.append(0)
                None

            if Salarys.objects.filter(date=value + " " + year).exists():
                usersSortiesChart = (
                    Salarys.objects.using("auth_db")
                    .values("total_hours")
                    .filter(user_id=request.user.id, date=value + " " + year)
                    .annotate(entree=Avg("total_hours"))
                    .order_by("date")
                    .get()
                )
                dataSorties2.append(usersSortiesChart["total_hours"])
            else:
                dataSorties2.append(0)
                None

            pass
        
        # Total par année
        totalHours = (
            Salarys.objects.using("auth_db")
            .filter(date__contains=year)
            .aggregate(Sum("hours", distinct=False))
        )
        
        totalBrut = (
            Salarys.objects.using("auth_db")
            .filter(date__contains=year)
            .aggregate(Sum("brut", distinct=False))
        )
        
        totalNet = (
            Salarys.objects.using("auth_db")
            .filter(date__contains=year)
            .aggregate(Sum("net", distinct=False))
        )

        if request.method == "POST":
            doc_form = CreateDocSalarysForm(request.POST, request.FILES)
            if doc_form.is_valid():
                myfile = request.FILES["file"]
                fs = FileSystemStorage()
                fs.save("static/salarys/" + myfile.name, myfile)
                doc_form.save()
                msg = "Votre document a bien été ajoutée !"
                context = {
                    "title": "Salaires - Applications manager",
                    "page": "Salaires",
                    "salarysList": salarysList,
                    "msg": msg,
                    "msg_status": "success",
                    "dataEntrees": dataEntrees,
                    "dataSorties": dataSorties,
                    "dataEntrees2": dataEntrees2,
                    "dataSorties2": dataSorties2,
                    "totalHours": totalHours["hours__sum"],
                    "totalBrut": totalBrut["brut__sum"],
                    "totalNet": totalNet["net__sum"],
                    "year": year,
                }
                return render(request, "pages/salarys.html", context)
            else:
                msg = "Une erreur est survenu !"
                context = {
                    "title": "Salaires - Applications manager",
                    "page": "Salaires",
                    "salarysList": salarysList,
                    "msg": msg,
                    "msg_status": "danger",
                    "dataEntrees": dataEntrees,
                    "dataSorties": dataSorties,
                    "dataEntrees2": dataEntrees2,
                    "dataSorties2": dataSorties2,
                    "totalHours": totalHours["hours__sum"],
                    "totalBrut": totalBrut["brut__sum"],
                    "totalNet": totalNet["net__sum"],
                    "year": year,
                }
                return render(request, "pages/salarys.html", context)

    else:
        context = {"title": "Connexion - Applications manager"}
        return render(request, "pages/sign-in.html", context)
