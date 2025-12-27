import os
import django
import sys
from collections import namedtuple

# Setup Django
sys.path.append('f:/Projetos/Teste encaixe')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Produto, ProdutoInsumoCor
from inventory.models import Material, Cor
from molds.models import MoldeMaterial, Molde
from sales.services.material_calculator import get_material_requirements_for_orders

def reproduce():
    print("--- Reproduction Test ---")
    
    # 1. Setup Data
    # Material: Ziper (Unit: MT or UN?) Let's assume MT for the bug scenario.
    mat, _ = Material.objects.get_or_create(nome="Ziper Teste Debug", defaults={'unidade': 'MT', 'preco_custo': 1.0})
    cor, _ = Cor.objects.get_or_create(nome="Preto")
    
    # Molde & MoldeMaterial
    molde = Molde.objects.first()
    if not molde: 
        print("No Molde found.")
        return

    # User says: 800 mm (but stored as 0.8 meters in DB)
    mm, _ = MoldeMaterial.objects.get_or_create(
        molde=molde, 
        material=mat, 
        defaults={'quantidade': 0.8, 'tipo': 'insumo'}
    )
    mm.quantidade = 0.8 # Explicitly set to 0.8 meters
    mm.save()
    
    # Product
    p = Produto.objects.create(nome="Produto Debug Calc", molde=molde, preco_base=10)
    
    # Link Product to Insumo
    ProdutoInsumoCor.objects.create(produto=p, molde_material=mm, cor=cor)
    
    # 2. Mock Order with 100 units
    MockItem = namedtuple('MockItem', ['produto', 'quantidade', 'configuracoes'])
    MockOrder = namedtuple('MockOrder', ['itens'])
    
    class MockConfigManager:
        def all(self): return []
    
    # QUANTITY = 100
    item = MockItem(produto=p, quantidade=100, configuracoes=MockConfigManager())
    
    class MockItemManager:
        def all(self): return [item]
        
    order = MockOrder(itens=MockItemManager())
    
    # 3. Calculate
    orders = [order]
    report = get_material_requirements_for_orders(orders)
    
    # 4. Check Result
    key = (mat, cor)
    if key in report:
        qtd_total = report[key]['qtd']
        print(f"Material: {mat.nome}")
        print(f"Molde Qty (Unit): {mm.quantidade}")
        print(f"Order Qty: {item.quantidade}")
        print(f"Calculated Total (MM): {qtd_total}")
        
        # Expected: 0.8 * 1000 (to mm) * 100 = 80,000
        if abs(qtd_total - 80000) < 0.1:
            print("SUCCESS: Calculation is 80,000 MM (Correctly normalized).")
        else:
             print(f"FAIL: Unexpected value {qtd_total}")
             
    else:
        print("FAIL: Material not found in report.")

    # Cleanup
    p.delete()
    # mm.delete() # Keep depending on if we reused
    
if __name__ == '__main__':
    reproduce()
