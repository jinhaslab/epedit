# records/management/commands/import_records.py

import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from records.models import Case, DiseaseRecord
from dictionaries.models import DiseaseDictionaryEntry, JobCodeOccupation
from django.db import transaction

class Command(BaseCommand):
    help = 'Imports raw data and links to dictionaries if possible.'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'data', 'basic_data.xlsx')
        df = pd.read_excel(file_path, dtype=str).fillna('')

        COLUMN_MAP = {'fid': 'fid', 'disease': 'disease', 'job': 'job'}
        if not all(col in df.columns for col in COLUMN_MAP.keys()):
            self.stdout.write(self.style.ERROR(f"Excel must have columns: {', '.join(COLUMN_MAP.keys())}"))
            return
        
        self.stdout.write("Starting import. All raw data will be saved.")
        
        with transaction.atomic():
            DiseaseRecord.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Old disease records deleted."))

            created_count = 0
            for index, row in df.iterrows():
                # 1. 원본 텍스트를 그대로 가져옵니다.
                fid = row.get(COLUMN_MAP['fid'])
                raw_disease = row.get(COLUMN_MAP['disease'])
                raw_job = row.get(COLUMN_MAP['job'])
                
                if not fid or not raw_disease or not raw_job:
                    continue

                case, _ = Case.objects.get_or_create(fid=fid)

                # 2. 사전에 일치하는 항목이 있는지 '시도'합니다.
                disease_link = None
                try:
                    disease_link = DiseaseDictionaryEntry.objects.get(disease_name=raw_disease)
                except DiseaseDictionaryEntry.DoesNotExist:
                    pass # 없어도 괜찮습니다. 그냥 넘어갑니다.

                occupation_link = None
                try:
                    occupation_link = JobCodeOccupation.objects.get(occupation=raw_job)
                except JobCodeOccupation.DoesNotExist:
                    pass # 없어도 괜찮습니다.

                # 3. 원본 텍스트는 항상 저장하고, 링크는 있을 때만 저장합니다.
                DiseaseRecord.objects.create(
                    case=case,
                    raw_disease_name=raw_disease,
                    raw_occupation=raw_job,
                    disease=disease_link,       # 찾았으면 링크, 못찾았으면 None
                    occupation=occupation_link, # 찾았으면 링크, 못찾았으면 None
                    # --- 나머지 필드들 ---
                    ids=row.get('ids', ''),
                    fnames=row.get('fnames', ''),
                    disease_code=row.get('disease_code', ''),
                    job_code=row.get('job_code', ''),
                    # ... (엑셀의 나머지 모든 데이터를 채웁니다) ...
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {created_count} raw records."))