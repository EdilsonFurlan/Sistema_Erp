import json
import math
from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Calculates fabric usage based on a mold JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, nargs='?', default='teste.json', help='Path to the JSON mold file')
        parser.add_argument('--quantity', type=int, default=60, help='Number of items to produce')

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        quantity = options['quantity']

        if not os.path.exists(json_file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {json_file_path}'))
            return

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        pieces = data.get('pieces', [])
        
        # Color Mapping (Hardcoded for this example based on user request)
        # In a real system, this would come from the database or another config file
        color_mapping = {
            "Corpo Frente Costa": "Vermelho",
            "Fundo": "Azul",
            "Emenda Corpo": "Vermelho", # Assuming same as body
            "Fole Corpo": "Vermelho",   # Assuming same as body
        }
        
        # Default color if not found
        default_color = "Indefinido"

        usage_by_color = {}

        self.stdout.write(f"Calculating usage for {quantity} items...")

        for piece in pieces:
            piece_id = piece.get('id')
            name = piece.get('name')
            qty_per_item = piece.get('qty', 1)
            geom = piece.get('geom', {})
            geom_type = geom.get('type')
            
            area_mm2 = 0.0

            if geom_type == 'poly':
                pts = geom.get('pts', [])
                # Shoelace formula for polygon area
                n = len(pts)
                if n > 2:
                    sum1 = 0
                    sum2 = 0
                    for i in range(n - 1):
                        sum1 += pts[i]['x'] * pts[i+1]['y']
                        sum2 += pts[i]['y'] * pts[i+1]['x']
                    # Add last point connection to first
                    sum1 += pts[n-1]['x'] * pts[0]['y']
                    sum2 += pts[n-1]['y'] * pts[0]['x']
                    area_mm2 = 0.5 * abs(sum1 - sum2)
            
            elif geom_type == 'rect':
                # Rect defined by halfW and halfH
                w = geom.get('halfW', 0) * 2
                h = geom.get('halfH', 0) * 2
                area_mm2 = w * h
            
            elif geom_type == 'circle':
                radius = geom.get('radius', 0)
                area_mm2 = math.pi * (radius ** 2)

            # Convert mm2 to m2 (1 m2 = 1,000,000 mm2)
            area_m2 = area_mm2 / 1_000_000.0
            
            total_piece_area = area_m2 * qty_per_item * quantity
            
            color = color_mapping.get(name, default_color)
            
            if color not in usage_by_color:
                usage_by_color[color] = 0.0
            
            usage_by_color[color] += total_piece_area

            # Detailed output for verification
            # self.stdout.write(f"Piece: {name} | Type: {geom_type} | Area/pc: {area_m2:.6f} m2 | Qty: {qty_per_item} | Total: {total_piece_area:.4f} m2 | Color: {color}")

        self.stdout.write("-" * 40)
        self.stdout.write("TOTAL FABRIC USAGE (Net Area):")
        self.stdout.write("-" * 40)
        
        for color, area in usage_by_color.items():
            # Add a safety margin estimate (e.g. 15% waste)
            # This is common in textile industry due to layout gaps
            waste_factor = 1.15 
            gross_area = area * waste_factor
            
            self.stdout.write(f"{color}: {area:.2f} m² (Net) -> approx {gross_area:.2f} m² (with 15% margin)")
            
            # Estimate linear meters for standard widths
            for width in [1.40, 1.50, 1.60]:
                linear_m = gross_area / width
                self.stdout.write(f"    Width {width}m: {linear_m:.2f} linear meters")
            self.stdout.write("")

