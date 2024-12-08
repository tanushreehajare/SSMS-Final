from django import forms
from .models import StationaryBill

class StationaryBillForm(forms.ModelForm):
    image = forms.ImageField()
    class Meta:
        model = StationaryBill
        fields = ['caption']

