from django import forms
from .models import PlmProject
import re
from users.models import User

class PlmProjectDateCollect(forms.ModelForm):
    prefix = "date_collect"
    date_collect = forms.DateField(label='Date Collect', required=True,
                                   widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = PlmProject
        fields = ['date_collect']


class UpdatePlmProject(forms.ModelForm):
    date_analyze = forms.DateField(label='Date Analyzed', required=True,
                                   widget=forms.DateInput(attrs={'type': 'date'}))
    date_report = forms.DateField(label='Date Report', required=True,
                                  widget=forms.DateInput(attrs={'type': 'date'}))
    reviewed_by = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True),
                                    empty_label="Reviewer", required=False)

    date_review = forms.DateField(label='Date Review', required=True,
                                      widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = PlmProject
        fields = ['date_analyze', 'date_report', 'date_review', 'reviewed_by']
        
class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label="Upload Excel file")