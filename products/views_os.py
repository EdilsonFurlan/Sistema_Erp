from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Produto, OrdemServicoTecnica, OrdemServicoItem
from sales.models import PedidoItem

def engineering_dashboard(request):
    """
    Dashboard para engenharia visualizar itens pendentes de cadastro tecnico.
    """
    # Itens que precisam de definicao tecnica
    pending_items = PedidoItem.objects.filter(status='PENDENTE_CADASTRO').select_related('pedido', 'molde', 'produto')
    
    # OS em aberto
    open_os = OrdemServicoTecnica.objects.filter(status='ABERTA')

    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_items')
        if selected_ids:
            # Criar nova OS
            os = OrdemServicoTecnica.objects.create(responsavel=request.user if request.user.is_authenticated else None)
            
            for item_id in selected_ids:
                pedido_item = PedidoItem.objects.get(id=item_id)
                OrdemServicoItem.objects.create(os=os, pedido_item=pedido_item)
            
            messages.success(request, f"OS #{os.id} criada com sucesso com {len(selected_ids)} itens.")
            return redirect('os_detail', os_id=os.id)
        else:
            messages.warning(request, "Selecione pelo menos um item para criar OS.")

    return render(request, 'products/engineering_dashboard.html', {
        'pending_items': pending_items,
        'open_os': open_os
    })

def os_detail(request, os_id):
    os = get_object_or_404(OrdemServicoTecnica, id=os_id)
    all_products = Produto.objects.filter(parent__isnull=False).select_related('parent', 'cor')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'resolve_existing':
            produto_id = request.POST.get('produto_id')
            if produto_id:
                produto = Produto.objects.get(id=produto_id)
                
                # Update OS
                os.produto_resultante = produto
                os.status = 'CONCLUIDA'
                os.save()
                
                # Update Items
                for os_item in os.itens.all():
                    pi = os_item.pedido_item
                    pi.produto = produto # Vincula o produto final
                    pi.molde = produto.parent.molde # Update Molde as well
                    pi.status = 'LIBERADO_PRODUCAO'
                    pi.save()
                    
                messages.success(request, f"OS #{os.id} resolvida! Itens liberados para producao.")
                return redirect('engineering_dashboard')

    return render(request, 'products/os_detail.html', {
        'os': os,
        'products': all_products
    })
