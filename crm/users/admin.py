from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
# Register your models here.
from .models import User

# admin.site.register(User, UserAdmin)

# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # форма редактирования существующего пользователя
    fieldsets = UserAdmin.fieldsets + (
        ("Оборудование", {"fields": ("pcm_microscope", "plm_microscope", "plm_scales")}),
    )
    # форма создания нового пользователя (у неё свой набор полей)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Оборудование", {"fields": ("pcm_microscope", "plm_microscope", "plm_scales")}),
    )
    # необязательно: показать колонки в списке пользователей
    list_display = UserAdmin.list_display + ("pcm_microscope", "plm_microscope", "plm_scales")