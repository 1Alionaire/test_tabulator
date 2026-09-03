from django import forms
from .models import MainProject
import re

class ProjectCOCUpload(forms.ModelForm):

    class Meta:
        model = MainProject
        fields = ['coc_file']
