from django import forms
from .models import PlmProject
import re

class UpdatePlmProject(forms.ModelForm):
    date_collect = forms.DateField(label='Date Collected', required=True,
                                   widget=forms.DateInput(attrs={'type': 'date'}))
    date_receive = forms.DateField(label='Date Received', required=True,
                                   widget=forms.DateInput(attrs={'type': 'date'}))
    date_analyze = forms.DateField(label='Date Analyzed', required=True,
                                   widget=forms.DateInput(attrs={'type': 'date'}))
    date_report = forms.DateField(label='Date Report', required=True,
                                  widget=forms.DateInput(attrs={'type': 'date'}))
    date_review = forms.DateField(label='Date Review', required=True,
                                  widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = PlmProject
        fields = ['date_collect', 'date_receive', 'date_analyze', 'date_report',
                  'date_review']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} form-control'.strip()


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label="Upload Excel file")