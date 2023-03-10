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
DEFAULT_IMG_URL ="https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/1665px-No-Image-Placeholder.svg.png"

# django form to create a new listing.
class NewListingForm(forms.Form):
    title = forms.CharField(label="Listing Title", max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control col-2 mb-3'}))
    description = forms.CharField(label="Description", max_length=200, required=True, widget=forms.Textarea(attrs={'class': 'form-control col-4 mb-3', 'rows': '5'}))
    initial_bid = forms.FloatField(label="Starting bid", required=True, widget=forms.NumberInput(attrs={'class': 'form-control col-2 mb-3'}))
    image_url = forms.URLField(label="Image URL", required=False, widget=forms.URLInput(attrs={'class': 'form-control col-2 mb-3'}))
    category = forms.ChoiceField(label="Category", required=False, choices=CATEGORIES, widget=forms.Select(attrs={'class': 'form-control col-2 mb-3'}))


# django form to add a bid for a listing.
class PlaceBidForm(forms.Form):
    bid = forms.FloatField(label="", required=True, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Bid'}))


# django form to add a comment for a listing.
class AddCommentForm(forms.Form):
    comment = forms.CharField(label="", max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add comment'}))


def index(request):
    '''
    This function filters the active listings and the closed listings.
    And in order to show each listing in a card format on the index page,
    this function selects, for each listing, a maximun of 100 character 
    for the description, and specifies what price to show (initial bid or max bid)
    '''
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
    '''This function saves the listing details (coming 
    from a post request) in the database.
    '''
    if request.method == "POST":
        current_user = request.user
        new_listing = Listing()
        new_listing.creator_id = current_user
        new_listing.title = request.POST['title']
        new_listing.description = request.POST['description']
        new_listing.initial_bid = request.POST['initial_bid']
        # if the user did not give an image url, i'll put a default one
        if not request.POST['image_url']:
            new_listing.image_url = DEFAULT_IMG_URL
        else:
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

    listing_comments = current_listing.comments.all()

    # if the auction of the current_listing is closed
    if current_listing.is_closed == True:
        return render(request, "auctions/closed_listing_page.html", {
            "current_listing": current_listing,
            "no_bids": no_bids,
            "highest_bid": highest_bid,
            "number_of_biddings" : number_of_biddings,
            "highest_bidder": highest_bidder,
            "user_is_creator": user_is_creator,
            "add_to_watchlist": add_to_watchlist,
            "listing_comments": listing_comments
        })

    return render(request, "auctions/listing_page.html", {
        "current_listing": current_listing,
        "add_bid_form": PlaceBidForm(),
        "add_comment_form": AddCommentForm(),
        "user_is_creator": user_is_creator,
        "add_to_watchlist": add_to_watchlist,
        "no_bids": no_bids,
        "highest_bid": highest_bid,
        "number_of_biddings" : number_of_biddings,
        "highest_bidder": highest_bidder,
        "listing_comments": listing_comments
    })


@login_required(login_url='/login')
def add_to_watchlist(request):
    '''This function adds a listing to a user's watchlist.'''
    if request.method == "POST":
        current_user = request.user
        listing_id = request.POST["listing_id"]
        current_listing = Listing.objects.get(id=listing_id)
        current_user.watchlist.add(current_listing)
        messages.success(request, 'The listing was added to your watchlist.')
        return HttpResponseRedirect(reverse("auctions:listing_page", kwargs={'listing_id': listing_id}))
    else: # GET
        return HttpResponseRedirect(reverse("auctions:index"))


@login_required(login_url='/login')
def remove_from_watchlist(request):
    '''This function removes a listing from a user's watchlist.'''
    if request.method == "POST":
        current_user = request.user
        listing_id = request.POST["listing_id"]
        current_listing = Listing.objects.get(id=listing_id)
        current_user.watchlist.remove(current_listing)
        messages.warning(request, 'The listing was removed from your watchlist.')
        return HttpResponseRedirect(reverse("auctions:listing_page", kwargs={'listing_id': listing_id}))
    else: # GET
        return HttpResponseRedirect(reverse("auctions:index"))


@login_required(login_url='/login')
def add_bid(request):
    '''This function checks if the bid value is valid (equal or greater 
    than the initial bid or greater than the previous bids) 
    and saves it to the database.'''
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
    '''This function gets all the bids made 
    on a given listing.
    '''
    current_listing = Listing.objects.get(id=listing_id)
    biddings = current_listing.biddings.all()
    return render(request, "auctions/bids_details.html", {
        "current_listing": current_listing,
        "biddings": biddings
    })


@login_required(login_url='/login')
def close_auction(request, listing_id):
    '''This function sets the attribute "is_closed" 
    to True for a specific listing.
    '''
    current_listing = Listing.objects.get(id=listing_id)
    current_listing.is_closed = True
    current_listing.save()
    return HttpResponseRedirect(reverse("auctions:index"))


@login_required(login_url='/login')
def add_comment(request, listing_id):
    '''This function adds a comment from a given user id
    to a specific listing.
    '''
    if request.method == "POST":
        current_user = request.user
        new_comment = Comments()
        new_comment.user_id = current_user
        new_comment.listing_id = Listing.objects.get(id=listing_id)
        new_comment.comment = request.POST["comment"]
        new_comment.save()
        messages.success(request, 'Your comment was added successfully!')
        return HttpResponseRedirect(reverse("auctions:listing_page", kwargs={'listing_id': listing_id}))
    else: # GET
        return HttpResponseRedirect(reverse("auctions:index"))


@login_required(login_url='/login')
def watchlist(request):
    '''This function gets all the watchlisted listings of a given user.
    And it handles long descriptions and which price to show 
    (initial bid of highest bid).
     '''
    current_user = request.user
    watchlist_listings = current_user.watchlist.all()
    for watchlist_listing in watchlist_listings:
        # Handling long descriptions
        if len(watchlist_listing.description) > MAX_DESCRIPTION_LEN:
            watchlist_listing.description = watchlist_listing.description[:MAX_DESCRIPTION_LEN-3] + "..."
        # Decide what bid value to show for listings(the initial bid or the highest bid)
        if watchlist_listing.biddings.exists():
            watchlist_listing.no_bids = False
            watchlist_listing.max_bid = watchlist_listing.biddings.all().aggregate(Max("bid_value"))["bid_value__max"]
        else:
            watchlist_listing.no_bids = True
    return render(request, "auctions/watchlist.html", {
        "watchlist_listings": watchlist_listings
    })


def categories(request):
    '''This function saves all the listing categories 
    in a list called categories.
    '''
    categories = []
    # I removed the first element of the list CATEGORIES bcz it's the option "Choose a category"
    for category in CATEGORIES[1:]: 
        categories.append(category[1])
    return render(request, "auctions/categories.html", {
        "categories": categories
    })


def listings_by_category(request, category_name):
    '''This function selects all the listings that belong 
    to the category: category_name, and saves them 
    in a variable called filtered_listings.
    '''
    filtered_listings = Listing.objects.filter(category=category_name, is_closed=False)
    for filtered_listing in filtered_listings:
        # Handling long descriptions
        if len(filtered_listing.description) > MAX_DESCRIPTION_LEN:
            filtered_listing.description = filtered_listing.description[:MAX_DESCRIPTION_LEN-3] + "..."
        # Decide what bid value to show for listings(the initial bid or the highest bid)
        if filtered_listing.biddings.exists():
            filtered_listing.no_bids = False
            filtered_listing.max_bid = filtered_listing.biddings.all().aggregate(Max("bid_value"))["bid_value__max"]
        else:
            filtered_listing.no_bids = True
    return render(request, "auctions/active_listings_by_category.html", {
        "category_name": category_name,
        "filtered_listings": filtered_listings
    })