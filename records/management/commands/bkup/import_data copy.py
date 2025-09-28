#management > commands > import_data.py
import os
import pandas as pd
from django.core.management.base import BaseCommand
from records.models import DiseaseRecord, ExposureFactor, ExposureDictionary, Case
from django.conf import settings
from django.db import transaction

class Command(BaseCommand):
    help = 'Imports data from basic_data.xlsx into the DiseaseRecord model.'

    def handle(self, *args, **options):
        excel_file_path = os.path.join(settings.BASE_DIR, 'data', 'basic_data.xlsx')
        
        if not os.path.exists(excel_file_path):
            self.stdout.write(self.style.ERROR(f"Excel file not found at: {excel_file_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Attempting to import data from: {excel_file_path}"))

        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')

            # Get the set of valid exposure names from the dictionary
            valid_exposures = set(ExposureDictionary.objects.values_list('name', flat=True))
            if not valid_exposures:
                self.stdout.write(self.style.WARNING("Exposure dictionary is empty. Please run `import_exp_dict` first."))

            # Get or create the '기타' ExposureFactor
            etc_factor, _ = ExposureFactor.objects.get_or_create(name='기타')

            # 기존 데이터 삭제
            DiseaseRecord.objects.all().delete()
            # Keep '기타' factor, delete others
            ExposureFactor.objects.exclude(name='기타').delete() 
            
            imported_count = 0
            for index, row in df.iterrows():
                # 원본 유해인자 문자열 저장
                exposure_raw = str(row.get('exposure', ''))

                # DiseaseRecord 객체 생성 (exposure 필드는 나중에 추가)
                record = DiseaseRecord.objects.create(
                    fid=row.get('fid'),
                    fnames=row.get('fnames'),
                    disease_name=row['disease'],
                    disease_code=row['disease_code'],
                    occupation=row['job'],
                    job_code=row['job_code'],
                    decision=row['decision'],
                    smry=row['smry'],                    
                    pdf_link=row['pdf_link'],

                    # 최초 데이터 저장
                    original_disease_name=row['disease'],
                    original_disease_code=row['disease_code'],
                    original_occupation=row['job'],
                    original_job_code=row['job_code'],
                    original_decision=row['decision'],
                    original_smry=row['smry'],
                    original_exposure=exposure_raw
                )

                # 유해인자 처리 (ManyToManyField)
                if exposure_raw:
                    exposure_items = [item.strip() for item in exposure_raw.split(',') if item.strip()]
                    for item_name in exposure_items:
                        if item_name in valid_exposures:
                            factor, _ = ExposureFactor.objects.get_or_create(name=item_name)
                            record.exposure.add(factor)
                        else:
                            record.exposure.add(etc_factor)
                
                imported_count += 1

            self.stdout.write(self.style.SUCCESS(f"Successfully imported {imported_count} records."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing data: {e}"))