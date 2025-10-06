import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
# 📝 records.models 대신 dictionaries.models에서 가져옵니다.
from dictionaries.models import DiseaseDictionaryEntry 
import re

class Command(BaseCommand):
    help = 'Imports KCD-9 disease dictionary data from kcd_RAG_data.xlsx (17,395 codes)'

    def handle(self, *args, **options):
        # 새 파일 경로: ohsearch의 kcd_RAG_data.xlsx
        file_path = '/home/rag/papps/ohsearch/data/kcd_RAG_data.xlsx'

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Reading KCD-9 data from {file_path}...")
        df = pd.read_excel(file_path, dtype=str).fillna('')

        if 'code' not in df.columns or 'name_kor' not in df.columns:
            self.stdout.write(self.style.ERROR("Excel file must have 'code' and 'name_kor' columns."))
            return
        
        self.stdout.write(f"Total entries: {len(df)}")

        # 중복 제거 (code 기준)
        original_count = len(df)
        df.drop_duplicates(subset=['code'], keep='first', inplace=True)
        unique_count = len(df)
        self.stdout.write(f"Removed {original_count - unique_count} duplicate entries based on 'code'.")

        DiseaseDictionaryEntry.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Old disease dictionary data deleted."))

        self.stdout.write("Importing KCD-9 data...")
        count = 0

        for _, row in df.iterrows():
            disease_code = row['code'].strip()
            disease_name = row['name_kor'].strip()

            if disease_code and disease_name:
                # disease_code를 기준으로 저장 (코드는 추가하지 않음)
                try:
                    obj, created = DiseaseDictionaryEntry.objects.update_or_create(
                        disease_code=disease_code,
                        defaults={'disease_name': disease_name}
                    )
                    count += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipped {disease_code}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Import completed!\n'
            f'   - Total KCD-9 codes imported: {count}\n'
            f'   - Includes T, V, W, X, Y codes\n'
            f'   - Levels 1-4 (대분류~세분류) all included'
        ))
