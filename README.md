## CS50's Web Programming with Python and JavaScript

# Project 2 - eBay-like e-commerce auction site

This project consists of an eBay-like e-commerce auction site that allows users to post auction listings, place bids on listings, comment on those listings, and add listings to a “watchlist.”

* The website contains the following pages
1. **Register page:** New users can register by giving their username, email and password.

1. **Login page:** Registered users can log in by giving their username and password.

1. **Create listing page:** Signed in users can create a new listing. They specify a title, a description and the starting bid of the listing. They can optionally provide a category and a URL for an image of the listing.

1. **Index Page:** This page shows 2 sections: 
    * The **currently active** listings: For each active listing, the page displays the title, the description, the current price and the photo.
    * The **closed** listings: For each closed listing, the page displays the title, the description, the photo and the price at which the listing was sold / or the phrase "*Did not get sold*" if the auction of the listing was closed without any bids on it.

1. **Listing page:** Clicking on an **active listing** from the index page takes users to a page specific to that listing. This page displays the listing details: description, category, creator name, current price, in addition to the number of bids made on the listing, and the user's name who has the highest bid. But if there are no bids on the listing yet, the page says so. Finally, the page displays all the comments made on that listing.
In addition to that, **signed in users** can do multiple actions:
    * Add the listing to their “Watchlist.” If the listing is already on the watchlist, the user is able to remove it.
    * Bid on the item. The bid must be at least as large as the starting bid, and must be greater than any other bids that have been placed (if any). If the bid doesn’t meet those criteria, the user is presented with an error.
    * Close the auction from this page **if the user is the one who created the listing**, which makes the highest bidder the winner of the auction and makes the listing no longer active.
    * Add comments to the listing page. 

   Clicking on a **closed listing** from the index page also takes users to a page specific to that listing. The page states that the auction on that listing is closed. This page diplays the title, description, category, creator name, number of bids made, the price on which that listing was sold, and the winner name. If the signed in user is the one who won the auction on that listing, the page says so. If no bids were made on that listing, the page says so. Comments made on that listing are shown as well.

1. **Bids details:** From the listing page, the user can click on the number of bids made for the listing, and the user will be redirected to a page that lists, in a table format, the biders' names and their bids.

1. **Watchlist:** Users who are signed in are able to visit a watchlist page, which displays all the listings that a user has added to their watchlist. Clicking on any of those listings takes the user to that listing’s page.

1. **Categories:** Users are able to visit a page that displays a list of all listing categories. Clicking on the name of any category takes the user to a page that displays all of the **active** listings in that category.

* Via the **Django admin interface**, a site administrator is able to view, add, edit, and delete any listings, comments, and bids made on the site.