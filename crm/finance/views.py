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
from plm.plm_table_logic import PLMSamplesDataEntryManager, PLMSamplesWeightManager, generate_qc_entry_process
import django.utils
from datetime import datetime
from users.models import User
from django.db.models import Max
from tem.models import TEMGridQCRecord, TEMGridRecord
from report_generator.plm.plm_report_generator import BulkSampleReportGenerator
from invoice_generator.invoice_generator_start import InvoiceGenerator, DataForInvoiceGenerator
from finance.models import Company


def finance_main_menu(request):
    return render(request, template_name="finance/main_page.html")

class CompanyTableView(LoginRequiredMixin, TemplateView):
    extra_context = {
        'title': 'Company Main'
        }
    template_name = 'finance/main_page_company.html'

# =============== getting all PLM projects ===============
@require_GET
def api_get_company_price_table(request):
    companies = Company.objects.all().order_by('slug').values(
                                                     'id',
                                                     'name',
                                                     'slug',
                                                     'representative',
                                                     'pcm_price',
                                                     'plm_price',
                                                     'nob_price', 
                                                     'prep_nob_price', 
                                                     'tem_price', 
                                                     'air_tem_price', 
                                                     'lead_wipe_price',
                                                     'lead_air_price', 
                                                     'vermi_price', 
                                                     'mold_price')
    return JsonResponse(list(companies), safe=False)

@csrf_exempt
@require_POST
def api_update_company_price_table(request):
    payload_json = json.loads(request.body)
    print(payload_json)
    return JsonResponse({'status':'ok'})