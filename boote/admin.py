from django.contrib import admin
from boote.models import Boat, BoatIssue, BoatType, Booking


@admin.register(Boat)
class BoatAdmin(admin.ModelAdmin):
    list_display = ["name", "owner"]


@admin.register(BoatIssue)
class BoatIssueAdmin(admin.ModelAdmin):
    date_hierarchy = "reported_date"
    list_display = ["boat", "reported_date", "fixed_by"]
    list_filter = ["boat__name", ]


admin.site.register(BoatType)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    list_display = ["boat", "date", "type", "user"]
    list_filter = ["boat__name", "type"]
