from django.contrib import admin
# 📝 DiseaseRecord 모델의 occupation이 job으로 바뀌었으므로, JobCodeOccupation 모델을 import합니다.
from .models import DiseaseRecord, Case, PopulationData, WorkProcessData, Profile 
from dictionaries.models import JobCodeOccupation

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    search_fields = ('fid',)
    
@admin.register(PopulationData)
class PopulationDataAdmin(admin.ModelAdmin):
    list_display = ('case', 'variable', 'value')
    search_fields = ('case__fid', 'variable')
    list_filter = ('variable',)

@admin.register(WorkProcessData)
class WorkProcessDataAdmin(admin.ModelAdmin):
    list_display = ('case', 'variable', 'value')
    search_fields = ('case__fid', 'variable')
    list_filter = ('variable',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_seen')
    search_fields = ('user__username',)


@admin.register(DiseaseRecord)
class DiseaseRecordAdmin(admin.ModelAdmin):
    # 📝 'occupation' -> 'job'으로 변경
    list_display = ('case', 'disease', 'job', 'last_modified_at', 'last_modified_by')
    # 📝 'occupation__occupation' -> 'job__occupation'으로 변경
    search_fields = ('case__fid', 'disease__disease_name', 'job__occupation')
    
    # 📝 'occupation' -> 'job'으로 변경
    autocomplete_fields = ('disease', 'job', 'case')