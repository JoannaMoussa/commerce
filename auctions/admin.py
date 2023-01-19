from django.contrib import admin
from .models import User, Listing, Bid, Comments

class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email")
    
class ListingAdmin(admin.ModelAdmin):
    list_display = ("id", "creator_id", "title", "initial_bid", "image_url", "category", "is_closed")

class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "listing_id", "bid_value")

class CommentsAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "listing_id", "comment")


# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Comments, CommentsAdmin)