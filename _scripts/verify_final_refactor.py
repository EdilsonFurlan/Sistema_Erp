import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from molds.models import Molde, MoldeDetalhe
from products.models import ProdutoReferencia, ItensMaterial, ProdutoCor
from inventory.models import Material, Cor
from sales.models import Pedido, PedidoItem
from sales.services.material_calculator import get_material_requirements_for_orders
from clients.models import Cliente

def clean_db():
    Pedido.objects.all().delete()
    ProdutoReferencia.objects.all().delete()
    # Molde.objects.all().delete() # Preserve others if needed, but for clean test better delete
    # Material/Cor too
    
    # Safe cleanup (avoid protected errors)
    try:
        Pedido.objects.all().delete()
        ProdutoCor.objects.all().delete()
        ItensMaterial.objects.all().delete()
        ProdutoReferencia.objects.all().delete()
        Molde.objects.all().delete()
        Material.objects.all().delete()
        Cor.objects.all().delete()
        Cliente.objects.all().delete()
    except Exception as e:
        print(f"Cleanup warning: {e}")

def verify():
    # clean_db() # Disabled to avoid wiping everything if user has data. Use unique names instead?
    # Test env, okay to assume I can create/delete MY test data.
    
    # 1. Setup
    m_zipper = Material.objects.create(nome="Zipper Test YKK", preco_custo=2.0, unidade="un", eh_tecido=False)
    c_blue = Cor.objects.create(nome="Azul Test", hex_code="#0000FF")
    client, _ = Cliente.objects.get_or_create(nome="Test Client")
    
    # 2. Molde
    molde = Molde.objects.create(nome="Molde Test Mochila")
    MoldeDetalhe.objects.create(
        molde=molde, nome_original="Frente", tipo_geom="rect",
        area_base_mm2=100000.0, qtd_padrao=1,
        geometria_json={'type': 'rect'}
    )
    
    # 3. ProdutoReferencia
    prod_ref = ProdutoReferencia.objects.create(nome="Mochila Escolar Test", molde=molde, preco_base=100.0)
    
    # BOM: 2 Zippers
    ItensMaterial.objects.create(produto_referencia=prod_ref, material=m_zipper, quantidade=2, tipo='insumo')
    
    # 4. SKU
    sku_blue = ProdutoCor.objects.create(produto_referencia=prod_ref, cor=c_blue, sku="TEST-AZUL")
    
    # 5. Order
    pedido = Pedido.objects.create(cliente="Test", cliente_cadastro=client)
    item = PedidoItem.objects.create(pedido=pedido, molde=molde, produto=sku_blue, quantidade=10)
    
    print(f"Created Order Item: {item} (Qty: 10, SKU: {sku_blue})")
    
    # 6. Verify Calculator
    report = get_material_requirements_for_orders([pedido])
    
    zipper_key = (m_zipper, c_blue)
    
    if zipper_key in report:
        qty = report[zipper_key]['qtd']
        print(f"Calculator Result for Zipper: {qty}")
        if qty == 20.0:
            print("SUCCESS: Insumo calculation verified (10 * 2 = 20).")
        else:
            print(f"FAILURE: Expected 20.0, got {qty}")
    else:
        print("FAILURE: Zipper not found in report.")
        # Debug report keys
        for k in report.keys():
            print(f" - Key: {k[0].nome}, {k[1].nome}")

    # Cleanup (Optional)
    item.delete()
    pedido.delete()
    sku_blue.delete()
    prod_ref.delete()
    molde.delete()
    m_zipper.delete()
    c_blue.delete()

if __name__ == '__main__':
    verify()
