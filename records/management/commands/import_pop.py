import os
import pandas as pd
from django.core.management.base import BaseCommand
from records.models import Case, PopulationData
from django.conf import settings
from django.db import transaction

class Command(BaseCommand):
    help = 'Imports population data from pop_table.xlsx.'

    def handle(self, *args, **options):
        pop_data_path = os.path.join(settings.BASE_DIR, 'data', 'pop_table.xlsx')
        if not os.path.exists(pop_data_path):
            self.stdout.write(self.style.ERROR(f"File not found: {pop_data_path}"))
            return

        self.stdout.write(self.style.WARNING("Deleting old population data..."))
        PopulationData.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Old population data deleted."))
        
        self.stdout.write("Importing from pop_table.xlsx...")
        df_pop = pd.read_excel(pop_data_path).fillna('')
        
        with transaction.atomic():
            for _, row in df_pop.iterrows():
                fid = row.get('fid')
                variable = row.get('variables')
                value = row.get('values')

                if not all([fid, variable]):
                    continue

                try:
                    case_instance = Case.objects.get(fid=fid)
                    PopulationData.objects.update_or_create(
                        case=case_instance,
                        variable=variable,
                        defaults={'value': str(value)}
                    )
                except Case.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Case with fid='{fid}' not found in basic data. Skipping this row."))
        
        self.stdout.write(self.style.SUCCESS(f"Successfully imported population data."))
