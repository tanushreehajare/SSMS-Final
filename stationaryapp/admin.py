from django.contrib import admin
from stationaryapp.models import facultyrequest, stationary, assignment, faculty, CustomUser, StationaryBill, item, Profile

# Register your models here.
admin.site.register(stationary)
admin.site.register(assignment)
admin.site.register(facultyrequest)
admin.site.register(faculty)
admin.site.register(CustomUser)
admin.site.register(StationaryBill)
admin.site.register(item)
admin.site.register(Profile)