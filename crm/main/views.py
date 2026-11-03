from .models import MainProject, MainTypeAnalysis
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from .forms import ProjectCOCUpload
from django.shortcuts import  redirect, get_object_or_404
from django.urls import reverse_lazy
from plm.models import PlmProject
from pcm.models import PcmProject
import logging

logger = logging.getLogger(__name__)

class MainTableView(LoginRequiredMixin, TemplateView):
    extra_context = {
        'title': 'Main'
        }
    template_name = 'main/index.html'

class UploadCOCView(UpdateView):
    model = MainProject
    form_class = ProjectCOCUpload
    template_name = 'main/coc_upload_page.html'
    context = {'title': 'Upload COC'}
    context_object_name = 'work'
    
    def get_object(self):
        return get_object_or_404(MainProject, id=self.kwargs['id'])

    def get_success_url(self):
        return reverse_lazy('main:main')

def route_work(request, id):
    main_project = MainProject.objects.get(pk=id)
    if main_project.project_type == MainTypeAnalysis.PCM:
        pcm_project = get_object_or_404(PcmProject, project=main_project)
        return redirect('pcm:pcm_detail', pcm_project.id)
    if main_project.project_type in [MainTypeAnalysis.Bulk, MainTypeAnalysis.BulkTEM, MainTypeAnalysis.EPT]:
        plm_project = get_object_or_404(PlmProject, project=main_project) 
        return redirect('plm:plm_detail', plm_project.id)