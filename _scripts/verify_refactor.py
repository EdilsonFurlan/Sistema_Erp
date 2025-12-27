
import os
import django
import sys

# Setup Django
sys.path.append(r'f:\Projetos\Teste encaixe')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from molds.models import Molde, MoldePeca, MoldeMaterial
from products.models import Produto, ProdutoPecaCor, ProdutoInsumoCor, ProdutoConsumo
from inventory.models import Material, Cor
from sales.models import Pedido, PedidoItem
from django.utils import timezone

def verify():
    print("--- Starting Verification ---")
    
    # 1. Create Molde
    molde, created = Molde.objects.get_or_create(nome="Molde Test Refactor")
    print(f"Molde: {molde}")

    # Create Materials
    mat_nylon, _ = Material.objects.get_or_create(nome="Nylon 600", defaults={'largura_padrao_mm': 1500, 'preco_custo': 10.0, 'eh_tecido': True})
    mat_ziper, _ = Material.objects.get_or_create(nome="Ziper #5", defaults={'largura_padrao_mm': 30, 'preco_custo': 2.0, 'eh_tecido': False, 'tem_cor': True})
    cor_azul, _ = Cor.objects.get_or_create(nome="Azul Royal")
    cor_preto, _ = Cor.objects.get_or_create(nome="Preto")

    # Create Molde Components
    mp, _ = MoldePeca.objects.get_or_create(molde=molde, nome_original="Frente", defaults={'material_padrao': mat_nylon, 'area_base_mm2': 100000, 'geometria_json': {'type': 'rect', 'halfW': 100, 'halfH': 100}})
    mm, _ = MoldeMaterial.objects.get_or_create(molde=molde, material=mat_ziper, defaults={'quantidade': 0.5, 'tipo': 'insumo'})

    # 2. Create Product (Direct Link)
    produto, created = Produto.objects.get_or_create(nome="Mochila Azul Teste", molde=molde)
    print(f"Produto: {produto} (Linked to {produto.molde})")

    # 3. Configure Colors & Overrides
    # Piece -> Blue (Default Material)
    ppc, _ = ProdutoPecaCor.objects.update_or_create(
        produto=produto,
        molde_peca=mp,
        defaults={'cor': cor_azul}
    )
    print(f"Configured Piece Color: {ppc}")

    # Insumo -> Black (Override Material to Nylon just to test logic - unrealistic but valid for code check)
    # Actually let's create a new material "Ziper #8" to override "Ziper #5"
    mat_ziper8, _ = Material.objects.get_or_create(nome="Ziper #8", defaults={'largura_padrao_mm': 40, 'preco_custo': 3.0, 'eh_tecido': False, 'tem_cor': True})

    pic, _ = ProdutoInsumoCor.objects.update_or_create(
        produto=produto,
        molde_material=mm,
        defaults={'cor': cor_preto, 'material': mat_ziper8}
    )
    print(f"Configured Insumo Color with Override: {pic} (Should use {mat_ziper8.nome})")

    # 4. Calculate Consumption (Costing)
    from products.views import _calculate_consumption
    _calculate_consumption(produto)
    consumos = ProdutoConsumo.objects.filter(produto=produto)
    print(f"Calculated Consumptions: {consumos.count()}")
    for c in consumos:
        print(f" - {c.material.nome} ({c.cor}): {c.consumo_total}")

    # 5. Create Order
    pedido = Pedido.objects.create(cliente="Cliente Teste")
    item = PedidoItem.objects.create(
        pedido=pedido,
        molde=molde,
        produto=produto, # The key refactor change
        quantidade=10
    )
    print(f"Order Item Created: {item} with Product {item.produto}")

    # 6. Verify Sales Material Calculator (The refactored service)
    from sales.services.material_calculator import get_material_requirements_for_orders
    report = get_material_requirements_for_orders([pedido])
    print("Material Requirements Report:")
    for key, data in report.items():
        mat, cor = key
        print(f" - {mat.nome} ({cor}): {data['qtd']}")
    
    # Check if Nylon (Blue) and Ziper (Black) are present
    # Nylon comes from Config (which comes from Product Defaults if not overridden)
    # Wait, create_order usually populates PedidoConfig from Product.
    # But here I created Item manually.
    # Usually Sales View does:
    # product_rules = ...
    # for piece in pieces: create PedidoConfig...
    
    # Testing Manual Item Config population logic mimics sales view:
    print("Populating PedidoConfig from Product...")
    from sales.models import PedidoConfig
    
    product_rules = {
        rule.molde_peca_id: rule.cor
        for rule in ProdutoPecaCor.objects.filter(produto=produto)
    }
    
    count_conf = 0
    for peca in MoldePeca.objects.filter(molde=molde):
        cor_default = product_rules.get(peca.id)
        if cor_default:
            PedidoConfig.objects.create(
                pedido_item=item,
                molde_peca=peca,
                material=peca.material_padrao,
                cor=cor_default
            )
            count_conf += 1
            
    print(f"Created {count_conf} Configs.")

    # Re-run calculator
    report = get_material_requirements_for_orders([pedido])
    print("Material Requirements Report (After Config):")
    for key, data in report.items():
        mat, cor = key
        print(f" - {mat.nome} ({cor}): {data['qtd']}")

    print("--- Verification Complete ---")

if __name__ == "__main__":
    verify()
