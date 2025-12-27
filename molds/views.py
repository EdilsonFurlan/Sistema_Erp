from django.shortcuts import render, redirect
from .models import Molde
from products.forms import MoldeUploadForm # Reusing form dependent on Molde model? 
# Wait, MoldeUploadForm is in products/forms.py but imports Molde from molds.models. 
# I should probably move the form to molds/forms.py or keep it there if it's product-creation context.
# Let's keep specific Molde management here.

def molde_list(request):
    moldes = Molde.objects.all().order_by('-data_criacao')
    return render(request, 'molds/molde_list.html', {'moldes': moldes})

def molde_detail(request, molde_id):
    from django.shortcuts import get_object_or_404
    molde = get_object_or_404(Molde, id=molde_id)
    # Prefetch related data
    pecas = molde.detalhes.all()
    # materiais_ficha (BOM) removed from Molde. Now in Produto.
    
    context = {
        'molde': molde,
        'pecas': pecas,
    }
    return render(request, 'molds/molde_detail.html', context)

def molde_delete(request, molde_id):
    from django.contrib import messages
    from django.db.models import ProtectedError
    from django.shortcuts import get_object_or_404
    
    molde = get_object_or_404(Molde, id=molde_id)
    
    if request.method == 'POST':
        try:
            molde.delete()
            messages.success(request, f"Molde '{molde.nome}' excluído com sucesso.")
        except ProtectedError:
             messages.error(request, f"Não é possível excluir o Molde '{molde.nome}' pois ele está sendo usado por Produtos ou Pedidos.")
        except Exception as e:
            messages.error(request, f"Erro ao excluir molde: {e}")
            
    return redirect('molde_list')
