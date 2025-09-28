import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
# 📝 records.models 대신 dictionaries.models에서 가져옵니다.
from dictionaries.models import DiseaseDictionaryEntry 
import re

class Command(BaseCommand):
    help = 'Imports and cleans disease dictionary data.'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'data', 'disease_dic.xlsx')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Reading data from {file_path}...")
        df = pd.read_excel(file_path, dtype=str).fillna('')

        if '질병명' not in df.columns or '질병코드' not in df.columns:
            self.stdout.write(self.style.ERROR("Excel file must have '질병명' and '질병코드' columns."))
            return
        
        original_count = len(df)
        df.drop_duplicates(subset=['질병명'], keep='first', inplace=True)
        unique_count = len(df)
        self.stdout.write(f"Removed {original_count - unique_count} duplicate entries based on '질병명'.")

        DiseaseDictionaryEntry.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Old disease dictionary data deleted."))

        self.stdout.write("Importing cleaned data...")
        count = 0
        for _, row in df.iterrows():
            disease_name = row['질병명'].strip()
            
            # ▼▼▼▼▼ 질병 코드 클리닝 로직 ▼▼▼▼▼
            disease_code_raw = row['질병코드'].strip()
            # 영문자와 숫자, 점(.), 쉼표(,), 하이픈(-)만 남기고 모두 제거 후 대문자화
            disease_code_cleaned = re.sub(r'[^A-Z0-9.,-]', '', disease_code_raw.upper())
            # ▲▲▲▲▲ 클리닝 완료 ▲▲▲▲▲
            
            if disease_name:
                DiseaseDictionaryEntry.objects.create(
                    disease_name=disease_name,
                    disease_code=disease_code_cleaned # 깨끗해진 코드를 저장
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {count} unique disease entries."))
