from django.shortcuts import render

# Create your views here.
def tem_main_menu(request):
    return render(request, template_name="tem/main_page.html")

def original_grid_book(request):
    return render(request, template_name="tem/original_grid_book.html")

def qc_grid_book(request):
    return render(request, template_name="tem/qc_grid_book.html")
