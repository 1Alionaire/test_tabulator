from django import forms
from .models import PlmProject
import re
from users.models import User

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label="Upload Excel file")