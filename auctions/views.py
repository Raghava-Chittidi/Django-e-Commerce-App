from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms

from .models import User, Category, Listing, Bid, Comment, Watchlist


# Create Listing Form
class CreateListingForm(forms.Form):
    title = forms.CharField(max_length=50, label="Title", widget=forms.TextInput(attrs={'style': 'display: block;' 'width: 800px;'}))
    description = forms.CharField(max_length=200, widget=forms.Textarea(attrs={'style': 'display: block;' 'width: 800px;'}))
    starting_bid = forms.DecimalField(max_digits=8, decimal_places=2, label="Starting Bid:", widget=forms.NumberInput(attrs={'style': 'display: block;' 'width: 800px;'}))
    image_url = forms.URLField(required=False, label="Image Link", widget=forms.URLInput(attrs={'style': 'display: block;' 'width: 800px;'}))
    category = forms.CharField(required=False, max_length=20, label="Category", widget=forms.TextInput(attrs={'style': 'display: block;' 'width: 800px;'}))



# Route "/login"
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)

            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


# Route "/logout"
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))


# Route "/register"
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
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


# Route "/"
@login_required
def index(request):

    # Get the total number of listings in the watchlist
    request.session["watchlistNum"] = len(Watchlist.objects.filter(user=request.user.id))

    # When Close Auction button is clicked
    if request.method == "POST":
        id = request.POST["listing"]
        bidID = int(request.POST["bidID"]) - 1

        # Get winner's username of the auction for that listing
        user = Bid.objects.get(id=bidID).user
        username = User.objects.get(username=user).username

        # Disable the listing and set its winner
        listing = Listing.objects.get(id=id)
        listing.active = False
        listing.winner = username
        listing.save()
        return HttpResponseRedirect(reverse("index"))

    # Only show active listings on index page
    return render(request, "auctions/index.html", {
        "active_listings": Listing.objects.filter(active=True)
    })


# Route "/create"
@login_required
def create(request):

    # When Create Listing button is clicked
    if request.method == "POST":
        form = CreateListingForm(request.POST)

        # Get the new listing details
        if form.is_valid():
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            starting_bid = int(form.cleaned_data["starting_bid"])
            image_url = form.cleaned_data["image_url"]
            category = form.cleaned_data["category"]
            category_id = Category.objects.get(category=category).id
            id = len(Listing.objects.all()) + 1

            # Create new listing
            new = Listing(id, request.user.id, title, starting_bid, description, category_id, image_url)
            new.save()

    # Show the Create Listing Form
    return render(request, "auctions/create.html", {
        "form": CreateListingForm()
    })


# Route "/listing/x"
@login_required
def listing(request, number):

    # Get all the comments
    comments = Comment.objects.all()

    # Get the total number of bids for that current listing
    bids = Bid.objects.all()
    bidNumber = len(Bid.objects.filter(listing=number))

    # Get the current listing the user is looking at
    listing = Listing.objects.get(id=number)

    if request.method == "POST":

        # If Place Bid button is clicked
        if request.POST.get("comment") is None:
            bid = float(request.POST["bid"])
            bid = "{:.2f}".format(bid)

            # Ensure bid placed is > listing price
            if float(bid) <= float(listing.price):
                return render(request,"auctions/error.html")

            # Save the new listing price and bid
            listing.price = bid
            listing.save()
            new = Bid(len(bids) + 1, request.user.id, number, bid)
            new.save()
            return HttpResponseRedirect(reverse("listing", args=(number,)))

        # If Add Comment button is clicked
        else:

            # Save the new comment
            comment = request.POST["comment"]
            new = Comment(len(comments) + 1, request.user.id, number, comment)
            new.save()
            return HttpResponseRedirect(reverse("listing", args=(number,)))

    # Get all the listings that are in the watchlist
    watchlist = Watchlist.objects.filter(user=request.user.id).values_list('listing_id', flat=True)
    listings = Listing.objects.filter(id__in = watchlist, active=True)

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "number": bidNumber,
        "watchlist": listings,
        "comments": comments
    })


@login_required
def watchlist(request):



    # When the Add to Watchlist or Remove From Watchlist button is clicked
    if request.method == "POST":
        id = request.POST["id"]
        watchlistID = len(Watchlist.objects.all()) + 1
        
        # Check if the user has clicked add or remove
        if request.POST["check"] == "add":

            # Add to watchlist
            new = Watchlist(watchlistID, request.user.id, id)
            new.save()
            request.session["watchlistNum"] += 1
        else:

            # Remove from watchlist
            remove = Watchlist.objects.filter(listing=id)
            remove.delete()
            request.session["watchlistNum"] -= 1

        return HttpResponseRedirect(reverse("watchlist"))

    # Get the active listings that are in the watchlist
    watchlist = Watchlist.objects.filter(user=request.user.id).values_list('listing_id', flat=True)
    listings = Listing.objects.filter(id__in = watchlist, active=True)

    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })


# Route "/categories"
@login_required
def categories(request):

    # Show all the existing categories as a list
    return render(request, "auctions/categories.html", {
        "categories": Category.objects.all()
    })


# Route "/categories/xxx"
@login_required
def category_type(request, category):

    # Get all the listings of the category clicked
    category_type = Category.objects.filter(category=category).values_list('id', flat=True)
    listings = Listing.objects.filter(category__in = category_type)

    return render(request, "auctions/category_type.html", {
        "category": category,
        "listings": listings
    })
