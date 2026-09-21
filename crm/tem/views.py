from django.shortcuts import render
from tem.models import TEMGridRecord, TEMGridQCRecord
from django.http import JsonResponse

# Create your views here.
def tem_main_menu(request):
    return render(request, template_name="tem/main_page.html")

def original_grid_book(request):
    return render(request, template_name="tem/original_grid_book.html")

def qc_grid_book(request):
    return render(request, template_name="tem/qc_grid_book.html")

def api_get_original_grid_book_table(request):
    grid_boxes = TEMGridRecord.objects.all().values('id',
                                                      'position', 
                                                        'year', 
                                                        'grid_box', 
                                                        'grid_id_1', 
                                                        'grid_id_2', 
                                                        'plm_tem_project__project__lab_id', 
                                                        'plm_tem_sample__lab_sample')
    return JsonResponse(list(grid_boxes), safe=False)

def api_get_qc_grid_book_table(request):
    grid_boxes = TEMGridQCRecord.objects.all().values('id',
                                                      'position', 
                                                        'year', 
                                                        'grid_box', 
                                                        'grid_id_1', 
                                                        'grid_id_2', 
                                                        'plm_tem_project__project__lab_id', 
                                                        'plm_tem_sample__lab_sample')
    return JsonResponse(list(grid_boxes), safe=False)