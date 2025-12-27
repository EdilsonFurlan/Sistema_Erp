
import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from products.models import ProdutoCor, ProdutoReferencia, ProdutoCorItem

def check_latest_sku():
    try:
        # Get latest SKU
        sku = ProdutoCor.objects.last()
        if not sku:
            print("No SKUs found.")
            return

        print(f"Latest SKU: {sku.id} - {sku.sku} (Ref: {sku.produto_referencia.nome})")
        
        # Check Items
        items = sku.itens_cor.all()
        print(f"Total Cor Items found: {items.count()}")
        
        for item in items:
            print(f" - Material: {item.material.nome} (ID: {item.material.id}) -> Cor: {item.cor.nome}")
            
        # Verify Reference Materials
        print("\nReference Materials vs SKU Colors:")
        ref_items = sku.produto_referencia.itens_material.all()
        for ref_item in ref_items:
            # Check logic used in view
            match = items.filter(material=ref_item.material).first()
            status = f"MATCH: {match.cor.nome}" if match else "MISSING"
            print(f" - Ref Item: {ref_item.material.nome} (ID: {ref_item.material.id}) -> {status}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_latest_sku()
