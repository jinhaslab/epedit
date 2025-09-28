
import os
import pandas as pd
from django.core.management.base import BaseCommand
from records.models import ExposureDictionary
from django.conf import settings

class Command(BaseCommand):
    help = 'Imports exposure dictionary from exp_dic.xlsx.'

    def handle(self, *args, **options):
        excel_file_path = os.path.join(settings.BASE_DIR, 'data', 'exp_dic.xlsx')
        
        if not os.path.exists(excel_file_path):
            self.stdout.write(self.style.ERROR(f"Excel file not found at: {excel_file_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Importing exposure dictionary from: {excel_file_path}"))

        try:
            df = pd.read_excel(excel_file_path)

            # Check if 'exp_dic' column exists
            if 'exp_dic' not in df.columns:
                self.stdout.write(self.style.ERROR("Column 'exp_dic' not found in the Excel file."))
                return

            # Clear existing dictionary
            ExposureDictionary.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Successfully cleared existing exposure dictionary."))

            # Import new data
            for item in df['exp_dic'].dropna().unique():
                ExposureDictionary.objects.create(name=item)
            
            self.stdout.write(self.style.SUCCESS(f"Successfully imported {len(df['exp_dic'].dropna().unique())} unique exposure terms."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing exposure dictionary: {e}"))
