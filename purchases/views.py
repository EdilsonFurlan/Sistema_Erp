from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from purchases.models import OrdemCompra, OrdemCompraItem
from sales.models import Pedido
from inventory.models import EstoqueMaterial
from sales.services.material_calculator import get_material_requirements_for_orders

def purchase_planning(request):
    """
    Dashboard to view pending orders and select them for purchase.
    """
    orders = Pedido.objects.all().order_by('-data')
        
    return render(request, 'purchases/purchase_planning.html', {'orders': orders})

def visualize_purchase_creation(request):
    """
    Preview material requirements for SELECTED orders before creating PO.
    """
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_orders')
        if not selected_ids:
            messages.warning(request, "Nenhum pedido selecionado.")
            return redirect('purchase_planning')

        orders = Pedido.objects.filter(id__in=selected_ids)
        
        # 1. Aggregate Requirements
        requirements = get_material_requirements_for_orders(orders)
        
        # 2. Compare with Stock
        preview_list = []
        for (material, cor), data in requirements.items():
            qtd_needed = data['qtd']
            
            # Get Current Stock
            stock_entry = EstoqueMaterial.objects.filter(material=material, cor=cor).first()
            current_stock = stock_entry.quantidade if stock_entry else 0.0
            
            to_buy = max(0, qtd_needed - current_stock)
            
            preview_list.append({
                'material': material,
                'cor': cor,
                'qtd_needed': qtd_needed,
                'current_stock': current_stock,
                'to_buy': to_buy
            })
            
        preview_list.sort(key=lambda x: x['material'].nome)
        
        context = {
            'orders': orders,
            'preview_list': preview_list,
            'selected_ids_str': ",".join(selected_ids) # Pass forward
        }
        return render(request, 'purchases/purchase_creation.html', context)
        
    return redirect('purchase_planning')

def purchase_order_create(request):
    """
    Finalizes the creation of the Purchase Order.
    """
    if request.method == 'POST':
        selected_ids_str = request.POST.get('selected_ids')
        if not selected_ids_str:
            return redirect('purchase_planning')
            
        selected_ids = selected_ids_str.split(',')
        orders = Pedido.objects.filter(id__in=selected_ids)
        
        with transaction.atomic():
            # 1. Create Header
            oc = OrdemCompra.objects.create(status='aberta')
            oc.pedidos.set(orders)
            
            # 2. Calculate Again (Safety)
            requirements = get_material_requirements_for_orders(orders)
            
            # 3. Create Items
            for (material, cor), data in requirements.items():
                qtd_needed = data['qtd']
                
                stock_entry = EstoqueMaterial.objects.filter(material=material, cor=cor).first()
                current_stock = stock_entry.quantidade if stock_entry else 0.0
                to_buy = max(0, qtd_needed - current_stock)
                
                OrdemCompraItem.objects.create(
                    ordem_compra=oc,
                    material=material,
                    cor=cor,
                    quantidade_necessaria=qtd_needed,
                    quantidade_estoque_na_epoca=current_stock,
                    quantidade_comprar=to_buy
                )
        
        messages.success(request, f"Ordem de Compra #{oc.id} gerada com sucesso!")
        return redirect('purchase_order_detail', oc_id=oc.id)

    return redirect('purchase_planning')

def purchase_order_list(request):
    ocs = OrdemCompra.objects.all().order_by('-data_criacao')
    return render(request, 'purchases/purchase_order_list.html', {'ocs': ocs})

def purchase_order_detail(request, oc_id):
    oc = get_object_or_404(OrdemCompra, id=oc_id)
    return render(request, 'purchases/purchase_order_detail.html', {'oc': oc})

def purchase_order_delete(request, oc_id):
    oc = get_object_or_404(OrdemCompra, id=oc_id)
    if request.method == 'POST':
        oc.delete()
        messages.success(request, f"Ordem de Compra #{oc_id} excluída com sucesso.")
        return redirect('purchase_order_list')
    return redirect('purchase_order_detail', oc_id=oc_id)

def purchase_order_recalculate(request, oc_id):
    """
    Recalculates an existing Purchase Order based on current stock and order configurations.
    Useful if stock was updated after PO generation.
    """
    oc = get_object_or_404(OrdemCompra, id=oc_id)
    
    if request.method == 'POST':
        with transaction.atomic():
            # 1. Clear existing items
            oc.itens.all().delete()
            
            # 2. Re-calculate requirements
            requirements = get_material_requirements_for_orders(oc.pedidos.all())
            
            # 3. Create items with fresh stock data
            for (material, cor), data in requirements.items():
                qtd_needed = data['qtd']
                
                stock_entry = EstoqueMaterial.objects.filter(material=material, cor=cor).first()
                current_stock = stock_entry.quantidade if stock_entry else 0.0
                to_buy = max(0, qtd_needed - current_stock)
                
                OrdemCompraItem.objects.create(
                    ordem_compra=oc,
                    material=material,
                    cor=cor,
                    quantidade_necessaria=qtd_needed,
                    quantidade_estoque_na_epoca=current_stock,
                    quantidade_comprar=to_buy
                )
        
        messages.success(request, f"Ordem de Compra #{oc_id} recalculada com sucesso!")
            
    return redirect('purchase_order_detail', oc_id=oc_id)
