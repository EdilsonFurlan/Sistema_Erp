import os
import django
import sys

# Setup Django
sys.path.append('f:/Projetos/Teste encaixe')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from sales.models import Pedido
from encaixe.services.material_calculator import get_material_requirements_for_orders

def debug_order():
    # Order 8 was found in previous step having the Ziper
    try:
        order = Pedido.objects.get(id=8)
    except Pedido.DoesNotExist:
        print("Order 8 not found (maybe DB changed?). Checking last order...")
        order = Pedido.objects.last()
        
    print(f"Debugging Order: {order}")
    
    # Run Calculator
    get_material_requirements_for_orders([order])
    print("Calculation finished. Check debug_calc_log.txt")

if __name__ == '__main__':
    debug_order()
