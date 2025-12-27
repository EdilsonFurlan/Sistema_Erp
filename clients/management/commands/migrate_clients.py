from django.core.management.base import BaseCommand
from sales.models import Pedido
from clients.models import Cliente

class Command(BaseCommand):
    help = 'Migrates client names from Pedido strings to Cliente objects'

    def handle(self, *args, **options):
        pedidos = Pedido.objects.filter(cliente_cadastro__isnull=True)
        count = 0
        created_count = 0
        
        for p in pedidos:
            nome_cliente = p.cliente.strip()
            if not nome_cliente:
                continue

            cliente_obj, created = Cliente.objects.get_or_create(nome=nome_cliente)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created Client: {nome_cliente}'))
            
            p.cliente_cadastro = cliente_obj
            p.save()
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} orders.'))
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new clients.'))
