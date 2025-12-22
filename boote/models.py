from datetime import date, datetime, timedelta
from pathlib import Path
import uuid

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models


class BoatType(models.Model):
    name = models.CharField(max_length=30)
    url = models.CharField(max_length=256)
    length = models.CharField(max_length=15)
    beam = models.CharField(max_length=15)
    draught = models.CharField(max_length=15)

    def __str__(self):
        return self.name


def boat_img_path(instance, filename):
    unique_filename = uuid.uuid4()
    extension = Path(filename).suffix
    # File will be uploaded to MEDIA_ROOT/boats_gallery/<unique filename>.<extension>
    return f"boats_gallery/{unique_filename}.{extension}"


class Boat(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        # Protect club boats from being deleted unintentionally (user interaction
        # required, no way to get a default owner)
    )
    type = models.ForeignKey(
        BoatType,
        on_delete=models.PROTECT,
        # Cannot delete a boat type as long as there are boats of it
    )

    photo = models.ImageField(upload_to=boat_img_path, null=True)
    name = models.CharField(max_length=30)
    active = models.BooleanField(default=True)
    briefing = models.CharField(max_length=2000, null=True, default="")
    remarks = models.CharField(max_length=2000, null=True)
    club_boat = models.BooleanField(default=False)
    booking_remarks = models.CharField(max_length=2000, null=True, default="")
    instructions = models.FileField(
        upload_to="boat_instructions",
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    def getBookings7days(self):
        """Get list that describes bookings for upcoming 7 days.

        0 for free, 1 for partially booked, 2 for fully booked.
        """
        d1 = datetime.now()
        d2 = d1 + timedelta(days=6)
        result = [0, 0, 0, 0, 0, 0, 0]
        for booking in Booking.objects.filter(
            boat=self, date__lte=d2, date__gte=d1, status=1
        ):
            offset = (booking.date - d1.date()).days
            result[offset] = 1
        return result

    def get_detailed_bookings(self, num_days=1):
        """Get detailed bookings for the next num_days.

        The returned list is intended for usage in booking table templates.
        It contains data for each half-hour slot from 8:00 to 22:00.

        Args:
            num_days (int): The number of days to get bookings for.

        Returns:
            list: A three-level nested list:
                    - first level: days
                    - second level: half-hour slots
                    - third level: booking details (user id, display name, booking type)
        """
        start_hour = 8
        end_hour = 22
        # There are two half-hour slots per hour
        num_slots = (end_hour - start_hour) * 2

        # Initialize empty result structure [days][slots][booking data]
        res = [[["", "", ""] for _ in range(num_slots)] for _ in range(num_days)]

        start_date = date.today()
        end_date = start_date + timedelta(days=num_days - 1)

        for booking in Booking.objects.filter(
            boat=self, date__lte=end_date, date__gte=start_date, status=1
        ):
            # Calculate index of the booking day relative to start_date
            day_idx = (booking.date - start_date).days

            uid = booking.user.username
            usertag = booking.user.first_name + " " + booking.user.last_name

            # Convert start and end times into half-hour slot indices
            slot_start_idx = round(
                (booking.time_from.hour - start_hour) * 2
                + (booking.time_from.minute / 30)
            )
            slot_end_idx = round(
                (booking.time_to.hour - start_hour) * 2 + (booking.time_to.minute / 30)
            )

            # Store booking data for corresponding half-hour slots
            for i in range(max(0, slot_start_idx), min(num_slots, slot_end_idx)):
                res[day_idx][i] = [uid, usertag, booking.type]

        return res

    def getNumberOfIssues(self):
        return BoatIssue.objects.filter(boat=self, status=1).count()


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_date = models.DateField(default=datetime.now)
    boat = models.ForeignKey(Boat, on_delete=models.CASCADE)
    status = models.IntegerField(default=1)
    type = models.CharField(
        max_length=3,
        choices=(
            ("PRV", "Freie Nutzung"),
            ("AUS", "Ausbildung"),
            ("REG", "Regatta"),
            ("REP", "Reparatur"),
        ),
        default="PRV",
    )
    date = models.DateField()
    time_from = models.TimeField()
    time_to = models.TimeField()
    notified = models.BooleanField(default=False)


class BoatIssue(models.Model):
    boat = models.ForeignKey(Boat, on_delete=models.CASCADE)
    status = models.IntegerField(default=1)
    reported_by = models.ForeignKey(
        User,
        related_name="user_reporting",
        on_delete=models.PROTECT,
        # Probably not a good idea to delete issue until it is resolved,
        # might want to talk to the reporter of the issue
    )
    reported_date = models.DateField()
    reported_descr = models.CharField(max_length=2000)
    fixed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="user_fixing", null=True
    )
    fixed_date = models.DateField(null=True)
    fixed_descr = models.CharField(max_length=2000, null=True)
    notified = models.BooleanField(default=False)
