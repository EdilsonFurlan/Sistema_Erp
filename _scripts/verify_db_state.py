import os
import django
import sys

# Setup Django
sys.path.append('f:/Projetos/Teste encaixe')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from molds.models import MoldeMaterial
from sales.models import PedidoItem

def inspect_db():
    print("--- Inspecting DB ---")
    
    # Find MoldeMaterial for Ziper
    mms = MoldeMaterial.objects.filter(material__nome__icontains="ziper")
    print(f"Found {mms.count()} MoldeMaterials for 'ziper'.")
    
    for mm in mms:
        mat = mm.material
        print(f"\n[MoldeMaterial ID: {mm.id}]")
        print(f"  Molde: {mm.molde.nome}")
        print(f"  Material: {mat.nome} (ID: {mat.id})")
        print(f"  Material Unit: '{mat.unidade}'")
        print(f"  Is Measure Unit? {mat.is_unidade_medida()}")
        
        # Check if used in any orders
        # Find products using this Molde
        products_using = mm.molde.produto_set.all()
        for p in products_using:
            # Find Order Items for this Product
            items = PedidoItem.objects.filter(produto=p)
            for item in items:
                print(f"  -> Found in Order #{item.pedido.id} | Product: {p.nome} | ItemQty: {item.quantidade}")
                
                # Check Insumo Config
                # Usually insumos don't have per-item configuration unless overridden.
                # Just calculating for this item:
                val = mm.quantidade * item.quantidade
                print(f"     -> Calculated Need (mm): {val}")
                
                 # Display Logic Simulation
                if mat.is_unidade_medida():
                     disp = mat.get_valor_display(val)
                     print(f"     -> Display ({mat.unidade}): {disp}")

if __name__ == '__main__':
    inspect_db()
