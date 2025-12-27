
import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from products.models import ProdutoCor, ProdutoCorItem

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
            item_mat_id = item.item_material.id if item.item_material else "None"
            mat_name = item.material.nome
            cor_name = item.cor.nome
            print(f" - [DB Record] Material: {mat_name} | ItemRefID: {item_mat_id} => Cor: {cor_name}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_latest_sku()
