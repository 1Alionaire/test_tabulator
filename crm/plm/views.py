from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from main.models import MainProject
from django.views.generic import UpdateView
from .models import PlmProject
from .forms import UpdatePlmProject
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.


class PLMTableView(TemplateView):
    extra_context = {
        'title': 'PLM Main'
        }
    template_name = 'plm/plm_main.html'

def api_get_plm_projects_table(request):
    plm_projects = MainProject.active_objects.filter(sample_type_id__in=[2,3,4]).order_by('lab_id_sort').values(
                                                     'id',
                                                     'lab_id',
                                                     'lab_id_sort',
                                                     'date_registered',
                                                     'time_registered',
                                                     'company_id',
                                                     'project_name',
                                                     'project_address',
                                                     'sample_type_id',
                                                     'number_samples',
                                                     'turn_around_time_id',
                                                     'nob_number_samples', 
                                                     'technician', 
                                                     'status_id', 
                                                     'comment')
    return JsonResponse(list(plm_projects), safe=False)

class UpdateProjectView(UpdateView):
    model = PlmProject
    form_class = UpdatePlmProject
    template_name = 'plm/plm_page.html'
    context = {'title': 'test'}
    context_object_name = 'work'
    
    def get_object(self):
        return get_object_or_404(PlmProject, id=self.kwargs['id'])

def render_plm_detail(request, id):
    return render(request, template_name='plm/plm_page.html', context={'title':'ID', 
                                                'ID': id})