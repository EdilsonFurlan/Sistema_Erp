import os
import django
import sys

# Setup Django
sys.path.append('f:/Projetos/Teste encaixe')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ProdutoReferencia, ItensMaterial
from molds.models import MoldeMaterial

def migrate_data():
    print("--- Starting Data Migration (MoldeMaterial -> ItensMaterial) ---")
    
    produtos = ProdutoReferencia.objects.all()
    print(f"Found {produtos.count()} Products to process.")
    
    count_created = 0
    
    for p in produtos:
        molde = p.molde
        materiais_molde = MoldeMaterial.objects.filter(molde=molde)
        
        print(f"Processing Product: {p.nome} (Molde: {molde.nome}) - Found {materiais_molde.count()} items.")
        
        for mm in materiais_molde:
            # Create corresponding ItensMaterial
            # Check duplicates?
            exists = ItensMaterial.objects.filter(
                produto_referencia=p,
                material=mm.material
            ).exists()
            
            if not exists:
                ItensMaterial.objects.create(
                    produto_referencia=p,
                    material=mm.material,
                    quantidade=mm.quantidade,
                    tipo=mm.tipo
                )
                count_created += 1
            else:
                 print(f"  Skipping existing Item: {mm.material.nome}")

    print(f"Migration Completed. Created {count_created} new ItensMaterial entries.")

if __name__ == '__main__':
    migrate_data()
