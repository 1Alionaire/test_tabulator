from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import  redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
from django.db.models import Max
from finance.models import Company
from finance.company_price_table_logic import CompanyPriceTableManager
import logging
from django.core.exceptions import ValidationError
from django.db import IntegrityError

logger = logging.getLogger(__name__)

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
    try:
        payload_json = json.loads(request.body)
        table_manager = CompanyPriceTableManager(payload_json)
        error = table_manager.validate_whole_object()

        # validating whole object
        if error is not None:
            return JsonResponse({'status' : '!ok' , **error}, status=400)

        # updating 
        return JsonResponse(table_manager.table_update_processing())
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': '; '.join(e.messages)}, status=400)
    except IntegrityError as e:
        return JsonResponse({'error': f'database constraint failed: {e}'}, status=400)
    except Exception:
        logger.exception('main table update failed')
        return JsonResponse({'error': 'internal server error'}, status=500)