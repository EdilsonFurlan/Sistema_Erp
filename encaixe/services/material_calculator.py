import math
from products.models import ProdutoConsumo
from molds.models import MoldePeca

def get_material_requirements_for_orders(orders):
    """
    Calculates total material requirements for a list of orders.
    Returns a dictionary: key=(material, cor), value={'qtd': float, 'pecas': list}
    """
    report_data = {}

    for order in orders:
        for item in order.itens.all():
            
            # 1. Fabrics (from Configs) - Dynamic Calculation
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
                margin = 0 
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

            # 2. Accessories (Insumos) - Direct from Configuration (ProdutoInsumoCor)
            if item.produto:
                # Iterate over configured supplies
                for pic in item.produto.insumos_cor.all():
                    
                    # Resolve Material Override
                    material = pic.material if pic.material else pic.molde_material.material
                    cor = pic.cor
                    
                    # Resolve Quantity (from Molde definition)
                    qty_unit = pic.molde_material.quantidade
                    
                    # Normalize to MM if it's a measure unit (because View expects MM for these units)
                    # Assuming MoldeMaterial stores the value in the Material's unit (e.g. 0.8 for 0.8 mt)
                    if material.is_unidade_medida():
                        u = material.unidade.lower().strip()
                        if u in ['mt', 'm', 'mts', 'metro', 'metros']:
                            qty_unit *= 1000.0
                        elif u in ['cm', 'centimetro']:
                            qty_unit *= 10.0
                    
                    qty_total = qty_unit * item.quantidade
                    
                    key = (material, cor)
                    
                    if key not in report_data:
                        report_data[key] = {'qtd': 0.0, 'pecas': set()}
                    
                    report_data[key]['qtd'] += qty_total

    return report_data
