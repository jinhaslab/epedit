import os
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings 
# FIX 1: dictionaries.models에서 JobCodeOccupation을 가져옵니다.
from dictionaries.models import JobCodeOccupation 

class Command(BaseCommand):
    # FIX: help 텍스트를 모델 필드에 맞게 수정
    help = 'Imports job code and occupation data from an XLSX file using pandas.'

    def add_arguments(self, parser):
        parser.add_argument('xlsx_file', type=str, help='The path to the XLSX file relative to BASE_DIR/data (e.g., job8thstd.xlsx)')

    def handle(self, *args, **options):
        # 파일 경로를 settings.BASE_DIR 기준으로 구성
        # 예: data/job8thstd.xlsx
        excel_file_name = options['xlsx_file']
        excel_file_path = os.path.join(settings.BASE_DIR, 'data', excel_file_name)
        
        if not os.path.exists(excel_file_path):
            self.stdout.write(self.style.ERROR(f"Excel file not found at: {excel_file_path}"))
            self.stdout.write(self.style.WARNING(f"Please ensure '{excel_file_name}' is in your 'data/' directory."))
            return

        self.stdout.write(self.style.SUCCESS(f"Attempting to import data from: {excel_file_path}"))

        try:
            # pandas를 사용하여 엑셀 파일 읽기
            # sheet_name을 지정하지 않으면 기본적으로 첫 번째 시트를 읽습니다.
            df = pd.read_excel(excel_file_path)

            # 필요한 컬럼이 DataFrame에 있는지 확인
            # Excel 컬럼명은 'job_code'와 'job'이라고 가정합니다.
            if 'job_code' not in df.columns or 'job' not in df.columns:
                raise CommandError("Excel file must contain 'job_code' and 'job' columns.")

            imported_count = 0
            updated_count = 0

            # DataFrame의 각 행을 반복하며 데이터베이스에 저장
            for index, row in df.iterrows():
                job_code = str(row['job_code']).strip() if pd.notna(row['job_code']) else ''
                job_name = str(row['job']).strip() if pd.notna(row['job']) else '' # 'job' 컬럼의 값을 가져옵니다.

                if not job_code or not job_name:
                    self.stdout.write(self.style.WARNING(f"Skipping row {index+2} due to missing data (Job Code: {job_code}, Job Name: {job_name})"))
                    continue

                try:
                    # FIX 2: JobCodeOccupation 모델 이름으로 수정
                    obj, created = JobCodeOccupation.objects.update_or_create(
                        job_code=job_code,
                        # FIX 3: JobCodeOccupation 모델의 실제 필드 이름은 'occupation'입니다.
                        defaults={'occupation': job_name} 
                    )
                    if created:
                        imported_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing row {index+2} ({job_code}, {job_name}): {e}"))

            self.stdout.write(self.style.SUCCESS(f'Successfully imported {imported_count} new records and updated {updated_count} existing records.'))

        except Exception as e:
            raise CommandError(f'Error importing XLSX data: {e}')
