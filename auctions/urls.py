from django.urls import path

from . import views

app_name = "auctions"
urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("createListing", views.create_listing, name="create_listing"),
    path("listing/<int:listing_id>", views.listing_page, name="listing_page"),
    path("addToWatchlist", views.add_to_watchlist, name="add_to_watchlist"),
    path("removeFromWatchlist", views.remove_from_watchlist, name="remove_from_watchlist"),
    path("addBid", views.add_bid, name="add_bid"),
    path("listing/<int:listing_id>/bidsDetails", views.bids_details, name="bids_details"),
    path("listing/<int:listing_id>/closeAuction", views.close_auction, name="close_auction"),
    path("listing/<int:listing_id>/addComment", views.add_comment, name="add_comment"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("categories", views.categories, name="categories"),
    path("category/<str:category_name>", views.listings_by_category, name="listings_by_category")
]
