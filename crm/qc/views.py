from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse, FileResponse, Http404
from main.models import MainProject
from django.views.generic import UpdateView
from django.shortcuts import  redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from openpyxl import load_workbook
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
import django.utils
from datetime import datetime
from users.models import User
from django.db.models import Max
from finance.models import Company
import logging
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from main.models import MainTypeAnalysis
from utils.utils import form_errors_to_text
from .models import PlmQCReplicateDuplicateItem, PlmTypeQCSample, PlmTypeAnalysisSample
from users.models import User
from plm.models import SampleMethod
from django.db.models.functions import ExtractYear, ExtractMonth
from django.views.generic import TemplateView, ListView

class UserPlmMenuView(LoginRequiredMixin, TemplateView):
    extra_context = {
        'title': 'QC PLM'
        }
    template_name = 'qc/user_plm_menu.html'

class UserPcmMenuView(LoginRequiredMixin, TemplateView):
    extra_context = {
        'title': 'QC PCM'
        }
    template_name = 'qc/user_pcm_menu.html'


class ManagerPlmMenuView(LoginRequiredMixin, TemplateView):
    extra_context = {
        'title': 'QC Manager PLM'
        }
    template_name = 'qc/manager_plm_menu.html'

class ManagerPlmRepDupByAnalyst(LoginRequiredMixin, TemplateView):
    extra_context = {
        'title': 'QC Reps Dups by Analyst'
        }
    template_name = 'qc/manager_plm_dup_rep_by_analyst.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rows = (
            PlmQCReplicateDuplicateItem.objects
            .filter(project__date_analyze__isnull=False)
            .values(
                'analyst_id', 'analyst__username', 'qc_type', 'analysis_type',
                year=ExtractYear('project__date_analyze'),
                month=ExtractMonth('project__date_analyze'),
            )
            .order_by('analyst__username', 'qc_type', 'analysis_type', 'year', 'month')
            .distinct()
        )
        ctx['nav_data'] = [
            {
                'analyst': r['analyst_id'],
                'analyst_label': r['analyst__username'],
                'qc_type': r['qc_type'],
                'qc_type_label': PlmTypeQCSample(r['qc_type']).label,
                'analysis_type': r['analysis_type'],
                'analysis_type_label': PlmTypeAnalysisSample(r['analysis_type']).label,
                'year': r['year'],
                'month': r['month'],
            }
            for r in rows
        ]
        return ctx

class ManagerPlmRepDupAllInfo(ListView):
    model = PlmQCReplicateDuplicateItem
    template_name = 'qc/manager_plm_dup_rep_all_info.html'
    context_object_name = 'items'

    # GET-параметр -> ORM-лукап
    FILTERS = {
        'analyst': 'analyst_id',
        'qc_type': 'qc_type',
        'analysis_type': 'analysis_type',
        'year': 'project__date_analyze__year',
        'month': 'project__date_analyze__month',
    }

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'project', 'original_sample', 'qc_sample', 'analyst', 'reviewer'
        )
        lookups = {
            orm: self.request.GET[param]
            for param, orm in self.FILTERS.items()
            if param in self.request.GET
        }
        return qs.filter(**lookups)


class ManagerPcmMenuView(LoginRequiredMixin, TemplateView):
    extra_context = {
        'title': 'QC Manager PCM'
        }
    template_name = 'qc/manager_pcm_menu.html'

