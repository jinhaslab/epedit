from django import forms
from .models import DiseaseRecord

class DiseaseRecordForm(forms.ModelForm):
    class Meta:
        model = DiseaseRecord
        # 폼에서 직접 제어하지 않을 필드들을 exclude에 명시합니다.
        exclude = [
            'case',
            'last_modified_by',
            'created_at',
            'changed_fields',
            
            # --- 새로운 구조에 맞게 수정 ---
            'disease',           # ForeignKey 필드 (JS로 제어)
            'job',               # ForeignKey 필드 (JS로 제어)
            'exposure',          # ManyToManyField (JS로 제어)
            
            # --- original 필드들 ---
            'original_ids',
            'original_disease_name',
            'original_disease_code',
            'original_job',
            'original_job_code',
            'original_decision',
            'original_smry',
            'original_exposure',
            'original_pdf_link',
            'original_pop_link',
            'original_process_link',
            'original_exp_start',
            'original_exp_period',
        ]
        
        labels = {
            'ids': 'IDS',
            'fnames': '파일 이름',
            'disease_code': '질병 코드',
            'job_code': '직종 코드',
            'decision': '결정 사항',
            'smry': '고찰',
            'pdf_link': 'PDF 링크',
            'pop_link': '인구 링크',
            'process_link': '공정 링크',
            'exp_start': '노출 시작 연도',
            'exp_period': '노출 기간(년)',
            'disease_confirmed': '질병 확인',
            'job_confirmed': '직종 확인',    # occupation_confirmed -> job_confirmed로 변경
            'decision_confirmed': '결정 확인',
            'exposure_confirmed': '유해인자 확인',
            'smry_confirmed': '고찰 확인',
        }
        widgets = {
            'exp_start': forms.NumberInput(attrs={'class': 'form-control'}),
            'exp_period': forms.NumberInput(attrs={'class': 'form-control'}),
            'decision': forms.Textarea(attrs={'rows': 2}),
            'smry': forms.Textarea(attrs={'rows': 5}),
        }