from django.core.management.base import BaseCommand
from reeftrack_app.models import Municipality, Barangay


class Command(BaseCommand):
    help = 'Seed Municipality and Barangay data for Sarangani Bay Protected Seascapes (SBPS)'

    def handle(self, *args, **options):
        # Sarangani Bay municipalities and their barangays
        data = {
            'Alabel': [
                'Alegria', 'Alna', 'Balian', 'Baluntay', 'Datalbong',
                'Datal-udas', 'Duel', 'E. Martinez', 'El Palmar',
                'Kalaneg', 'Kawayan', 'Lacsap-anan', 'Laguma',
                'Liberty', 'Lumbayao', 'Malaklunoy', 'Molita',
                'Poblacion', 'San Roque', 'Santa Maria', 'Sulit',
                'Tambilil', 'Tantang', 'Tio-ongon', 'Wa Municip',
            ],
            'Glan': [
                'Adlaon', 'Baliton', 'Batoteling', 'Baybay',
                'Bualan', 'Bulatok', 'Bulatus', 'Calabalol',
                'Dualing', 'Dukaln', 'Dunguan', 'Calumpang',
                'E. Lopez', 'Elite', 'Espaka', 'F. Pichon',
                'Glan', 'Glan Peidu', 'Gumasa', 'Ilaya',
                'Kaltapa', 'Kanguha', 'Lemlunay', 'Libang',
                'Lilot', 'Lumbal', 'Lumbong', 'Luna',
                'Malabod', 'Malalag', 'Malandag', 'Maluay',
                'Milalag', 'Nalia', 'Palkan', 'Pamplona',
                'Poblacion', 'Polopon', 'Puangyao', 'Rizal',
                'Sabang', 'Safi', 'Salaman', 'Salngle',
                'San Carlos', 'San Francisco', 'San Isidro',
                'San Miguel', 'San Roque', 'San Vicente',
                'Santa Maria', 'Santo Niño', 'Sapu Masla',
                'Sapu Padidu', 'Tagaytay', 'Taluya',
                'Tango', 'Tapon', 'Tuburan', 'Tuyan',
                'Union',
            ],
            'Maasim': [
                'Amsipit', 'Bales', 'Colon', 'Daliao',
                'Datal-udas', 'Dimaluag', 'Ganatan', 'Greenleaf',
                'Kabatan', 'Kalaneg', 'Kamatis', 'Kawayan',
                'Liberty', 'Lilot', 'Lun Masla', 'Lun Padidu',
                'Mangale', 'New Canaan', 'Padiay', 'Paraiso',
                'Poblacion', 'Rizal', 'Saguiming', 'San Isidro',
                'San Juan', 'San Roque', 'Taluya', 'Tapon',
                'Tibudan', 'Tingled', 'Villa Kalachuchi',
            ],
            'Malapatan': [
                'Bulan', 'Carpenter', 'Crossing', 'Datalbong',
                'Duenas', 'Gumasa', 'Kaltapa', 'Lacsap-anan',
                'Layag', 'Liberation', 'Lumbayao', 'Malapatan',
                'Mangui', 'Moro', 'Nomios', 'Pag-asa',
                'Poblacion', 'San Jose', 'San Roque', 'Sapu Masla',
                'Tinoto',
            ],
            'Malungon': [
                'Baking', 'Balkan', 'Biangan', 'Buayan',
                'Bulol', 'Datalawam', 'Datalbong', 'Duran',
                'Kalaneg', 'Kib-agay', 'Kibala', 'Kiblat',
                'Kipyab', 'Lambayong', 'Langa-an', 'Lanuro',
                'Lapu-lapu', 'Liberty', 'Liliongan', 'Lumabat',
                'Maga', 'Malabod', 'Malandag', 'Malungon',
                'Malungon Gamay', 'Nabalawag', 'New Canaan',
                'Pangyan', 'Poblacion', 'Rizal', 'Salbuyan',
                'San Isidro', 'San Roque', 'Santa Maria',
                'Santo Niño', 'Saravia', 'Tacon', 'Talagas',
                'Tamban', 'Tuan-tuan', 'Tuburan', 'Union',
            ],
        }

        created_municipalities = 0
        created_barangays = 0

        for muni_name, barangays in data.items():
            muni, created = Municipality.objects.get_or_create(name=muni_name)
            if created:
                created_municipalities += 1
                self.stdout.write(self.style.SUCCESS(f'  Created municipality: {muni_name}'))

            for b_name in barangays:
                _, created = Barangay.objects.get_or_create(
                    name=b_name,
                    municipality=muni,
                )
                if created:
                    created_barangays += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created {created_municipalities} municipalities and {created_barangays} barangays.'
        ))
