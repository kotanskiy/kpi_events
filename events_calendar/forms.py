from django import forms
from django.forms import ModelForm
from events_calendar.models import Event, Organization


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'name',
            'description',
            'image',
            'start_date',
            'end_date',
            'category',
            'place_of_event',
            'web_site',
            'fb_link',
        ]

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'name',
            'image',
        ]

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
