from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from .models import User, Listing, Bid, Comments, CATEGORIES
from django import forms
from django.db.models import Max, Count
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
    active_listings = Listing.objects.filter(is_closed=False)
    closed_listings = Listing.objects.filter(is_closed=True)
    for active_listing in active_listings:
        # Handling long descriptions
        if len(active_listing.description) > MAX_DESCRIPTION_LEN:
            active_listing.description = active_listing.description[:MAX_DESCRIPTION_LEN-3] + "..."
        # Decide what bid value to show for listings(the initial bid or the highest bid)
        if active_listing.biddings.exists():
            active_listing.no_bids = False
            active_listing.max_bid = active_listing.biddings.all().aggregate(Max("bid_value"))["bid_value__max"]
        else:
            active_listing.no_bids = True

    for closed_listing in closed_listings:
        # Handling long descriptions
        if len(closed_listing.description) > MAX_DESCRIPTION_LEN:
            closed_listing.description = closed_listing.description[:MAX_DESCRIPTION_LEN-3] + "..."
        # Decide what bid value to show for listings(the initial bid or the highest bid)
        if closed_listing.biddings.exists():
            closed_listing.no_bids = False
            closed_listing.max_bid = closed_listing.biddings.all().aggregate(Max("bid_value"))["bid_value__max"]
        else:
            closed_listing.no_bids = True
    
    return render(request, "auctions/index.html", {
        "active_listings": active_listings,
        "closed_listings": closed_listings
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
        return HttpResponseRedirect(reverse("auctions:index"))
    else: # GET
        return render(request, "auctions/create_listing.html", {
            "form": NewListingForm()
        })


def listing_page(request, listing_id):
    current_listing = Listing.objects.get(id=listing_id)
    highest_bid = None
    number_of_biddings = 0
    highest_bidder = None
    user_is_creator = False
    add_to_watchlist = False

    # checking if first bid or there are existing bid values
    if current_listing.biddings.exists():
        no_bids = False
        # first method to get the highest bid and the number of bids
        #highest_bid = current_listing.biddings.all().aggregate(Max("bid_value"))["bid_value__max"]
        # .aggregate(Count()) returns a disctionary where the key is '{field}__{aggregation}'
        # and the value is the aggregation result.
        #number_of_biddings = current_listing.biddings.all().aggregate(Count("id"))["id__count"]

        # Second method to get the highest bid and the number of bids in one line
        # aggregate_result is something like this: {'id__count': 4, 'bid_value__max': 130.0}
        aggregate_result = current_listing.biddings.all().aggregate(Count("id"), Max("bid_value"))
        highest_bid = aggregate_result["bid_value__max"]
        number_of_biddings = aggregate_result["id__count"]
        highest_bidder = current_listing.biddings.get(bid_value=highest_bid).user_id
    else:
        no_bids = True

    if request.user.is_authenticated:
        current_user = request.user
        if current_user == current_listing.creator_id:
            user_is_creator = True
        else:
            if current_listing not in current_user.watchlist.all():
                add_to_watchlist = True

    # if the auction of the current_listing is closed
    if current_listing.is_closed == True:
        return render(request, "auctions/closed_listing_page.html", {
            "current_listing": current_listing,
            "no_bids": no_bids,
            "highest_bid": highest_bid,
            "number_of_biddings" : number_of_biddings,
            "highest_bidder": highest_bidder
        })

    return render(request, "auctions/listing_page.html", {
        "current_listing": current_listing,
        "form": PlaceBidForm(),
        "user_is_creator": user_is_creator,
        "add_to_watchlist": add_to_watchlist,
        "no_bids": no_bids,
        "highest_bid": highest_bid,
        "number_of_biddings" : number_of_biddings,
        "highest_bidder": highest_bidder,
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
            # if there are other bids
            if current_listing.biddings.exists():
                messages.error(request, 'Your bid must be greater than the highest bid.')
            else: # if it's the first bid
                messages.error(request, 'Your bid must be equal to or greater than the initial bid.')
        return HttpResponseRedirect(reverse("auctions:listing_page", kwargs={'listing_id': listing_id}))
    else: # GET
        return HttpResponseRedirect(reverse("auctions:index"))


def bids_details(request, listing_id):
    current_listing = Listing.objects.get(id=listing_id)
    biddings = current_listing.biddings.all()
    return render(request, "auctions/bids_details.html", {
        "current_listing": current_listing,
        "biddings": biddings
    })


def close_auction(request, listing_id):
    current_listing = Listing.objects.get(id=listing_id)
    current_listing.is_closed = True
    current_listing.save()
    return HttpResponseRedirect(reverse("auctions:index"))

