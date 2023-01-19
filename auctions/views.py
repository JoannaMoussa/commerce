from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from .models import User, Listing, Bid, Comments, CATEGORIES
from django import forms

# Creating a django form that allows the user to create a new listing.
class NewListingForm(forms.Form):
    title = forms.CharField(label="Listing Title", required=True, widget=forms.TextInput(attrs={'class': 'form-control col-2 mb-3'}))
    description = forms.CharField(label="Description", required=True, widget=forms.Textarea(attrs={'class': 'form-control col-4 mb-3', 'rows': '5'}))
    initial_bid = forms.FloatField(label="Starting bid", required=True, widget=forms.NumberInput(attrs={'class': 'form-control col-2 mb-3'}))
    image_url = forms.URLField(label="Image URL", widget=forms.URLInput(attrs={'class': 'form-control col-2 mb-3'}))
    category = forms.ChoiceField(label="Category", choices=CATEGORIES, widget=forms.Select(attrs={'class': 'form-control col-2 mb-3'}))


def index(request):
    return render(request, "auctions/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request):
    if request.method == "POST":
        current_user = request.user
        new_listing = Listing()
        new_listing.creator_id = current_user
        new_listing.title = request.POST['title']
        new_listing.description = request.POST['description']
        new_listing.initial_bid = request.POST['initial_bid']
        new_listing.image_url = request.POST['image_url']
        new_listing.category = request.POST['category']
        new_listing.save()
        return render(request, "auctions/index.html", {
            "message": "Your listing was created successfully!"
        })
    else: # GET
        return render(request, "auctions/create_listing.html", {
            "form": NewListingForm()
        })
