from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from .models import User, Listing, Bid, Comments, CATEGORIES
from django import forms
from django.db.models import Max
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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
        # Handling long descriptions
        if len(active_listing.description) > MAX_DESCRIPTION_LEN:
            active_listing.description = active_listing.description[:MAX_DESCRIPTION_LEN-3] + "..."
        # Decide what bid value to show for listings
        if active_listing.biddings.exists():
            active_listing.is_initial_bid = False
            active_listing.max_bid = active_listing.biddings.all().aggregate(Max("bid_value"))["bid_value__max"]
        else:
            active_listing.is_initial_bid = True
    
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
            messages.error(request, 'Invalid username and/or password.')
            return render(request, "auctions/login.html")
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
            messages.error(request, 'Passwords must match')
            return render(request, "auctions/register.html")

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            messages.error(request, 'Username already taken')
            return render(request, "auctions/register.html")
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")


@login_required(login_url='/login')
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
        messages.success(request, 'Your listing was created successfully!')
        return render(request, "auctions/index.html")
    else: # GET
        return render(request, "auctions/create_listing.html", {
            "form": NewListingForm()
        })


def listing_page(request, listing_id):
    current_listing = Listing.objects.get(id=listing_id)
    highest_bid = None
    # checking if first bid or there are existing bid values
    if current_listing.biddings.exists():
        is_initial_bid = False
        highest_bid = current_listing.biddings.all().aggregate(Max("bid_value"))["bid_value__max"]
    else:
        is_initial_bid = True
    if request.user.is_authenticated:
        current_user = request.user
        user_is_creator = False
        add_to_watchlist = False
        if current_user == current_listing.creator_id:
            user_is_creator = True
        else:
            if current_listing not in current_user.watchlist.all():
                add_to_watchlist = True
        return render(request, "auctions/listing_page.html", {
            "current_listing": current_listing,
            "form": PlaceBidForm(),
            "user_is_creator": user_is_creator,
            "add_to_watchlist": add_to_watchlist,
            "is_initial_bid": is_initial_bid,
            "highest_bid": highest_bid
        })
    else:
        return render(request, "auctions/listing_page.html", {
            "current_listing": current_listing,
            "is_initial_bid": is_initial_bid,
            "highest_bid": highest_bid
        })


@login_required(login_url='/login')
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


@login_required(login_url='/login')
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


@login_required(login_url='/login')
def add_bid(request):
    if request.method == "POST":
        current_user = request.user
        listing_id = request.POST["listing_id"]
        current_listing = Listing.objects.get(id=listing_id)
        allow_bid = False
        # if it's the first bid
        if not current_listing.biddings.exists():
            # check whether the bid chosen by the user is >= or less than the initial bid value
            if float(request.POST["bid"]) >= current_listing.initial_bid:
                allow_bid = True
        else: # if there are bids for this listing
            # get max of existing bid values
            biddings = current_listing.biddings.all()
            # biddings.aggregate(Max("bid_value")) returns a dictionary where the key is bid_value__max
            # and the value is a float (the max bid)
            highest_bid = biddings.aggregate(Max("bid_value"))["bid_value__max"]
            # check if the bid chosen by the user is greater than the max bid
            if float(request.POST["bid"]) > highest_bid:
                allow_bid = True
        if allow_bid:
            new_bid = Bid()
            new_bid.user_id = current_user
            new_bid.listing_id = current_listing
            new_bid.bid_value = request.POST["bid"]
            new_bid.save()
            messages.success(request, 'Your bid was added successfully!')
        else:
            messages.error(request, 'Your bid must be higher than the existing bids.')
        return HttpResponseRedirect(reverse("auctions:listing_page", kwargs={'listing_id': listing_id}))
    else: # GET
        return HttpResponseRedirect(reverse("auctions:index"))
