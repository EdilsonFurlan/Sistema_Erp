from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from products.models import Produto, ItensMaterial, ProdutoConsumo, ProdutoInsumo
from molds.models import Molde, MoldeDetalhe
from inventory.models import Material, Cor
from products.forms import MoldeUploadForm
from encaixe.services.molde_importer import process_molde_json
import os

from decimal import Decimal

def product_list(request):
    from django.db.models import Count
    products = Produto.objects.all().order_by('nome')\
        .select_related('molde')\
        .prefetch_related('itens_material__material', 'insumos__material')\
        .annotate(sku_count_annotated=Count('variantes'))
    
    for p in products:
        cost = Decimal(0.0)
        # Prefetched material items
        for item in p.itens_material.all():
            price = item.material.preco_custo or Decimal(0.0)
            cost += price * Decimal(str(item.quantidade))
        # Prefetched insumos
        for item in p.insumos.all():
            price = item.material.preco_custo or Decimal(0.0)
            cost += price * Decimal(str(item.quantidade))
            
        p.custo_estimado = cost
        p.sku_count = p.sku_count_annotated

    stats = {
        'total': products.count(),
        'standard': products.filter(eh_padrao=True).count(),
        'active': products.count(), # Placeholder for now
        'color': products.filter(eh_padrao=False).count(),
    }

    moldes = Molde.objects.all().order_by('nome')
    
    context = {
        'products': products,
        'moldes': moldes,
        'stats': stats,
    }
    return render(request, 'products/product_list.html', context)

def product_create(request, molde_id):
    """
    NEW: Step-by-step creation logic. Doesn't create Produto in DB until Save is clicked.
    Pre-fills the screen based on 'Standard Reference' if it exists.
    """
    molde = get_object_or_404(Molde, id=molde_id)
    std_ref = Produto.objects.filter(molde=molde, eh_padrao=True).first()
    if not std_ref:
        std_ref = Produto.objects.filter(molde=molde).order_by('id').first()

    if request.method == 'POST':
        # CHANGELOG: Check for changes before creating
        has_changes = False
        
        # Check Item Materials (Pieces)
        for detalhe in molde.detalhes.all():
            new_mat_id = request.POST.get(f'material_{detalhe.id}')
            # Find in std_ref
            old_item = None
            if std_ref:
                for item in std_ref.itens_material.all():
                    if item.molde_detalhe_id == detalhe.id:
                        old_item = item
                        break
            
            old_mat_id = str(old_item.material.id) if old_item else None
            if new_mat_id != old_mat_id:
                has_changes = True
                break
        
        # Check Insumos (Simple list check as we don't allow add/remove in UI for New Ref)
        if not has_changes and std_ref:
             # Logic: Iterate posted insumos and compare with existing
             # In is_new mode, template renders existing insumos with name="new_insumo_material[]"
             posted_mats = request.POST.getlist('new_insumo_material[]')
             posted_qtys = request.POST.getlist('new_insumo_quantidade[]')
             
             # Std Insumos
             std_insumos = list(std_ref.insumos.all())
             
             if len(posted_mats) != len(std_insumos):
                 has_changes = True
             else:
                 # Compare individually (assuming order implies correspondence since UI is generated from list)
                 for i, std_item in enumerate(std_insumos):
                     p_mat = posted_mats[i]
                     p_qty = posted_qtys[i]
                     
                     if str(p_mat) != str(std_item.material.id):
                         has_changes = True; break
                     
                     # Float compare
                     try:
                         val_p = float(str(p_qty).replace(',', '.'))
                         val_std = float(std_item.quantidade)
                         if abs(val_p - val_std) > 0.001:
                             has_changes = True; break
                     except:
                         has_changes = True; break

        # If no std_ref exists, it is the first one, so it is a change (creation)
        if not std_ref:
            has_changes = True

        if not has_changes:
            messages.warning(request, "Nenhuma alteração detectada em relação à referência base. Nova referência não criada.")
            return redirect('integrated_view')

        # 1. Create the actual Reference object
        nome = request.POST.get('nome') or f"Nova Ref {molde.nome}"
        product = Produto.objects.create(
            nome=nome,
            molde=molde,
            preco=0.0
        )
        
        # 2. Process and Save Materials (Reuse logic from batch save)
        count = 0
        for detalhe in molde.detalhes.all():
            mat_id = request.POST.get(f'material_{detalhe.id}')
            qty_val = request.POST.get(f'quantidade_{detalhe.id}')
            if mat_id and qty_val:
                try:
                    qty = float(qty_val)
                    ItensMaterial.objects.create(
                        produto=product,
                        molde_detalhe=detalhe,
                        material_id=mat_id,
                        quantidade=qty,
                        tipo='tecido_padrao'
                    )
                    count += 1
                except ValueError: continue
        
        # 3. Process and Save Insumos
        new_mats = request.POST.getlist('new_insumo_material[]')
        new_qtys = request.POST.getlist('new_insumo_quantidade[]')
        
        # We process exactly what was passed. If UI disabled add/remove, this list matches original count.
        for m_id, q_val in zip(new_mats, new_qtys):
            if m_id and q_val:
                try:
                    qty = float(str(q_val).replace(',', '.'))
                    ProdutoInsumo.objects.create(
                        produto=product,
                        material_id=m_id,
                        quantidade=qty
                    )
                    count += 1
                except ValueError: continue

        messages.success(request, f"Referência '{product.nome}' criada com {count} itens.")
        return redirect('integrated_view')

    # RENDER PHASE (Wizard)
    detalhes = []
    saved_items_map = {}
    if std_ref:
        saved_items_map = {item.molde_detalhe.id: item for item in std_ref.itens_material.all() if item.molde_detalhe}

    for peca in molde.detalhes.all().order_by('nome_original'):
        saved_item = saved_items_map.get(peca.id)
        detalhes.append({
            'obj': peca,
            'width_mm': peca.largura_mm,
            'height_mm': peca.altura_mm,
            'saved_material_id': saved_item.material.id if saved_item else None,
            'saved_qty': saved_item.quantidade if saved_item else None,
        })

    context = {
        'product': {'nome': f"Ref {molde.nome} (Nova)", 'molde': molde}, # Mock object for template
        'is_new': True,
        'custo_total': 0.0,
        'detalhes': detalhes,
        'insumos_gerais': std_ref.insumos.all() if std_ref else [],
        'tecidos': Material.objects.filter(eh_tecido=True).order_by('nome'),
        'acessorios': Material.objects.filter(eh_tecido=False).order_by('nome'),
        'cores': Cor.objects.all().order_by('nome'),
    }
    return render(request, 'products/product_detail.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Produto, id=product_id)
    
    # Handle forms for adding Material / SKU (Simplified logic for now)
    # Prepare Molde Detalhes with Dimensions for Calculator
    detailed_items = product.itens_material.filter(molde_detalhe__isnull=False)
    saved_map = {item.molde_detalhe.id: item for item in detailed_items}

    detalhes = []
    for peca in product.molde.detalhes.all().order_by('nome_original'):
        geom = peca.geometria_json or {}
        # Simple extraction. Assuming importer stored bbox or calculating from pts.
        width = 0.0
        height = 0.0
        
        width = peca.largura_mm
        height = peca.altura_mm
        
        # Fallback if stored is 0 (old data not re-imported)
        if (width == 0 or height == 0):
             # ... calculation logic (kept as fallback or removed if user forced re-import) ...
             # Keeping simplified fallback for safety
            if 'w' in geom and 'h' in geom:
                width = geom['w']
                height = geom['h']
            elif 'halfW' in geom and 'halfH' in geom:
                 width = geom['halfW'] * 2
                 height = geom['halfH'] * 2
            
        saved_item = saved_map.get(peca.id)
        detalhes.append({
            'obj': peca,
            'width_mm': width,
            'height_mm': height,
            'saved_material_id': saved_item.material.id if saved_item else None,
            'saved_qty': saved_item.quantidade if saved_item else None,
            'saved_cor_id': saved_item.cor.id if saved_item and saved_item.cor else None
        })
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Always update name if present
        new_name = request.POST.get('nome')
        if new_name and new_name != product.nome:
            product.nome = new_name
            product.save()

        # Update Price if present (Commercial product)
        new_price = request.POST.get('preco')
        if new_price is not None:
            try:
                product.preco = Decimal(new_price.replace(',', '.'))
                product.save()
            except: pass
        
        if action == 'add_material':
            mat_id = request.POST.get('material')
            qty = float(request.POST.get('quantidade') or 0)
            tipo = request.POST.get('tipo')
            if mat_id:
                ItensMaterial.objects.create(
                    produto_referencia=product,
                    material_id=mat_id,
                    quantidade=qty,
                    tipo=tipo
                )
                messages.success(request, "Material adicionado.")

        elif action == 'save_consumption_batch':
            # 1. Update Fabrics (MoldeDetalhe linked)
            detalhes = product.molde.detalhes.all()
            count = 0
            
            # ... (Existing Fabric Logic) ...
            for detalhe in detalhes:
                mat_key = f'material_{detalhe.id}'
                cor_key = f'cor_{detalhe.id}'
                qty_key = f'quantidade_{detalhe.id}' # This is hidden input calc
                
                mat_id = request.POST.get(mat_key)
                cor_id = request.POST.get(cor_key)
                qty_val = request.POST.get(qty_key)
                
                # DEBUG
                if mat_id or cor_id:
                     print(f"DEBUG FABRIC: Detalhe={detalhe.id} Mat={mat_id} Cor={cor_id} Qty={qty_val}")


                if mat_id and qty_val:
                    try:
                        material = Material.objects.get(id=mat_id)
                        qty = float(qty_val)
                        
                        cor_obj = None
                        if cor_id:
                            cor_obj = Cor.objects.get(id=cor_id)

                        ItensMaterial.objects.update_or_create(
                            produto=product,
                            molde_detalhe=detalhe,
                            defaults={
                                'material': material, 
                                'cor': cor_obj,
                                'quantidade': qty, 
                                'tipo': 'tecido_padrao'
                            }
                        )
                        count += 1
                    except (ValueError, Material.DoesNotExist):
                        continue

            # 2. Update Existing Insumos (ProdutoInsumo table)
            existing_insumos = product.insumos.all()
            for item in existing_insumos:
                mat_id = request.POST.get(f'insumo_exist_mat_{item.id}')
                cor_id = request.POST.get(f'insumo_exist_cor_{item.id}')
                qty_val = request.POST.get(f'insumo_exist_qty_{item.id}')
                delete_flag = request.POST.get(f'insumo_delete_{item.id}')

                if delete_flag:
                    item.delete()
                    count += 1
                elif mat_id and qty_val:
                    try:
                        print(f"DEBUG UPDATE INSUMO {item.id}: Mat={mat_id} Cor={cor_id} Qty={qty_val}")
                        item.material_id = mat_id
                        item.cor_id = cor_id if cor_id else None
                        item.quantidade = float(qty_val.replace(',', '.'))
                        item.save()
                        count += 1
                    except ValueError:
                        continue

            # 3. Create New Insumos (ProdutoInsumo table)
            # Debug: Check keys
            print("POST KEYS:", request.POST.keys())
            
            new_mats = request.POST.getlist('new_insumo_material[]')
            new_cors = request.POST.getlist('new_insumo_cor[]')
            new_qtys = request.POST.getlist('new_insumo_quantidade[]')
            
            print(f"DEBUG INSUMOS: M={new_mats} C={new_cors} Q={new_qtys}")
            
            def parse_float(val):
                if not val: return 0.0
                return float(str(val).replace(',', '.'))

            from itertools import zip_longest
            for m_id, c_id, q_val in zip_longest(new_mats, new_cors, new_qtys):
                if m_id and q_val:
                    try:
                        qty = parse_float(q_val)
                        
                        # Use new table
                        ProdutoInsumo.objects.create(
                            produto=product,
                            material_id=m_id,
                            cor_id=c_id if c_id else None,
                            quantidade=qty
                        )
                        count += 1
                        print(f"Saved new insumo: Mat={m_id} Qty={qty}")
                    except Exception as e:
                        print(f"Error saving insumo {m_id}: {e}")
                        messages.warning(request, f"Erro ao salvar item {m_id}: {e}")
            
            if count > 0:
                messages.success(request, f"{count} itens atualizados com sucesso.")
            else:
                messages.warning(request, "Nenhum item válido para salvar.")
        
        elif action == 'add_material_by_piece':
            # Logic for Piece-specific assignment
            molde_detalhe_id = request.POST.get('molde_detalhe_id')
            mat_id = request.POST.get('material')
            # JS Calculator now sends quantity in correct Unit (Meters if fabric is Meters)
            qty_unit = float(request.POST.get('quantidade') or 0)
            
            if molde_detalhe_id and mat_id:
                material = Material.objects.get(id=mat_id)
                ItensMaterial.objects.create(
                    produto=product,
                    molde_detalhe_id=molde_detalhe_id,
                    material=material,
                    quantidade=qty_unit,
                    tipo='tecido_padrao' 
                )
                messages.success(request, f"Tecido atribuído à peça.")
                
        elif action == 'add_material_general':
            # Logic for General Insumos (No specific Molde Detalhe usually, or optional)
            mat_id = request.POST.get('material')
            qty = float(request.POST.get('quantidade') or 0)
            
            if mat_id:
                material = Material.objects.get(id=mat_id)
                ProdutoInsumo.objects.create(
                    produto=product,
                    material=material,
                    quantidade=qty
                )
                messages.success(request, f"Insumo '{material.nome}' adicionado.")

        elif action == 'delete_material':
             item_id = request.POST.get('item_id')
             ItensMaterial.objects.filter(id=item_id).delete()
             
        return redirect('product_detail', product_id=product.id)
    
    materials = Material.objects.all()
    # Correct filtering based on user instruction: eh_tecido field
    tecidos = Material.objects.filter(eh_tecido=True).order_by('nome')
    acessorios = Material.objects.filter(eh_tecido=False).order_by('nome')
    cores = Cor.objects.all().order_by('nome')
    
    
    # Calculate Total Cost
    custo_total = Decimal(0.0)
    for item in product.itens_material.all():
        price = item.material.preco_custo or Decimal(0.0)
        qty = Decimal(str(item.quantidade))
        custo_total += price * qty
        
    for item in product.insumos.all():
        price = item.material.preco_custo or Decimal(0.0)
        qty = Decimal(str(item.quantidade))
        custo_total += price * qty

    context = {
        'product': product,
        'custo_total': custo_total,
        'itens': product.itens_material.all().order_by('molde_detalhe__nome_original', 'id'),
        'detalhes': detalhes,
        'insumos_gerais': product.insumos.all().order_by('id'),
        'materials': materials,
        'tecidos': tecidos,
        'acessorios': acessorios,
        'cores': cores,
    }
    return render(request, 'products/product_detail.html', context)

def product_delete(request, product_id):
    produto = get_object_or_404(Produto, id=product_id)
    if request.method == 'POST':
        produto.delete()
        messages.success(request, "Produto excluído.")
    return redirect('product_list')

# TODO: Refactor Molde Import if necessary
def molde_import(request):
    if request.method == 'POST':
        form = MoldeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Create instance but DO NOT save the file field yet
            molde = form.save(commit=False)
            
            # Get the uploaded file
            uploaded_file = request.FILES.get('arquivo_json')
            
            if uploaded_file:
                # Set name if empty
                if not molde.nome:
                    name, _ = os.path.splitext(uploaded_file.name)
                    molde.nome = name
                
                # Crucial Step: Clear the file field to prevent saving to disk (redundant storage)
                molde.arquivo_json = None 
                molde.save()

                try:
                    # Process directly from memory stream
                    process_molde_json(molde, file_stream=uploaded_file)
                    
                    # Automaticaaly Create Standard Reference
                    std_ref = Produto.objects.create(
                        nome=f"Referência Padrão - {molde.nome}",
                        molde=molde,
                        eh_padrao=True,
                        preco=0.0
                    )
                    # Auto-populate ItensMaterial based on MoldeDetail for Standard Ref?
                    # For now just create the shell so user can configure it.
                    # We can auto-create empty slots if needed.
                    
                    messages.success(request, f"Molde '{molde.nome}' importado e Referência Padrão criada.")
                    return redirect('product_detail', product_id=std_ref.id) # Redirect to config standard ref
                except Exception as e:
                    print(f"Erro ao processar: {e}")
                    # Could add message error here
            else:
                 # Fallback if form valid but no file (shouldn't happen with required field)
                 molde.save()
                 
    else:
        form = MoldeUploadForm()
    return render(request, 'products/molde_import.html', {'form': form})

def sku_create(request, reference_id):
    """
    Criação de SKU Detalhada: Escolha de cores por peça/insumo.
    """
    reference = get_object_or_404(Produto, id=reference_id)
    cores = Cor.objects.all().order_by('nome')
    
    # Pegar materiais/peças e insumos do PAI
    ref_items = reference.itens_material.all()
    ref_insumos = reference.insumos.all()

    if request.method == 'POST':
        sku_code = request.POST.get('sku')
        nome = request.POST.get('nome_comercial')
        preco = request.POST.get('preco')
        
        # --- BLOC DE VERIFICAÇÃO DE DUPLICIDADE ---
        # 1. Construir assinatura proposta (Proposed Signature)
        # Formato: Lista de tuplas (tipo, item_id_ou_detalhe, material_id, cor_id, quantidade)
        # Tipo 1: Peça (ItemMaterial), Tipo 2: Insumo (ProdutoInsumo)
        
        proposed_signature = []
        
        # Coletar cores propostas para Itens (Peças)
        for item in ref_items:
            cor_id = request.POST.get(f'cor_item_{item.id}')
            cor_val = int(cor_id) if cor_id else None
            # Chave: 'piece', detalhe_id, mat_id, cor_id, qty
            proposed_signature.append(
                ('piece', item.molde_detalhe.id, item.material.id, cor_val, float(item.quantidade))
            )
            
        # Coletar cores propostas para Insumos
        for insumo in ref_insumos:
            cor_id = request.POST.get(f'cor_insumo_{insumo.id}')
            cor_val = int(cor_id) if cor_id else None
            # Para insumos, usamos o ID do insumo PAI para garantir a ordem/identidade se houver múltiplos iguais
            # Mas na comparação com irmãos, não temos link com ID do pai.
            # Então insumos serão tratados como "bag" de (material, cor, qty).
            proposed_signature.append(
                ('insumo', None, insumo.material.id, cor_val, float(insumo.quantidade))
            )
        
        # Ordenar para garantir consistência
        proposed_signature.sort() 
        
        # 2. Comparar com irmãos existentes
        siblings = Produto.objects.filter(parent=reference)
        is_duplicate = False
        duplicate_sku = ""

        from collections import Counter

        for sib in siblings:
            sib_signature = []
            
            # Signature das Peças do Irmão
            for s_item in sib.itens_material.all():
                c_id = s_item.cor.id if s_item.cor else None
                sib_signature.append(
                    ('piece', s_item.molde_detalhe.id, s_item.material.id, c_id, float(s_item.quantidade))
                )
            
            # Signature dos Insumos do Irmão
            for s_insumo in sib.insumos.all():
                c_id = s_insumo.cor.id if s_insumo.cor else None
                sib_signature.append(
                    ('insumo', None, s_insumo.material.id, c_id, float(s_insumo.quantidade))
                )
            
            sib_signature.sort()
            
            if proposed_signature == sib_signature:
                is_duplicate = True
                duplicate_sku = sib.sku or sib.nome
                break
        
        if is_duplicate:
            messages.error(request, f"ATENÇÃO: Já existe um produto com esta exata combinação de cores e materiais! (SKU: {duplicate_sku})")
            # Renderizar novamente com dados preenchidos seria ideal, mas redirect simples previne dados sujos por enquanto.
            # Para melhor UX, poderiamos passar os dados no contexto, mas simplificaremos.
            return render(request, 'products/sku_create.html', {
                'reference': reference,
                'cores': cores,
                'ref_items': ref_items,
                'ref_insumos': ref_insumos,
                'error_duplicate': True # Flag para UI se quiser usar
            })

        # --- FIM VERIFICAÇÃO ---

        # 1. Criar o registro do Produto (Filho)
        sku_obj = Produto.objects.create(
            parent=reference,
            molde=reference.molde,
            sku=sku_code,
            nome=nome if nome else f"{reference.nome}",
            nome_comercial=nome,
            preco=preco or 0.0
        )
        
        # 2. Processar Cores das Peças (ItensMaterial)
        for item in ref_items:
            cor_id = request.POST.get(f'cor_item_{item.id}')
            ItensMaterial.objects.create(
                produto=sku_obj,
                molde_detalhe=item.molde_detalhe,
                material=item.material,
                cor_id=cor_id if cor_id else None,
                quantidade=item.quantidade,
                tipo=item.tipo
            )

        # 3. Processar Cores dos Insumos (ProdutoInsumo)
        for insumo in ref_insumos:
            cor_id = request.POST.get(f'cor_insumo_{insumo.id}')
            ProdutoInsumo.objects.create(
                produto=sku_obj,
                material=insumo.material,
                cor_id=cor_id if cor_id else None,
                quantidade=insumo.quantidade
            )
            
        messages.success(request, f"Venda/SKU '{sku_obj.sku}' criado com sucesso com configurações de cores.")
        return redirect('integrated_view')

    context = {
        'reference': reference,
        'cores': cores,
        'ref_items': ref_items,
        'ref_insumos': ref_insumos,
    }
    return render(request, 'products/sku_create.html', context)


def integrated_view(request):
    """
    Painel Integrado: Lista de Referências (Fichas Técnicas) com filtro por molde.
    Permite visualizar custos e gerenciar SKUs de forma unificada.
    """
    molde_id = request.GET.get('molde_id')
    moldes = Molde.objects.all().order_by('nome')
    
    for m in moldes:
        m.ref_count = m.produto_set.filter(parent__isnull=True).count()

    # Queryset base: Apenas produtos "Pai" (Referências)
    queryset = Produto.objects.filter(parent__isnull=True).select_related('molde')\
        .prefetch_related('itens_material__material', 'insumos__material', 'variantes__itens_material__cor', 'variantes__insumos__cor')

    selected_molde = None
    if molde_id and molde_id != 'all':
        selected_molde = get_object_or_404(Molde, id=molde_id)
        queryset = queryset.filter(molde=selected_molde)

    referencias = queryset.order_by('nome')
    referencias_data = []

    for r in referencias:
        # Calcular custo estimativo da ficha técnica (Pai)
        cost = Decimal(0.0)
        # Itens Material (Tecidos vinculados a peças)
        for item in r.itens_material.all():
            price = item.material.preco_custo or Decimal(0.0)
            cost += price * Decimal(str(item.quantidade))
        # Insumos Globais
        for item in r.insumos.all():
            price = item.material.preco_custo or Decimal(0.0)
            cost += price * Decimal(str(item.quantidade))
        
        r.custo_estimado = cost
        # Variantes pré-carregadas
        r.skus = r.variantes.all()
        referencias_data.append(r)

    context = {
        'moldes': moldes,
        'selected_molde': selected_molde,
        'referencias_data': referencias_data,
        'selected_molde_id': molde_id or 'all'
    }
    return render(request, 'products/integrated_view.html', context)
    return render(request, 'products/integrated_view.html', context)

def sku_delete(request, sku_id):
    sku = get_object_or_404(Produto, id=sku_id)
    
    # Store context for redirect
    molde_id = sku.molde.id
    ref_id = sku.parent.id if sku.parent else None
    
    sku_code = sku.sku
    sku.delete()
    
    messages.success(request, f"Produto SKU '{sku_code}' removido com sucesso.")
    return redirect(f"/products/dashboard/?molde_id={molde_id}&ref_id={ref_id}")

def get_ref_variants(request, reference_id):
    """
    Returns the partial HTML for the variants list side panel.
    """
    reference = get_object_or_404(Produto, id=reference_id)
    variants = reference.variantes.all().order_by('sku')
    
    context = {
        'reference': reference,
        'variants': variants
    }
    return render(request, 'products/_ref_variants.html', context)
