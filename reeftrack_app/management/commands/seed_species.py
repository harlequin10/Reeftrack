from django.core.management.base import BaseCommand
from reeftrack_app.models import Species


class Command(BaseCommand):
    help = 'Seed coral species from the CPCe reference data'

    def handle(self, *args, **options):
        species_data = [
            ('ACROPORA BRANCHING (ACB)', 'ACROPORIDAE'),
            ('ACROPORA DIGITATE (ACD)', 'ACROPORIDAE'),
            ('ACROPORA PLATE (ACT)', 'ACROPORIDAE'),
            ('MONTIPORA BRANCHING (MONTB)', 'ACROPORIDAE'),
            ('MONTIPORA FOLIOSE (MONTF)', 'ACROPORIDAE'),
            ('NEW MONTIPORA ENCRUSTING (MONTE)', 'ACROPORIDAE'),
            ('COELOSERIS (COE)', 'AGARICIIDAE'),
            ('PACHYSERIS FOLIOSE (PACF)', 'AGARICIIDAE'),
            ('NEW LEPTOSERIS (LEPT)', 'AGARICIIDAE'),
            ('EUPHYLLIA (EUP)', 'EUPHYLLIDAE'),
            ('ECHINOPORA (ECHI)', 'FAVIIDAE'),
            ('FAVITES (FVI)', 'FAVIIDAE'),
            ('GONIASTREA (GONIA)', 'FAVIIDAE'),
            ('PLATYGYRA (PLAT)', 'FAVIIDAE'),
            ('MONTASTREA (MON)', 'FAVIIDAE'),
            ('OULOPHYLLIA (OULO)', 'FAVIIDAE'),
            ('FUNGIA (CMR)', 'FUNGIIDAE'),
            ('OTHER FREE LIVING FUNGIIDS (FOT)', 'FUNGIIDAE'),
            ('LOBOPHYLLIA (LOB)', 'MUSSIDAE'),
            ('SYMPHYLLIA (SYM)', 'MUSSIDAE'),
            ('HELIOPORA (HEL)', 'NON-SCLERACTINIAN CORALS'),
            ('GALAXEA (GAL)', 'OCULINIDAE'),
            ('POCILLOPORA (POC)', 'POCILLOPORIDAE'),
            ('SERIATOPORA (SER)', 'POCILLOPORIDAE'),
            ('GONIOPORA (GONIO)', 'PORITIDAE'),
            ('PORITES BRANCHING (PORB)', 'PORITIDAE'),
            ('PORITES MASSIVE (PORM)', 'PORITIDAE'),
            ('COSCINAREA (COS)', 'SIDERASTREIDAE'),
            ('OTHER ENCRUSTING CORALS (CE)', 'OTHER CORALS WITH NO SPECIFIC GENUS'),
            ('OTHER MASSIVE CORALS (CM)', 'OTHER CORALS WITH NO SPECIFIC GENUS'),
            ('NEW OTHER SUBMASSIVE CORALS (CSM)', 'OTHER CORALS WITH NO SPECIFIC GENUS'),
        ]

        created = 0
        for sub_cat, major_cat in species_data:
            _, was_created = Species.objects.get_or_create(
                sub_category=sub_cat,
                major_category=major_cat,
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done! Created {created} species. ({len(species_data)} total reference species).'
        ))
