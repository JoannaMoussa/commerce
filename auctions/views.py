from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from .models import User, Listing, Bid, Comments, CATEGORIES
from django import forms

MAX_DESCRIPTION_LEN = 100

# django form that allows the user to create a new listing.
class NewListingForm(forms.Form):
    title = forms.CharField(label="Listing Title", required=True, widget=forms.TextInput(attrs={'class': 'form-control col-2 mb-3'}))
    description = forms.CharField(label="Description", required=True, widget=forms.Textarea(attrs={'class': 'form-control col-4 mb-3', 'rows': '5'}))
    initial_bid = forms.FloatField(label="Starting bid", required=True, widget=forms.NumberInput(attrs={'class': 'form-control col-2 mb-3'}))
    image_url = forms.URLField(label="Image URL", widget=forms.URLInput(attrs={'class': 'form-control col-2 mb-3'}))
    category = forms.ChoiceField(label="Category", choices=CATEGORIES, widget=forms.Select(attrs={'class': 'form-control col-2 mb-3'}))


# django form that allows the user to add a bid for a listing.
class PlaceBidForm(forms.Form):
    bid = forms.FloatField(label="Bid", required=True, widget=forms.NumberInput(attrs={'class': 'form-control col-2 mb-3', 'placeholder': 'Bid'}))


def index(request):
    active_listings = Listing.objects.all()
    for active_listing in active_listings:
        if len(active_listing.description) > MAX_DESCRIPTION_LEN:
            active_listing.description = active_listing.description[:MAX_DESCRIPTION_LEN-3] + "..."
    return render(request, "auctions/index.html", {
        "active_listings": active_listings
    })


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


def listing_page(request, listing_id):
    current_listing = Listing.objects.get(id=listing_id)
    if request.user.is_authenticated:
        current_user = request.user
        if current_listing in current_user.watchlist.all():
            watchlist_button = False
        else:
            watchlist_button = True
        return render(request, "auctions/listing_page.html", {
            "current_listing": current_listing,
            "form": PlaceBidForm(),
            "watchlist_button": watchlist_button
        })
    else:
        return render(request, "auctions/listing_page.html", {
            "current_listing": current_listing,
            "form": PlaceBidForm()
        })


# TODO @login_required
def add_to_watchlist(request):
    if request.method == "POST":
        current_user = request.user
        listing_id = request.POST["listing_id"]
        current_listing = Listing.objects.get(id=listing_id)
        current_user.watchlist.add(current_listing)
        # TODO show a success message to the user that the listing item was added to the watchlist.
        return HttpResponseRedirect(reverse("auctions:listing_page", kwargs={'listing_id': listing_id}))
    else: # GET
        return HttpResponseRedirect(reverse("auctions:index"))


def remove_from_watchlist(request):
    if request.method == "POST":
        current_user = request.user
        listing_id = request.POST["listing_id"]
        current_listing = Listing.objects.get(id=listing_id)
        current_user.watchlist.remove(current_listing)
        # TODO show a success message to the user that the listing item was added to the watchlist.
        return HttpResponseRedirect(reverse("auctions:listing_page", kwargs={'listing_id': listing_id}))
    else: # GET
        return HttpResponseRedirect(reverse("auctions:index"))


def add_bid(request):
    pass