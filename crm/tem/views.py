from django.shortcuts import render

# Create your views here.
def tem_main_menu(request):
    return render(request, template_name="tem/main_page.html")