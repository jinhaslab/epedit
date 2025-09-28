# records/management/commands/add_data.py
import os
import pandas as pd
from django.core.management.base import BaseCommand
from records.models import DiseaseRecord, ExposureFactor
from django.conf import settings

class Command(BaseCommand):
    help = 'Adds or updates data from an Excel file into the DiseaseRecord model without deleting existing data.'

    # 파일명을 명령줄 인자로 받을 수 있도록 추가
    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str, help='The name of the Excel file to import from the "data" directory.')

    def handle(self, *args, **options):
        file_name = options['file_name']
        excel_file_path = os.path.join(settings.BASE_DIR, 'data', file_name)
        
        if not os.path.exists(excel_file_path):
            self.stdout.write(self.style.ERROR(f"Excel file not found at: {excel_file_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Attempting to add or update data from: {excel_file_path}"))

        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')

            created_count = 0
            updated_count = 0
            
            for index, row in df.iterrows():
                # fid를 기준으로 객체를 찾거나, 없으면 새로 만들기 위해 기본값(defaults)을 설정합니다.
                defaults = {
                    'fnames': row.get('fnames'),
                    'disease_name': row.get('disease'),
                    'disease_code': row.get('disease_code'),
                    'occupation': row.get('job'),
                    'job_code': row.get('job_code'),
                    'decision': row.get('decision'),
                    'smry': row.get('smry'),
                    'pdf_link': row.get('pdf_link'),
                    'original_exposure': str(row.get('exposure', ''))
                }

                # fid를 기준으로 객체를 가져오거나 생성 (update_or_create)
                # fid가 일치하는 레코드가 있으면 defaults 값으로 업데이트하고, 없으면 새로 생성합니다.
                record, created = DiseaseRecord.objects.update_or_create(
                    fid=row.get('fid'),
                    defaults=defaults
                )

                if created:
                    created_count += 1
                    self.stdout.write(f"  - Created new record for fid: {record.fid}")
                else:
                    updated_count += 1
                    self.stdout.write(f"  - Updated existing record for fid: {record.fid}")

                # 유해인자(Exposure) 처리 (ManyToManyField)
                exposure_raw = str(row.get('exposure', ''))
                
                # 기존 유해인자 연결을 모두 초기화 (업데이트 시 중요)
                record.exposure.clear()

                if exposure_raw:
                    exposure_items = [item.strip() for item in exposure_raw.split(',') if item.strip()]
                    for item_name in exposure_items:
                        factor, _ = ExposureFactor.objects.get_or_create(name=item_name)
                        record.exposure.add(factor)

            self.stdout.write(self.style.SUCCESS(
                f"Successfully processed data. Created: {created_count}, Updated: {updated_count} records."
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing data: {e}"))