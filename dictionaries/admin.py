from django.contrib import admin
from .models import DiseaseDictionaryEntry, JobCodeOccupation, ExposureDictionary

@admin.register(DiseaseDictionaryEntry)
class DiseaseDictionaryAdmin(admin.ModelAdmin):
    list_display = ('disease_name', 'disease_code')
    search_fields = ('disease_name', 'disease_code')

@admin.register(JobCodeOccupation)
class JobCodeOccupationAdmin(admin.ModelAdmin):
    list_display = ('occupation', 'job_code')
    search_fields = ('occupation', 'job_code')
    list_per_page = 30

@admin.register(ExposureDictionary)
class ExposureDictionaryAdmin(admin.ModelAdmin):
    search_fields = ('name',)