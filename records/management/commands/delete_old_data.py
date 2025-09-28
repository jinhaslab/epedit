# /home/rag/papps/test/records/management/commands/delete_old_data.py

from django.core.management.base import BaseCommand, CommandError
from records.models import DiseaseRecord
from datetime import datetime
from django.utils import timezone # 시간대 인식을 위해 필요

class Command(BaseCommand):
    help = 'Deletes DiseaseRecord entries created before a specified date.'

    def add_arguments(self, parser):
        # 명령 실행 시 날짜 인수를 받도록 설정합니다.
        parser.add_argument(
            'cutoff_date',
            type=str,
            help='The date (YYYY-MM-DD) before which records will be deleted. E.g., 2025-07-26',
        )

    def handle(self, *args, **options):
        cutoff_date_str = options['cutoff_date']

        try:
            # 입력된 날짜 문자열을 datetime 객체로 변환합니다.
            # Django의 DateTimeField는 기본적으로 시간대 인식(timezone aware) 객체를 사용하므로,
            # 입력된 날짜를 시간대 인식 객체로 만들어야 합니다.
            # KST (Asia/Seoul) 기준으로 7월 26일 00:00:00 이전을 의미합니다.
            cutoff_datetime = datetime.strptime(cutoff_date_str, '%Y-%m-%d')
            # settings.TIME_ZONE에 맞춰 시간대 정보를 추가합니다.
            cutoff_datetime = timezone.make_aware(cutoff_datetime, timezone.get_current_timezone())
        except ValueError:
            raise CommandError('Invalid date format. Please use YYYY-MM-DD. Example: 2025-07-26')

        self.stdout.write(self.style.WARNING(f"Attempting to delete records created before: {cutoff_datetime}"))

        # cutoff_datetime 이전에 생성된 레코드들을 쿼리합니다.
        # created_at__lt는 "less than" 즉, ~보다 작은/이전인 조건을 의미합니다.
        records_to_delete = DiseaseRecord.objects.filter(created_at__lt=cutoff_datetime)

        # 삭제될 레코드의 수를 먼저 확인합니다.
        count = records_to_delete.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"No records found created before {cutoff_date_str} to delete."))
            return

        # 사용자에게 삭제를 최종적으로 확인할지 묻습니다.
        self.stdout.write(self.style.WARNING(f"Found {count} records created before {cutoff_date_str}. Do you want to proceed with deletion? (yes/no)"))

        confirm = input()
        if confirm.lower() == 'yes':
            # 레코드들을 삭제합니다.
            deleted_count, _ = records_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_count} records created before {cutoff_date_str}."))
        else:
            self.stdout.write(self.style.NOTICE("Deletion cancelled."))