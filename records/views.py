from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Substr, Cast
from django.db.models import IntegerField
from django.views.decorators.csrf import csrf_exempt
import json
import requests

# 👇 필요한 모델들을 import 합니다.
from dictionaries.models import DiseaseDictionaryEntry, JobCodeOccupation, ExposureDictionary
from .models import DiseaseRecord, Case
from .forms import DiseaseRecordForm
from .utils.disease_field_handler import (
    get_additional_disease_context,
    save_additional_disease_fields
)

# -----------------------------------------------------------
# API 엔드포인트 뷰
# -----------------------------------------------------------
def get_unique_field_values(request):
    """자동 완성을 위한 제안 목록을 ID와 이름으로 반환하는 API 뷰"""
    field_name = request.GET.get('field_name')
    query = request.GET.get('q', '')
    suggestions = []

    if field_name == 'disease_name' or field_name == 'additional_disease_name':
        results = DiseaseDictionaryEntry.objects.filter(disease_name__icontains=query)[:20]
        suggestions = [{'id': r.id, 'name': r.disease_name} for r in results]

    # 📝 field_name == 'occupation' -> 'job'으로 변경
    elif field_name == 'job':
        results = JobCodeOccupation.objects.filter(occupation__icontains=query)[:20]
        suggestions = [{'id': r.id, 'name': r.occupation} for r in results]

    elif field_name == 'exposure':
        results = ExposureDictionary.objects.filter(name__icontains=query)[:20]
        suggestions = [{'id': r.id, 'name': r.name} for r in results]

    return JsonResponse({'suggestions': suggestions})

# records/views.py

# 함수 이름을 바꾸고, 이름으로 검색하도록 로직 변경
def get_disease_code_by_name(request):
    """질병 이름을 기반으로 질병 코드를 반환하는 API 뷰"""
    disease_name = request.GET.get('disease_name')
    data = {'disease_code': ''}
    if disease_name:
        entry = DiseaseDictionaryEntry.objects.filter(disease_name=disease_name).first()
        if entry:
            data['disease_code'] = entry.disease_code
    return JsonResponse(data)

# 함수 이름을 바꾸고, 이름으로 검색하도록 로직 변경
def get_job_code_by_occupation_name(request):
    """직종 이름을 기반으로 직종 코드를 반환하는 API 뷰"""
    occupation_name = request.GET.get('occupation_name')
    data = {'job_code': ''}
    if occupation_name:
        entry = JobCodeOccupation.objects.filter(occupation=occupation_name).first()
        if entry:
            data['job_code'] = entry.job_code
    return JsonResponse(data)

# -----------------------------------------------------------
# RecordListView (목록 페이지 뷰)
# -----------------------------------------------------------
class RecordListView(LoginRequiredMixin, ListView):
    model = DiseaseRecord
    template_name = 'records/record_list.html'
    context_object_name = 'records'
    paginate_by = 10
    login_url = reverse_lazy('login')

    def get_queryset(self):
        # 📝 'occupation' -> 'job'으로 변경
        queryset = super().get_queryset().select_related('case', 'last_modified_by', 'disease', 'job').prefetch_related('exposure')
        query = self.request.GET.get('q', '').strip()

        if query:
            queryset = queryset.filter(
                Q(case__fid__icontains=query) |
                Q(disease__disease_name__icontains=query) |
                # 📝 'occupation__occupation__icontains' -> 'job__occupation__icontains'로 변경
                Q(job__occupation__icontains=query) |
                Q(exposure__name__icontains=query) |
                Q(fnames__icontains=query) |
                Q(decision__icontains=query) |
                Q(smry__icontains=query)
            ).distinct()

        fid_query = self.request.GET.get('fid')
        if fid_query:
            queryset = queryset.filter(case__fid__icontains=fid_query)

        filter_configs = {
            'disease_name': self.request.GET.get('disease_name'),
            # 📝 'occupation' -> 'job'으로 변경
            'job': self.request.GET.get('job'),
            'exposure': self.request.GET.get('exposure'),
            'decision': self.request.GET.get('decision'),
            'year': self.request.GET.get('year'),
        }

        for field, param_value in filter_configs.items():
            if param_value:
                values = [v.strip() for v in param_value.split(',') if v.strip()]
                if values:
                    if field == 'year':
                        queryset = queryset.annotate(
                            year_str=Substr('case__fid', 6, 4)
                        ).filter(
                            case__fid__startswith='kosha',
                            year_str__in=values
                        )
                    elif field == 'exposure':
                        q_objects = Q()
                        for val in values:
                            q_objects |= Q(exposure__name=val)
                        queryset = queryset.filter(q_objects).distinct()
                    elif field == 'disease_name':
                        q_objects = Q()
                        for val in values:
                            # ForeignKey 관계에서는 관련 필드를 통해 검색
                            q_objects |= Q(disease__disease_name__iexact=val)
                        queryset = queryset.filter(q_objects)
                    elif field == 'job':
                        q_objects = Q()
                        for val in values:
                            # ForeignKey 관계에서는 관련 필드를 통해 검색
                            q_objects |= Q(job__occupation__iexact=val)
                        queryset = queryset.filter(q_objects)
                    else:
                        q_objects = Q()
                        for val in values:
                            # 다른 필드들은 기존처럼 처리
                            q_objects |= Q(**{f"{field}__iexact": val})
                        queryset = queryset.filter(q_objects)
        
        ids_from = self.request.GET.get('ids_from', '').strip()
        ids_to = self.request.GET.get('ids_to', '').strip()

        if ids_from.isdigit() or ids_to.isdigit():
            queryset = queryset.annotate(ids_as_int=Cast('ids', output_field=IntegerField()))
        if ids_from.isdigit():
            queryset = queryset.filter(ids_as_int__gte=int(ids_from))
        if ids_to.isdigit():
            queryset = queryset.filter(ids_as_int__lte=int(ids_to))
        
        selected_changed_fields = self.request.GET.getlist('changed_fields')
        if selected_changed_fields:
            for field in selected_changed_fields:
                queryset = queryset.filter(changed_fields__icontains=field)

        sort_by = self.request.GET.get('sort', '-created_at')
        order = self.request.GET.get('order', 'desc')
        
        if order == 'desc':
            sort_by = f"-{sort_by.lstrip('-')}"
        else:
            sort_by = sort_by.lstrip('-')

        if hasattr(DiseaseRecord, sort_by.lstrip('-').split('__')[0]):
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort', '-created_at')
        context['order'] = self.request.GET.get('order', 'desc')
        
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        if 'sort' in query_params:
            del query_params['sort']
        if 'order' in query_params:
            del query_params['order']
        context['other_params'] = query_params.urlencode()
        # 상세 페이지로 이동할 때 사용할 모든 파라미터 (페이지 포함)
        all_params = self.request.GET.copy()
        context['all_params'] = all_params.urlencode()
        context['ids_from'] = self.request.GET.get('ids_from', '')
        context['ids_to'] = self.request.GET.get('ids_to', '')
        context['selected_changed_fields'] = self.request.GET.getlist('changed_fields')

        return context

# -----------------------------------------------------------
# RecordDetailView (상세 페이지 뷰)
# -----------------------------------------------------------
class RecordDetailView(LoginRequiredMixin, DetailView):
    model = DiseaseRecord
    template_name = 'records/record_detail.html'
    context_object_name = 'record'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = self.object

        query_params = self.request.GET.copy()
        context['other_params'] = query_params.urlencode()

        # ✅ original_data는 "최초" 열에 표시되는 값 (original_* 필드)
        context['original_data'] = {
            'disease_name': record.original_disease_name or '',
            'disease_code': record.original_disease_code or '',
            'additional_disease_name': record.original_additional_disease_name or '',
            'additional_disease_code': record.original_additional_disease_code or '',
            # 📝 'occupation' -> 'job'으로 변경
            'job': record.original_job or '',
            'job_code': record.original_job_code or '',
            'exposure': record.original_exposure or '',
            'decision': record.original_decision or '',
            'smry': record.original_smry or '',
            'exp_start': record.original_exp_start or '',
            'exp_period': record.original_exp_period or '',
            'pdf_link': record.original_pdf_link,
            'pop_link': record.original_pop_link,
            'process_link': record.original_process_link
        }

        # ✅ current_data는 "최종(수정)" 열의 초기값으로 사용되는 값 (현재 저장된 값 또는 original 값)
        # 현재 저장된 값이 없으면 original 값을 기본값으로 사용 (RecordUpdateView와 동일한 로직)
        context['current_data'] = {
            'disease_name': record.disease.disease_name if record.disease else (record.original_disease_name or ''),
            'disease_code': record.disease_code or record.original_disease_code or '',
            'additional_disease_name': record.additional_disease_name or record.original_additional_disease_name or '',
            'additional_disease_code': record.additional_disease_code or record.original_additional_disease_code or '',
            # 📝 'occupation' -> 'job'으로 변경
            'job': record.job.occupation if record.job else (record.original_job or ''),
            'job_code': record.job_code or record.original_job_code or '',
            'exposure': ', '.join([e.name for e in record.exposure.all()]) if record.exposure.exists() else (record.original_exposure or ''),
            'decision': record.decision or record.original_decision or '',
            'smry': record.smry or record.original_smry or '',
            'exp_start': record.exp_start if record.exp_start is not None else (record.original_exp_start if record.original_exp_start is not None else ''),
            'exp_period': record.exp_period if record.exp_period is not None else (record.original_exp_period if record.original_exp_period is not None else ''),
            'pdf_link': record.pdf_link,
            'pop_link': record.pop_link,
            'process_link': record.process_link
        }
        context['population_data'] = record.case.population_data.all()
        context['work_process_data'] = record.case.work_processes.all()

        # 수정 이력 추가 (최신순으로 정렬)
        context['revision_history'] = record.revisions.all().order_by('-modified_at')

        return context

# -----------------------------------------------------------
# RecordUpdateView (수정 페이지 뷰)
# -----------------------------------------------------------
class RecordUpdateView(LoginRequiredMixin, UpdateView):
    model = DiseaseRecord
    form_class = DiseaseRecordForm
    template_name = 'records/record_form.html'
    context_object_name = 'record'
    login_url = reverse_lazy('login')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = self.object

        query_params = self.request.GET.copy()
        context['other_params'] = query_params.urlencode()

        # ✅ original_data는 "최초" 열에 표시되는 값 (original_* 필드)
        context['original_data'] = {
            'disease_name': record.original_disease_name or '',
            'disease_code': record.original_disease_code or '',
            'job': record.original_job or '',
            'job_code': record.original_job_code or '',
            'exposure': record.original_exposure or '',
            'decision': record.original_decision or '',
            'smry': record.original_smry or '',
            'exp_start': record.original_exp_start or '',
            'exp_period': record.original_exp_period or '',
            'additional_disease_name': record.original_additional_disease_name or '',
            'additional_disease_code': record.original_additional_disease_code or '',
        }

        # ✅ current_data는 "최종(수정)" 열의 초기값으로 사용되는 값 (현재 저장된 값 또는 original 값)
        # 현재 저장된 값이 없으면 original 값을 기본값으로 사용
        context['current_data'] = {
            'disease_name': record.disease.disease_name if record.disease else (record.original_disease_name or ''),
            'disease_code': record.disease_code or record.original_disease_code or '',
            'job': record.job.occupation if record.job else (record.original_job or ''),
            'job_code': record.job_code or record.original_job_code or '',
            'exposure': ', '.join([e.name for e in record.exposure.all()]) if record.exposure.exists() else (record.original_exposure or ''),
            'decision': record.decision or record.original_decision or '',
            'smry': record.smry or record.original_smry or '',
            'exp_start': record.exp_start if record.exp_start is not None else (record.original_exp_start if record.original_exp_start is not None else ''),
            'exp_period': record.exp_period if record.exp_period is not None else (record.original_exp_period if record.original_exp_period is not None else ''),
            'additional_disease_name': record.additional_disease_name or record.original_additional_disease_name or '',
            'additional_disease_code': record.additional_disease_code or record.original_additional_disease_code or '',
        }

        # ✅ 추가 context 데이터
        if record.disease:
            context['initial_disease'] = [{'id': record.disease.id, 'name': record.disease.disease_name}]
        if record.job:
            context['initial_job'] = [{'id': record.job.id, 'name': record.job.occupation}]

        context['initial_exposures'] = list(record.exposure.all().values('id', 'name'))
        context['initial_disease_names'] = [name.strip() for name in (record.original_disease_name or "").split(',') if name.strip()]
        context['initial_jobs'] = [name.strip() for name in (record.original_job or "").split(',') if name.strip()]
        context['exposure_dictionary'] = list(ExposureDictionary.objects.values_list('name', flat=True))

        return context

    def get_success_url(self):
        query_params = self.request.GET.urlencode()
        base_detail_url = reverse('record_detail', kwargs={'pk': self.object.pk})
        return f"{base_detail_url}?{query_params}" if query_params else base_detail_url

    def form_invalid(self, form):
        """폼이 유효하지 않을 때 호출되며, context를 다시 생성하여 템플릿에 전달"""
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def form_valid(self, form):
        record_to_save = form.save(commit=False)
        record_from_db = get_object_or_404(DiseaseRecord, pk=self.object.pk)
        changed_fields = []

        # 변경 전 값 저장 (revision history용)
        before_values = {}
        after_values = {}

        # Disease 처리
        disease_name = self.request.POST.get('disease', '').strip()
        if disease_name:
            from dictionaries.models import DiseaseDictionaryEntry
            try:
                disease_entry = DiseaseDictionaryEntry.objects.get(disease_name=disease_name)
                record_to_save.disease = disease_entry
            except DiseaseDictionaryEntry.DoesNotExist:
                record_to_save.disease = None
        else:
            record_to_save.disease = None

        # Job 처리
        job_name = self.request.POST.get('job', '').strip()
        if job_name:
            from dictionaries.models import JobCodeOccupation
            try:
                job_entry = JobCodeOccupation.objects.get(occupation=job_name)
                record_to_save.job = job_entry
            except JobCodeOccupation.DoesNotExist:
                record_to_save.job = None
        else:
            record_to_save.job = None

        # 코드 필드 처리
        record_to_save.disease_code = self.request.POST.get('disease_code_display', '')
        record_to_save.job_code = self.request.POST.get('job_code_display', '')

        # 추가 질병 필드 처리 (모듈화된 함수 사용)
        additional_disease_name, additional_disease_code, has_additional_changes = save_additional_disease_fields(
            record_to_save, self.request.POST
        )
        if has_additional_changes:
            if additional_disease_name != (record_from_db.additional_disease_name or ''):
                changed_fields.append('additional_disease_name')
                before_values['additional_disease_name'] = record_from_db.additional_disease_name or ''
                after_values['additional_disease_name'] = additional_disease_name
            if additional_disease_code != (record_from_db.additional_disease_code or ''):
                changed_fields.append('additional_disease_code')
                before_values['additional_disease_code'] = record_from_db.additional_disease_code or ''
                after_values['additional_disease_code'] = additional_disease_code

        # 핵심 필드들 보존 (수정되지 않도록)
        record_to_save.ids = record_from_db.ids
        record_to_save.case = record_from_db.case
        record_to_save.fnames = record_from_db.fnames

        # 변경 사항 감지 및 기록
        if self.request.POST.get('disease_name') != record_from_db.original_disease_name:
            changed_fields.append('disease_name')
            before_values['disease_name'] = record_from_db.disease.disease_name if record_from_db.disease else ''
            after_values['disease_name'] = disease_name

        if self.request.POST.get('disease_code') != record_from_db.original_disease_code:
            changed_fields.append('disease_code')
            before_values['disease_code'] = record_from_db.disease_code or ''
            after_values['disease_code'] = record_to_save.disease_code or ''

        if self.request.POST.get('job') != record_from_db.original_job:
            changed_fields.append('job')
            before_values['job'] = record_from_db.job.occupation if record_from_db.job else ''
            after_values['job'] = job_name

        if self.request.POST.get('job_code') != record_from_db.original_job_code:
            changed_fields.append('job_code')
            before_values['job_code'] = record_from_db.job_code or ''
            after_values['job_code'] = record_to_save.job_code or ''

        if record_to_save.decision != record_from_db.decision:
            changed_fields.append('decision')
            before_values['decision'] = record_from_db.decision or ''
            after_values['decision'] = record_to_save.decision or ''

        if record_to_save.smry != record_from_db.smry:
            changed_fields.append('smry')
            before_values['smry'] = record_from_db.smry or ''
            after_values['smry'] = record_to_save.smry or ''

        if str(record_to_save.exp_start or '') != str(record_from_db.exp_start or ''):
            changed_fields.append('exp_start')
            before_values['exp_start'] = record_from_db.exp_start or ''
            after_values['exp_start'] = record_to_save.exp_start or ''

        if str(record_to_save.exp_period or '') != str(record_from_db.exp_period or ''):
            changed_fields.append('exp_period')
            before_values['exp_period'] = record_from_db.exp_period or ''
            after_values['exp_period'] = record_to_save.exp_period or ''

        exposure_from_post = self.request.POST.get('exposure', '')
        new_exposure_names = set([item.strip() for item in exposure_from_post.split(',') if item.strip()])
        current_exposure_names = set([e.name for e in record_from_db.exposure.all()])
        if new_exposure_names != current_exposure_names:
            changed_fields.append('exposure')
            before_values['exposure'] = ", ".join(sorted(current_exposure_names))
            after_values['exposure'] = ", ".join(sorted(new_exposure_names))

        confirmed_fields = [
            'disease_confirmed',
            'job_confirmed',
            'exposure_confirmed',
            'decision_confirmed',
            'smry_confirmed'
        ]
        for field in confirmed_fields:
            new_value = (self.request.POST.get(field) == 'on')
            old_value = getattr(record_from_db, field)
            if new_value != old_value:
                changed_fields.append(field)
                before_values[field] = old_value
                after_values[field] = new_value
            setattr(record_to_save, field, new_value)

        # 변경된 필드와 메타데이터 설정
        record_to_save.changed_fields = ",".join(list(set(changed_fields)))
        record_to_save.last_modified_by = self.request.user

        # 저장
        record_to_save.save()

        # Exposure (ManyToMany) 처리
        exposure_names = self.request.POST.get('exposure', '')
        if exposure_names:
            exposure_list = [name.strip() for name in exposure_names.split(',') if name.strip()]
            from dictionaries.models import ExposureDictionary
            exposures = []
            for name in exposure_list:
                try:
                    exp = ExposureDictionary.objects.get(name=name)
                    exposures.append(exp)
                except ExposureDictionary.DoesNotExist:
                    pass  # 존재하지 않는 유해인자는 무시
            record_to_save.exposure.set(exposures)
        else:
            record_to_save.exposure.clear()

        # ✅ original 필드는 최초 임포트 시에만 설정되며, 이후 수정 시에는 절대 변경되지 않습니다.
        # 이 로직은 제거되었습니다.

        # 변경사항이 있으면 revision history 생성
        if changed_fields:
            from .models import RecordRevision

            # 변경 카테고리 요약 생성
            summary_categories = []
            changed_set = set(changed_fields)

            if changed_set.intersection({'disease_name', 'disease_code'}):
                summary_categories.append('질병')
            if changed_set.intersection({'additional_disease_name', 'additional_disease_code'}):
                summary_categories.append('추가질병')
            if changed_set.intersection({'job', 'job_code'}):
                summary_categories.append('직종')
            if changed_set.intersection({'exposure', 'exp_start', 'exp_period'}):
                summary_categories.append('노출')
            if changed_set.intersection({'smry', 'decision'}):
                summary_categories.append('진단/결정')
            if changed_set.intersection({'disease_confirmed', 'job_confirmed', 'exposure_confirmed', 'decision_confirmed', 'smry_confirmed'}):
                summary_categories.append('확인상태')

            summary = ', '.join(summary_categories) + ' 변경'

            RecordRevision.objects.create(
                record=record_to_save,
                modified_by=self.request.user,
                changed_fields=",".join(changed_fields),
                summary=summary,
                before_values=before_values,
                after_values=after_values
            )

        self.object = record_to_save
        return redirect(self.get_success_url())

# -----------------------------------------------------------
# 사전(Dictionary) 목록 뷰
# -----------------------------------------------------------
class ExposureDictionaryListView(LoginRequiredMixin, ListView):
    model = ExposureDictionary
    template_name = 'records/exposure_dictionary_list.html'
    context_object_name = 'dictionary_entries'
    paginate_by = 25

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        queryset = super().get_queryset().order_by('name')

        if query:
            queryset = queryset.filter(name__icontains=query)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context
    
class DiseaseDictionaryListView(LoginRequiredMixin, ListView):
    model = DiseaseDictionaryEntry
    template_name = 'records/disease_dictionary_list.html'
    context_object_name = 'dictionary_entries'
    paginate_by = 25

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        queryset = DiseaseDictionaryEntry.objects.all().order_by('disease_name')
        if query:
            queryset = queryset.filter(Q(disease_name__icontains=query) | Q(disease_code__icontains=query))
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context
    

@login_required
def proxy_rag_search(request):
    """
    RAG 검색 API 요청을 서버 측에서 처리하는 프록시 뷰
    """
    query = request.GET.get('query', '')
    if not query:
        return JsonResponse({'error': '쿼리가 제공되지 않았습니다.'}, status=400)
    
    rag_api_url = "https://sehnr.org/jobsearch/api/search/"
    try:
        # 서버에서 직접 외부 API 호출
        response = requests.get(rag_api_url, params={'query': query})
        response.raise_for_status() # HTTP 오류가 발생하면 예외를 발생시킵니다.
        data = response.json()
        return JsonResponse(data)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f"프록시 검색 중 오류 발생: {str(e)}"}, status=500)

def ai_search_popup(request):
    """AI 검색 팝업 페이지 (로그인 불필요)"""
    target = request.GET.get('target', 'disease')
    title = request.GET.get('title', 'AI 검색')
    query = request.GET.get('query', '')

    context = {
        'target': target,
        'title': title,
        'initial_query': query
    }
    return render(request, 'records/ai_search_popup.html', context)

@login_required
def reset_record(request, pk):
    """레코드를 원본 데이터로 복원하는 API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 메서드만 허용됩니다.'}, status=405)

    try:
        record = get_object_or_404(DiseaseRecord, pk=pk)

        # 원본 데이터로 복원
        record.disease = None  # ForeignKey 초기화
        record.job = None      # ForeignKey 초기화
        record.exposure.clear()  # ManyToMany 초기화

        # 현재 데이터를 원본 데이터로 복원
        record.disease_code = record.original_disease_code or ''
        record.job_code = record.original_job_code or ''
        record.decision = record.original_decision or ''
        record.smry = record.original_smry or ''
        record.exp_start = record.original_exp_start
        record.exp_period = record.original_exp_period
        record.pdf_link = record.original_pdf_link or ''
        record.pop_link = record.original_pop_link or ''
        record.process_link = record.original_process_link or ''

        # 확인 상태 초기화
        record.disease_confirmed = False
        record.job_confirmed = False
        record.exposure_confirmed = False
        record.decision_confirmed = False
        record.smry_confirmed = False

        # 변경 필드 초기화
        record.changed_fields = ''
        record.last_modified_by = request.user

        record.save()

        return JsonResponse({'success': True, 'message': '레코드가 성공적으로 복원되었습니다.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
