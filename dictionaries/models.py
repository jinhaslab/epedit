from django.db import models

class DiseaseDictionaryEntry(models.Model):
    disease_name = models.CharField(max_length=255, unique=True, db_index=True, verbose_name="질병명")
    disease_code = models.CharField(max_length=255, blank=True, null=True, verbose_name="질병코드")

    def __str__(self):
        return self.disease_name
    
    class Meta:
        verbose_name = "질병 사전"
        verbose_name_plural = "질병 사전"
        ordering = ['disease_name']

class JobCodeOccupation(models.Model):
    job_code = models.CharField(max_length=10, unique=True, verbose_name='직종 코드')
    occupation = models.CharField(max_length=255, verbose_name='직종명')

    def __str__(self):
        return f"{self.occupation} ({self.job_code})"

    class Meta:
        verbose_name = '직종 코드-직종명 사전'
        verbose_name_plural = '직종 코드-직종명 사전'
        ordering = ['occupation']

class ExposureDictionary(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="유해인자명")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "유해인자 사전"
        verbose_name_plural = "유해인자 사전"
        ordering = ['name']