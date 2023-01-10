from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Category(models.Model):
    category = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.category}"


class Listing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(max_length=500, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name="listings", null=True, blank=True)
    photo = models.URLField(blank=True, max_length=1000)
    date = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    winner = models.CharField(default="No Winner", max_length=20)
    

    def __str__(self):
        return f"{self.user}: {self.id}. Title - {self.title}, Price - ${self.price}, Category - {self.category or 'None'}, Date - {self.date}"


class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    bid = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.user} is bidding on {self.listing} for ${self.bid}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    comment = models.TextField(max_length=500)

    def __str__(self):
        return f"{self.user} commented on {self.listing.title} - {self.comment}"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} has placed {self.listing} on watchlist"

 
