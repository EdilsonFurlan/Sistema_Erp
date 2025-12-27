import json
import math
import os
from django.core.management.base import BaseCommand
from encaixe.models import Molde, MoldePeca

class Command(BaseCommand):
    help = 'Imports a mold JSON into the database'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON mold file')
        parser.add_argument('name', type=str, help='Name for the new Mold')

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        mold_name = options['name']

        if not os.path.exists(json_file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {json_file_path}'))
            return

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 1. Create Molde
        molde, created = Molde.objects.get_or_create(nome=mold_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Molde: {mold_name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Molde {mold_name} already exists. Updating pieces...'))

        # 2. Create Pieces
        pieces = data.get('pieces', [])
        
        for piece in pieces:
            # Calculate Area
            geom = piece.get('geom', {})
            geom_type = geom.get('type')
            area_mm2 = 0.0

            if geom_type == 'poly':
                pts = geom.get('pts', [])
                n = len(pts)
                if n > 2:
                    sum1 = 0
                    sum2 = 0
                    for i in range(n - 1):
                        sum1 += pts[i]['x'] * pts[i+1]['y']
                        sum2 += pts[i]['y'] * pts[i+1]['x']
                    sum1 += pts[n-1]['x'] * pts[0]['y']
                    sum2 += pts[n-1]['y'] * pts[0]['x']
                    area_mm2 = 0.5 * abs(sum1 - sum2)
            
            elif geom_type == 'rect':
                w = geom.get('halfW', 0) * 2
                h = geom.get('halfH', 0) * 2
                area_mm2 = w * h
            
            elif geom_type == 'circle':
                radius = geom.get('radius', 0)
                area_mm2 = math.pi * (radius ** 2)
            
            MoldePeca.objects.update_or_create(
                molde=molde,
                nome_original=piece.get('name', 'Sem Nome'),
                defaults={
                    'tipo_geom': geom_type,
                    'area_base_mm2': area_mm2,
                    'qtd_padrao': piece.get('qty', 1),
                    'geometria_json': geom
                }
            )
            self.stdout.write(f"Imported piece: {piece.get('name')}")
        
        self.stdout.write(self.style.SUCCESS('Import complete!'))
