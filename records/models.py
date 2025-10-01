from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# 👇 사전 모델들을 dictionaries 앱에서 import 합니다.
from dictionaries.models import DiseaseDictionaryEntry, JobCodeOccupation, ExposureDictionary

## Case 모델
class Case(models.Model):
    """'fid'를 고유 키로 사용하는 사건 파일 모델"""
    fid = models.CharField(max_length=255, primary_key=True, verbose_name="사건 FID")

    def __str__(self):
        return self.fid

    class Meta:
        verbose_name = "사건 파일"
        verbose_name_plural = "사건 파일 목록"
        ordering = ['fid']

## DiseaseRecord 모델
class DiseaseRecord(models.Model):
    """질병 기록의 핵심 데이터 모델"""
    case = models.ForeignKey(Case, to_field='fid', on_delete=models.CASCADE, related_name='disease_records', verbose_name="사건 파일")
    ids = models.CharField(max_length=255, verbose_name='IDS', null=True, blank=True)
    fnames = models.TextField(verbose_name="파일 이름", null=True, blank=True)

    # 사전(Dictionary)과의 관계
    disease = models.ForeignKey(DiseaseDictionaryEntry, on_delete=models.SET_NULL, verbose_name="표준 질병", null=True, blank=True)
    # 📝 occupation -> job으로 변경
    job = models.ForeignKey(JobCodeOccupation, on_delete=models.SET_NULL, verbose_name="표준 직종", null=True, blank=True)
    exposure = models.ManyToManyField(ExposureDictionary, blank=True, verbose_name="표준 유해인자")
    
    # 기록 값
    disease_code = models.CharField(max_length=255, verbose_name="질병 코드", null=True, blank=True)
    additional_disease_name = models.CharField(max_length=255, verbose_name="추가 질병명", null=True, blank=True)
    additional_disease_code = models.CharField(max_length=255, verbose_name="추가 질병 코드", null=True, blank=True)
    job_code = models.CharField(max_length=50, verbose_name="직종 코드", null=True, blank=True)
    decision = models.TextField(max_length=100, verbose_name="결정 사항", null=True, blank=True)
    smry = models.TextField(verbose_name="고찰", null=True, blank=True)
    pdf_link = models.URLField(max_length=1024, verbose_name="PDF 링크", null=True, blank=True)
    exp_start = models.IntegerField(verbose_name="노출 시작 연도", null=True, blank=True)
    exp_period = models.IntegerField(verbose_name="노출 기간(년)", null=True, blank=True)
    process_link = models.URLField(max_length=1024, verbose_name="공정 링크", null=True, blank=True)
    pop_link = models.URLField(max_length=1024, verbose_name="인구 링크", null=True, blank=True)

    # 최초 데이터 (수정 전 원본 값)
    original_ids = models.CharField(max_length=255, verbose_name="최초 IDS", null=True, blank=True)
    original_disease_name = models.CharField(max_length=255, verbose_name="최초 질병명", null=True, blank=True)
    original_disease_code = models.CharField(max_length=255, verbose_name="최초 질병 코드", null=True, blank=True)
    original_additional_disease_name = models.CharField(max_length=255, verbose_name="최초 추가 질병명", null=True, blank=True)
    original_additional_disease_code = models.CharField(max_length=255, verbose_name="최초 추가 질병 코드", null=True, blank=True)
    # 📝 original_occupation -> original_job으로 변경
    original_job = models.CharField(max_length=255, verbose_name="최초 직종", null=True, blank=True)
    original_job_code = models.CharField(max_length=50, verbose_name="최초 직종 코드", null=True, blank=True)
    original_decision = models.TextField(max_length=1000, verbose_name="최초 결정 사항", null=True, blank=True)
    original_smry = models.TextField(verbose_name="최초 고찰", null=True, blank=True)
    original_exposure = models.TextField(max_length=255, verbose_name="최초 유해인자", null=True, blank=True)
    original_pdf_link = models.URLField(max_length=2048, verbose_name="최초 PDF 링크", null=True, blank=True)
    original_exp_start = models.IntegerField(verbose_name="최초 노출 시작 연도", null=True, blank=True)
    original_exp_period = models.IntegerField(verbose_name="최초 노출 기간(년)", null=True, blank=True)
    original_process_link = models.URLField(max_length=2048, verbose_name="최초 공정 링크", null=True, blank=True)
    original_pop_link = models.URLField(max_length=2048, verbose_name="최초 인구 링크", null=True, blank=True)

    # 기록 상태
    disease_confirmed = models.BooleanField(default=False, verbose_name="질병확인")
    # 📝 occupation_confirmed -> job_confirmed로 변경
    job_confirmed = models.BooleanField(default=False, verbose_name="직종확인")
    exposure_confirmed = models.BooleanField(default=False, verbose_name="유해인자확인")
    decision_confirmed = models.BooleanField(default=False, verbose_name="결정확인")
    smry_confirmed = models.BooleanField(default=False, verbose_name="고찰확인")
    changed_fields = models.TextField(verbose_name="변경된 항목", null=True, blank=True)

    # 메타데이터
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="수정한 사람")
    last_modified_at = models.DateTimeField(auto_now=True, verbose_name="수정 시간")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시간")

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new:
            if self.disease:
                self.original_disease_name = self.disease.disease_name
            # 📝 self.occupation -> self.job으로 변경
            if self.job:
                # 📝 original_occupation -> original_job으로 변경
                self.original_job = self.job.occupation

            self.original_ids = self.ids
            self.original_disease_code = self.disease_code
            self.original_job_code = self.job_code
            self.original_decision = self.decision
            self.original_smry = self.smry
            self.original_pdf_link = self.pdf_link
            self.original_exp_start = self.exp_start
            self.original_exp_period = self.exp_period
            self.original_process_link = self.process_link
            self.original_pop_link = self.pop_link
            self.original_additional_disease_name = self.additional_disease_name
            self.original_additional_disease_code = self.additional_disease_code

            # 처음 생성 시 original 값을 현재 필드에도 복사 (최초 = 최종)
            if not self.disease_code and self.original_disease_code:
                self.disease_code = self.original_disease_code
            if not self.job_code and self.original_job_code:
                self.job_code = self.original_job_code
            if not self.decision and self.original_decision:
                self.decision = self.original_decision
            if not self.smry and self.original_smry:
                self.smry = self.original_smry
            if not self.exp_start and self.original_exp_start:
                self.exp_start = self.original_exp_start
            if not self.exp_period and self.original_exp_period:
                self.exp_period = self.original_exp_period
            if not self.additional_disease_name and self.original_additional_disease_name:
                self.additional_disease_name = self.original_additional_disease_name
            if not self.additional_disease_code and self.original_additional_disease_code:
                self.additional_disease_code = self.original_additional_disease_code

        super().save(*args, **kwargs)

        if is_new and not self.original_exposure:
            exposure_names = ", ".join([e.name for e in self.exposure.all()])
            if self.original_exposure != exposure_names:
                self.original_exposure = exposure_names
                self.save(update_fields=['original_exposure'])

    def __str__(self):
        disease_display = self.disease.disease_name if self.disease else "N/A"
        # 📝 self.occupation -> self.job으로 변경
        job_display = self.job.occupation if self.job else "N/A"
        # 📝 occupation -> job으로 변경
        return f"FID: {self.case.fid}, 질병: {disease_display}, 직종: {job_display}"

    class Meta:
        verbose_name = "질병 기록"
        verbose_name_plural = "질병 기록들"
        ordering = ['-created_at']

    @property
    def changed_fields_str(self):
        if not self.changed_fields:
            return ""

        changed_set = set(self.changed_fields.split(','))
        summary_categories = []

        if changed_set.intersection({'disease_name', 'disease_code'}):
            summary_categories.append('질병')
        # 📝 occupation -> job으로 변경
        if changed_set.intersection({'job', 'job_code'}):
            summary_categories.append('직종')
        if changed_set.intersection({'exposure', 'exp_start', 'exp_period'}):
            summary_categories.append('노출')
        if changed_set.intersection({'smry', 'decision'}):
            summary_categories.append('논리')
        # 📝 occupation_confirmed -> job_confirmed로 변경
        if changed_set.intersection({'disease_confirmed', 'job_confirmed', 'exposure_confirmed', 'decision_confirmed', 'smry_confirmed'}):
             summary_categories.append('확인 상태')

        return ', '.join(summary_categories)
    
## 인구 정보 및 작업 공정 정보 모델
class PopulationData(models.Model):
    case = models.ForeignKey(Case, to_field='fid', on_delete=models.CASCADE, related_name='population_data', verbose_name="사건 파일")
    variable = models.CharField(max_length=255, verbose_name="변수명")
    value = models.TextField(verbose_name="값")

    def __str__(self):
        return f"{self.case.fid} - {self.variable}"

    class Meta:
        unique_together = ('case', 'variable')
        verbose_name = "인구학적 정보"
        verbose_name_plural = "인구학적 정보 목록"

class WorkProcessData(models.Model):
    case = models.ForeignKey(Case, to_field='fid', on_delete=models.CASCADE, related_name='work_processes', verbose_name="사건 파일")
    variable = models.CharField(max_length=255, verbose_name="변수명")
    value = models.TextField(verbose_name="값")

    def __str__(self):
        return f"{self.case.fid} - {self.variable}"

    class Meta:
        unique_together = ('case', 'variable')
        verbose_name = "작업 공정 정보"
        verbose_name_plural = "작업 공정 정보 목록"

## 수정 이력 모델
class RecordRevision(models.Model):
    """질병 기록의 수정 이력을 저장하는 모델"""
    record = models.ForeignKey(DiseaseRecord, on_delete=models.CASCADE, related_name='revisions', verbose_name="질병 기록")
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="수정자")
    modified_at = models.DateTimeField(auto_now_add=True, verbose_name="수정 시간")
    changed_fields = models.TextField(verbose_name="변경된 필드", blank=True)

    # 변경 내용 요약
    summary = models.CharField(max_length=500, verbose_name="변경 요약", blank=True)

    # 변경 전후 값 (JSON 형태로 저장)
    before_values = models.JSONField(verbose_name="변경 전 값", blank=True, default=dict)
    after_values = models.JSONField(verbose_name="변경 후 값", blank=True, default=dict)

    def __str__(self):
        return f"{self.record.case.fid} - {self.modified_at.strftime('%Y-%m-%d %H:%M')} by {self.modified_by}"

    class Meta:
        verbose_name = "수정 이력"
        verbose_name_plural = "수정 이력 목록"
        ordering = ['-modified_at']

    @property
    def changed_fields_list(self):
        """변경된 필드를 리스트로 반환"""
        if not self.changed_fields:
            return []
        return [field.strip() for field in self.changed_fields.split(',') if field.strip()]

    @property
    def changed_categories(self):
        """변경된 카테고리를 반환"""
        if not self.changed_fields:
            return []

        changed_set = set(self.changed_fields_list)
        categories = []

        if changed_set.intersection({'disease_name', 'disease_code', 'disease'}):
            categories.append('질병')
        if changed_set.intersection({'job', 'job_code'}):
            categories.append('직종')
        if changed_set.intersection({'exposure', 'exp_start', 'exp_period'}):
            categories.append('노출')
        if changed_set.intersection({'smry', 'decision'}):
            categories.append('진단/결정')
        if changed_set.intersection({'disease_confirmed', 'job_confirmed', 'exposure_confirmed', 'decision_confirmed', 'smry_confirmed'}):
            categories.append('확인상태')

        return categories

## 사용자 프로필 모델
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now=True, verbose_name="마지막 활동 시간")

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal: 사용자 생성 시 프로필 자동 생성
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()