import math
from products.models import ProdutoConsumo
from molds.models import MoldeDetalhe

def get_material_requirements_for_orders(orders):
    """
    Calculates total material requirements for a list of orders.
    Returns a dictionary: key=(material, cor), value={'qtd': float, 'pecas': list}
    """
    report_data = {}

    for order in orders:
        for item in order.itens.all():
            
            # 1. Fabrics (from Configs) - Dynamic Calculation
            # This ensures we handle custom fabric widths correctly vs the cached standard.
            configs = item.configuracoes.all()
            for conf in configs:
                if not conf.material: continue
                
                # --- Geometric Calculation (Bounding Box) ---
                
                width_mm = conf.material.largura_padrao_mm if conf.material.largura_padrao_mm else 1500
                
                # Extract Geometry to calc BBox
                geom = conf.molde_peca.geometria_json
                g_type = geom.get('type', 'unknown')
                
                w_box, h_box = 0, 0
                
                if g_type == 'rect':
                    w_box = geom.get('halfW', 0) * 2
                    h_box = geom.get('halfH', 0) * 2
                elif g_type == 'circle':
                    r = geom.get('radius', 0)
                    w_box = r * 2
                    h_box = r * 2
                elif g_type == 'poly':
                    pts = geom.get('pts', [])
                    if pts:
                        xs = [p['x'] for p in pts]
                        ys = [p['y'] for p in pts]
                        w_box = max(xs) - min(xs)
                        h_box = max(ys) - min(ys)
                
                # Add Margin
                margin = 0 # Could be configurable
                w_box += margin
                h_box += margin
                
                # --- ROW YIELD CALCULATION ---
                # Calculate Total Quantity of PIECES needed
                qty_peca_por_produto = conf.molde_peca.qtd_padrao if conf.molde_peca.qtd_padrao else 1
                total_item_qty = item.quantidade * qty_peca_por_produto
                
                # Option A: Normal Orientation
                fits_normal = int(width_mm // w_box)
                if fits_normal < 1: fits_normal = 1
                
                rows_normal = math.ceil(total_item_qty / fits_normal)
                total_normal = rows_normal * h_box
                
                # Option B: Rotated Orientation (90 deg)
                if conf.molde_peca.rotacao_fixa:
                    linear_mm = total_normal
                else:
                    fits_rotated = int(width_mm // h_box)
                    if fits_rotated < 1: fits_rotated = 1
                    
                    rows_rotated = math.ceil(total_item_qty / fits_rotated)
                    total_rotated = rows_rotated * w_box
                    
                    linear_mm = min(total_normal, total_rotated)
                
                linear_mm_safe = linear_mm * 1.00
                
                key = (conf.material, conf.cor)
                if key not in report_data:
                    report_data[key] = {'qtd': 0.0, 'pecas': []}
                
                report_data[key]['qtd'] += linear_mm_safe
                # report_data[key]['pecas'].append(...)

            # 2. Accessories (Insumos) - Direct from Configuration (ProdutoInsumoCor)
            # 2. Accessories / Materials (Defined in ItensMaterial)
            # Logic: Use the BOM from Produto, applied with the SKU Color.
            if item.produto:
                # item.produto is now a SKU (Unified Produto model where parent is not null)
                sku = item.produto
                
                # Helper to add to report
                def add_item_to_report(material, cor, quantity, order_qty):
                     if not material: return
                     qty_unit = quantity
                     
                     # Normalize Unit
                     if material.is_unidade_medida():
                        u = material.unidade.lower().strip()
                        if u in ['mt', 'm', 'mts', 'metro', 'metros']:
                            qty_unit *= 1000.0
                        elif u in ['cm', 'centimetro']:
                            qty_unit *= 10.0
                            
                     qty_total = qty_unit * order_qty
                     
                     key = (material, cor)
                     if key not in report_data:
                        report_data[key] = {'qtd': 0.0, 'pecas': set()}
                     
                     report_data[key]['qtd'] += qty_total

                # 0. Fabrics (Standard SKU Consumption) - IF NOT Custom Config
                if not item.configuracoes.exists():
                     consumos = sku.consumos.all()
                     if consumos.exists():
                         for cons in consumos:
                             # ProdutoConsumo usually stores calculated fabric consumption
                             add_item_to_report(cons.material, cons.cor, cons.consumo_total, item.quantidade)
                     else:
                         # Fallback: Check ItensMaterial for Fabric (if cache is missing)
                         for bom_item in sku.itens_material.filter(tipo='tecido_padrao'):
                             add_item_to_report(bom_item.material, bom_item.cor, bom_item.quantidade, item.quantidade)

                # 1. Iterate SKU ItensMaterial (Fabrics & Insumos linked to pieces)
                for bom_item in sku.itens_material.all():
                    if bom_item.tipo == 'tecido_padrao': continue # Handled by Geometry/Config OR ProdutoConsumo above
                    
                    if bom_item.tipo == 'insumo':
                        add_item_to_report(bom_item.material, bom_item.cor, bom_item.quantidade, item.quantidade)
                
                # 2. Iterate SKU Global Insumos
                for insumo in sku.insumos.all():
                    add_item_to_report(insumo.material, insumo.cor, insumo.quantidade, item.quantidade)

    return report_data

