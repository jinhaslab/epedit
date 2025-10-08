from django.urls import path
from . import views

urlpatterns = [
    # 기록 관리 URL
    path('', views.RecordListView.as_view(), name='record_list'),
    path('<int:pk>/', views.RecordDetailView.as_view(), name='record_detail'),
    path('<int:pk>/edit/', views.RecordUpdateView.as_view(), name='record_edit'),
    
    # API URL
    path('api/get-disease-code/', views.get_disease_code_by_name, name='get_disease_code_by_name'),
    path('api/get-job-code/', views.get_job_code_by_occupation_name, name='get_job_code_by_occupation_name'),
    
    path('api/autocomplete/', views.get_unique_field_values, name='autocomplete_suggestions'),
    
    # 기타 URL (사전 및 외부 연동)
    path('proxy/rag_search/', views.proxy_rag_search, name='proxy_rag_search'),
    path('proxy/job_rag_search/', views.proxy_job_rag_search, name='proxy_job_rag_search'),
    path('ai-search-popup/', views.ai_search_popup, name='ai_search_popup'),
    path('exposure-dictionary/', views.ExposureDictionaryListView.as_view(), name='exposure_dictionary_list'),
    path('disease-dictionary/', views.DiseaseDictionaryListView.as_view(), name='disease_dictionary_list'),

    # 레코드 복원 API
    path('api/reset-record/<int:pk>/', views.reset_record, name='reset_record'),

    # 🤖 자동 적용 API
    path('<int:pk>/auto-apply-disease/', views.auto_apply_disease, name='auto_apply_disease'),
    path('<int:pk>/auto-apply-job/', views.auto_apply_job, name='auto_apply_job'),

    # 담당자 관리 URL
    path('assignees/', views.assignee_list, name='assignee_list'),
    path('assignees/create/', views.assignee_create, name='assignee_create'),
    path('assignees/<int:pk>/update/', views.assignee_update, name='assignee_update'),
    path('assignees/<int:pk>/delete/', views.assignee_delete, name='assignee_delete'),
    path('assignees/<int:pk>/records/', views.AssigneeRecordsView.as_view(), name='assignee_records'),

    # 진행률 대시보드
    path('progress/', views.progress_dashboard, name='progress_dashboard'),
]