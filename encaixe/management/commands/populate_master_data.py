from django.core.management.base import BaseCommand
from inventory.models import Material, Cor

class Command(BaseCommand):
    help = 'Populates the database with initial Fabrics and Colors'

    def handle(self, *args, **options):
        # Colors
        colors = [
            {'nome': 'Vermelho', 'hex': '#e74c3c'},
            {'nome': 'Azul', 'hex': '#3498db'},
            {'nome': 'Verde', 'hex': '#2ecc71'},
            {'nome': 'Preto', 'hex': '#2c3e50'},
            {'nome': 'Branco', 'hex': '#ffffff'},
            {'nome': 'Cinza', 'hex': '#95a5a6'},
        ]
        
        for c in colors:
            Cor.objects.get_or_create(nome=c['nome'], defaults={'hex_code': c['hex']})
            self.stdout.write(f"Color ready: {c['nome']}")

        # Fabrics (Now Materials with eh_tecido=True)
        fabrics = [
            {'nome': 'Nylon 600', 'largura': 1500, 'custo': 15.00},
            {'nome': 'Lona', 'largura': 1400, 'custo': 22.50},
            {'nome': 'Tactel', 'largura': 1600, 'custo': 8.90},
        ]

        for f in fabrics:
            Material.objects.get_or_create(
                nome=f['nome'], 
                defaults={
                    'eh_tecido': True,
                    'unidade': 'MT',
                    'largura_padrao_mm': f['largura'], 
                    'preco_custo': f['custo']
                }
            )
            self.stdout.write(f"Fabric (Material) ready: {f['nome']}")

        self.stdout.write(self.style.SUCCESS('Master data populated successfully!'))
