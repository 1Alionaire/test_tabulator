from django import forms
from .models import PcmProject

class UpdatePcmProject(forms.ModelForm):
    date_collect = forms.DateField(label='Date Collected', required=True,
                                   widget=forms.DateInput(attrs={'type': 'date'}))
    date_analyze = forms.DateField(label='Date Analyzed', required=True,
                                   widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = PcmProject
        fields = ['date_collect', 'date_analyze', 'work_area', 'technician', 'rotometer',
                  'type_sampling']

        labels = {
            'work_area': 'Work Area',
            'technician': 'Technician',
            'rotometer': 'Rotometer',
            'type_sampling': 'Type of Sampling'
        }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs) # init function from parent class
    #     for name, field in self.fields.items(): # going through dict ? 
    #         existing = field.widget.attrs.get('class', '') 
    #         field.widget.attrs['class'] = f'{existing} form-control'.strip()
