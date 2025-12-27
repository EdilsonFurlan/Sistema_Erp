from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import OrdemProducao, OrdemProducaoItem
from sales.models import PedidoItem
from products.models import Produto
from django.db.models import Sum
from django.utils import timezone
from .models import OrdemProducao, OrdemProducaoItem, Maquina, RegistroProducao
from .forms import MaquinaForm

def production_dashboard(request):
    """
    PCP Dashboard:
    - Lista itens 'LIBERADO_PRODUCAO' que ainda nao tem OP.
    - Agrupa por SKU para facilitar geracao de OP.
    """
    # Get items ready for production but not linked to any OP
    # Note: related_name='producoes' implies ManyToMany or ReverseFK logic.
    # PedidoItem -> OrdemProducaoItem -> OrdemProducao
    # We want items where 'producoes' is empty.
    
    ready_items = PedidoItem.objects.filter(
        status='LIBERADO_PRODUCAO',
        producoes__isnull=True
    ).select_related('produto', 'produto__parent', 'pedido')
    
    # Custom grouping in Python (simple for now)
    grouped_items = {} 
    
    for item in ready_items:
        if not item.produto:
            continue # Should not happen if status is LIBERADO
            
        sku_id = item.produto.id
        if sku_id not in grouped_items:
            grouped_items[sku_id] = {
                'product': item.produto,
                'items': [],
                'total_qty': 0
            }
        grouped_items[sku_id]['items'].append(item)
        grouped_items[sku_id]['total_qty'] += item.quantidade

    return render(request, 'production/dashboard.html', {
        'grouped_items': grouped_items
    })

def create_op(request, sku_id):
    """
    Action to create OP for a specific SKU grouping.
    """
    if request.method == 'POST':
        product = get_object_or_404(Produto, id=sku_id)
        
        # Re-fetch items to be safe
        ready_items = PedidoItem.objects.filter(
            status='LIBERADO_PRODUCAO',
            producoes__isnull=True,
            produto=product
        )
        
        if not ready_items.exists():
            messages.warning(request, "Nenhum item pendente para este produto.")
            return redirect('production_dashboard')
            
        # Create OP
        total_qty = sum(item.quantidade for item in ready_items)
        op = OrdemProducao.objects.create(
            produto=product,
            quantidade_total=total_qty,
            status='PLANEJADA'
        )
        
        # Link items
        for item in ready_items:
            OrdemProducaoItem.objects.create(
                op=op, 
                pedido_item=item,
                quantidade=item.quantidade
            )
            # Update status (optional if we want to differentiate 'In Queue' vs 'In OP')
            item.status = 'EM_PRODUCAO'
            item.save()
            
        messages.success(request, f"OP #{op.id} gerada com sucesso para {total_qty} pecas.")
        return redirect('op_list')
        
    return redirect('production_dashboard')

def op_list(request):
    ops = OrdemProducao.objects.all().order_by('-data_criacao')
    return render(request, 'production/op_list.html', {'ops': ops})

import json

def create_op_screen(request):
    """
    New OP creation screen with grouping and filtering.
    """
    view_mode = request.GET.get('view_mode', 'pedido') # 'pedido' or 'produto'
    status_filter = request.GET.get('status', 'PENDENTE')
    
    # Base queryset
    items = PedidoItem.objects.select_related('pedido', 'produto', 'molde', 'pedido__cliente_cadastro').prefetch_related('producoes__op')
    
    # Filtering (simplified)
    if status_filter:
        if status_filter == 'PENDENTE':
            items = items.filter(status__in=['PENDENTE_CADASTRO', 'LIBERADO_PRODUCAO'])
        else:
            items = items.filter(status=status_filter)
            
    # Grouping
    grouped_data = {}
    if view_mode == 'pedido':
        for item in items:
            key = item.pedido
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(item)
    else: # group by product/molde
        for item in items:
            key = item.produto if item.produto else item.molde
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(item)

    # Check for "same product in production" alert data
    products_in_production = {}
    in_prod_items = PedidoItem.objects.filter(status='EM_PRODUCAO').select_related('produto', 'molde').prefetch_related('producoes__op')
    for ip in in_prod_items:
        prod_key = str(ip.produto.id) if ip.produto else (f"m_{ip.molde.id}" if ip.molde else None)
        if prod_key:
            if prod_key not in products_in_production:
                op_id = "Desconhecida"
                op_item = ip.producoes.first()
                if op_item:
                    op_id = op_item.op.id
                
                products_in_production[prod_key] = {
                    'qty': 0,
                    'op_id': op_id
                }
            products_in_production[prod_key]['qty'] += ip.quantidade

    return render(request, 'production/production_order_create.html', {
        'grouped_data': grouped_data,
        'view_mode': view_mode,
        'status_filter': status_filter,
        'products_in_production_json': json.dumps(products_in_production)
    })

def create_op_bulk(request):
    """
    Process selected items to create one or more OPs.
    """
    if request.method == 'POST':
        item_ids = request.POST.getlist('items')
        if not item_ids:
            messages.error(request, "Nenhum item selecionado.")
            return redirect('create_op_screen')
            
        # Allow creating OP from both Pending and Tech-Released statuses
        selected_items = PedidoItem.objects.filter(
            id__in=item_ids, 
            status__in=['PENDENTE_CADASTRO', 'LIBERADO_PRODUCAO']
        )
        
        # Group by product to create OPs
        items_by_product = {}
        for item in selected_items:
            if not item.produto:
                continue
            if item.produto not in items_by_product:
                items_by_product[item.produto] = []
            items_by_product[item.produto].append(item)
            
        created_ops = []
        for product, p_items in items_by_product.items():
            total_qty = sum(i.quantidade for i in p_items)
            op = OrdemProducao.objects.create(
                produto=product,
                quantidade_total=total_qty,
                status='PLANEJADA'
            )
            for item in p_items:
                OrdemProducaoItem.objects.create(
                    op=op,
                    pedido_item=item,
                    quantidade=item.quantidade
                )
                item.status = 'EM_PRODUCAO'
                item.save()
            created_ops.append(op.id)
            
        if created_ops:
            messages.success(request, f"Ordens de Produção criadas: {', '.join(map(str, created_ops))}")
        else:
            messages.error(request, "Não foi possível criar as OPs (verifique se os produtos estão configurados).")
            
        return redirect('op_list')
        
    return redirect('create_op_screen')

def iot_dashboard(request):
    return render(request, 'production/iot_dashboard.html')

def iot_dashboard_status(request):
    ops = OrdemProducao.objects.filter(status='EM_PRODUCAO').prefetch_related('maquinas_alocadas', 'registros_tempo')
    
    dashboard_data = []
    
    for op in ops:
        maquinas_data = []
        op_total_seconds = 0
        
        # Máquinas alocadas à OP (via admin ou lógica de vinculo)
        target_maquinas = op.maquinas.all() 
        
        for maq in target_maquinas:
            # Tempo histórico (finalizado)
            hist_qs = RegistroProducao.objects.filter(op=op, maquina=maq, finalizado=True).aggregate(sum_seg=Sum('duracao_segundos'))
            hist = hist_qs['sum_seg'] or 0
            
            # Tempo corrente (se estiver rodando agora)
            current = 0
            if maq.status_atual == 'LIGADO' and maq.op_atual == op:
                last_reg = maq.registros.filter(op=op, finalizado=False).last()
                if last_reg and last_reg.inicio:
                    current = (timezone.now() - last_reg.inicio).total_seconds()
            
            total = hist + current
            op_total_seconds += total
            
            maquinas_data.append({
                'obj': maq,
                'total_seconds': total,
                'is_active': (maq.status_atual == 'LIGADO' and maq.op_atual == op)
            })
            
        dashboard_data.append({
            'op': op,
            'maquinas': maquinas_data,
            'total_prod_seconds': op_total_seconds
        })
        
    return render(request, 'production/partials/iot_status.html', {'dashboard_data': dashboard_data})

def op_change_status(request, pk, status):
    op = get_object_or_404(OrdemProducao, pk=pk)
    # Safe validation can be added here
    op.status = status
    op.save()
    op.save()
    messages.success(request, f"OP #{op.id} atualizada para {status}.")
    return redirect('op_list')

def op_allocation(request, pk):
    op = get_object_or_404(OrdemProducao, pk=pk)
    
    if request.method == 'POST':
        selected_ids = request.POST.getlist('maquinas')
        
        # Update M2M
        op.maquinas.set(selected_ids)
        
        # Update Machine ownership (One OP at a time logic)
        # Validar se queremos "roubar" a máquina de outra OP ou avisar. 
        # Aqui vamos forçar a alocação (roubar).
        
        # 1. Libera máquinas que não estão mais na lista mas estavam nesta OP
        Maquina.objects.filter(op_atual=op).exclude(id__in=selected_ids).update(op_atual=None)
        
        # 2. Aloca as selecionadas para esta OP
        Maquina.objects.filter(id__in=selected_ids).update(op_atual=op)
        
        messages.success(request, f"Recursos alocados para OP #{op.id}.")
        return redirect('op_list')

    maquinas = Maquina.objects.all().order_by('nome')
    return render(request, 'production/op_allocation.html', {
        'op': op,
        'maquinas': maquinas
    })

def maquina_list(request):
    maquinas = Maquina.objects.all().order_by('nome')
    context = {
        'maquinas': maquinas,
        'total_maquinas': maquinas.count(),
        'maquinas_ligadas': maquinas.filter(status_atual='LIGADO').count()
    }
    return render(request, 'production/maquina_list.html', context)

def maquina_create(request):
    if request.method == 'POST':
        form = MaquinaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Máquina cadastrada com sucesso!")
            return redirect('maquina_list')
    else:
        form = MaquinaForm()
    return render(request, 'production/maquina_form.html', {'form': form})

def maquina_update(request, pk):
    maquina = get_object_or_404(Maquina, pk=pk)
    if request.method == 'POST':
        form = MaquinaForm(request.POST, instance=maquina)
        if form.is_valid():
            form.save()
            messages.success(request, "Máquina atualizada com sucesso!")
            return redirect('maquina_list')
    else:
        form = MaquinaForm(instance=maquina)
    return render(request, 'production/maquina_form.html', {'form': form})

def maquina_delete(request, pk):
    maquina = get_object_or_404(Maquina, pk=pk)
    # Check if machine has history or linked ops? Maybe prevent delete if critical.
    # For now, standard delete.
    maquina.delete()
    messages.success(request, "Máquina removida.")
    return redirect('maquina_list')
