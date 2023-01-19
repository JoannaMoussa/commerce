from django.contrib.auth.models import AbstractUser
from django.db import models

CATEGORIES = [("Fashion", "Fashion"),
              ("Toys", "Toys"),
              ("Electronics", "Electronics"),
              ("Home", "Home")]


class User(AbstractUser):
    pass


class Listing(models.Model):
    creator_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listing_items")
    title = models.CharField(max_length=20)
    description = models.TextField(max_length=200)
    initial_bid = models.FloatField()
    image_url = models.URLField()
    category = models.CharField(choices=CATEGORIES, max_length=20)
    is_closed = models.BooleanField(default=False)
    #users who watchlisted a listing item
    watchlist_users = models.ManyToManyField(User, blank=True, related_name="watchlist")

    def __str__(self):
        return f"{self.title}"


class Bid(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="biddings")
    listing_id = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="biddings")
    bid_value = models.FloatField()

    def __str__(self):
        return f"{self.bid_value} is the bid value of {self.user_id} for {self.listing_id}"


class Comments(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    listing_id = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField(max_length=100)

    def __str__(self):
        return f"{self.user_id}'s comment on {self.listing_id}: {self.comment}"
