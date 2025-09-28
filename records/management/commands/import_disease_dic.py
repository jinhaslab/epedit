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
        swap_count = 0  # 뒤바뀐 항목 카운트

        for _, row in df.iterrows():
            disease_name_raw = row['질병명'].strip()
            disease_code_raw = row['질병코드'].strip()

            # ▼▼▼▼▼ 데이터 뒤바뀜 감지 및 수정 로직 ▼▼▼▼▼
            # 질병명이 코드처럼 보이고, 코드가 한글 질병명처럼 보이는 경우 감지
            name_looks_like_code = bool(re.match(r'^[A-Z0-9.,-]+$', disease_name_raw))
            code_has_korean = bool(re.search(r'[가-힣]', disease_code_raw))

            if name_looks_like_code and code_has_korean:
                # 뒤바뀐 것으로 판단되면 교체
                disease_name = disease_code_raw
                disease_code_cleaned = re.sub(r'[^A-Z0-9.,-]', '', disease_name_raw.upper())
                swap_count += 1
                self.stdout.write(f"  SWAPPED: '{disease_name_raw}' <-> '{disease_code_raw}'")
            else:
                # 정상적인 경우
                disease_name = disease_name_raw
                disease_code_cleaned = re.sub(r'[^A-Z0-9.,-]', '', disease_code_raw.upper())
            # ▲▲▲▲▲ 뒤바뀜 수정 완료 ▲▲▲▲▲

            if disease_name:
                DiseaseDictionaryEntry.objects.create(
                    disease_name=disease_name,
                    disease_code=disease_code_cleaned
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {count} unique disease entries."))
        if swap_count > 0:
            self.stdout.write(self.style.WARNING(f"Fixed {swap_count} entries where disease name and code were swapped."))
