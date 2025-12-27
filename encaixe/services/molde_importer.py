import json
import math
from molds.models import MoldeDetalhe
from inventory.models import Material
from django.db import transaction

from encaixe.utils import read_mld_file

from django.core.files.base import ContentFile

def process_molde_json(molde, file_stream=None):
    """
    Parses the JSON file (or .mld file) associated with a Molde and creates MoldeDetalhe records.
    Ignores Insumos/Materials as they are now defined in Produto.
    
    Args:
        molde: The Molde instance to populate.
        file_stream: Optional file-like object containing the uploaded .mld data. 
                     If provided, we read from this instead of molde.arquivo_json.
    """
    try:
        data = {}
        
        # Determine source
        source = None
        if file_stream:
            source = file_stream
        elif molde.arquivo_json:
             # Fallback to existing file if no stream provided (legacy re-import)
             try:
                 source = molde.arquivo_json.open('rb')
             except:
                 # If we can't open 'rb' (maybe it's a FieldFile), try path
                 pass

        if source:
             # Try to read as .mld (binary) first
            try:
                # read_mld_file now handles file-like objects
                mld_content = read_mld_file(source)
                data = mld_content.get('data', {})
                
                if thumb_bytes and len(thumb_bytes) > 0:
                    filename = f"thumb_{molde.id}.png"
                    molde.imagem.save(filename, ContentFile(thumb_bytes), save=False)
                    from molds.models import Molde
                    Molde.objects.filter(id=molde.id).update(imagem=molde.imagem.name)
            except (ValueError, FileNotFoundError):
                 # Fallback: Try to read as standard JSON (rewind first)
                 if hasattr(source, 'seek'):
                     source.seek(0)
                 try:
                     # Assumes text JSON
                     text_content = source.read().decode('utf-8')
                     data = json.loads(text_content)
                 except:
                      # Last resort
                      pass
        
        if not data and molde.arquivo_json and hasattr(molde.arquivo_json, 'path'):
             # OLD Logic fallback using path
             try:
                mld_content = read_mld_file(molde.arquivo_json.path)
                data = mld_content.get('data', {})
             except:
                with open(molde.arquivo_json.path, 'r') as f:
                    data = json.load(f)
        
        pieces_data = data.get('pieces', [])
        # insumos_data = data.get('insumos', []) # Ignored
        # accessories_data = data.get('accessories', []) # Ignored
        
        with transaction.atomic():
            # Clear old data 
            molde.detalhes.all().delete()
            # materials were removed from Molde model

            # Process Pieces (Geometry Only)
            for p_data in pieces_data:
                geom = p_data.get('geom', {})
                tipo = geom.get('type', 'unknown')
                
                # Area Calculation (Priority: JSON value > Calculated)
                area = float(p_data.get('area_mm2', 0.0))
                
                if area == 0.0:
                    # Fallback calculation
                    if tipo == 'rect':
                        hw = geom.get('halfW', 0)
                        hh = geom.get('halfH', 0)
                        area = (hw * 2) * (hh * 2)
                        w_current = hw * 2
                        h_current = hh * 2
                    elif tipo == 'circle':
                        r = geom.get('radius', 0)
                        area = math.pi * (r ** 2)
                        w_current = r * 2
                        h_current = r * 2
                    elif tipo == 'poly':
                        pts = geom.get('pts', [])
                        if pts:
                            xs = [p['x'] for p in pts]
                            ys = [p['y'] for p in pts]
                            w_current = max(xs) - min(xs)
                            h_current = max(ys) - min(ys)
                            
                            # Shoelace Formula
                            area_accum = 0.0
                            n = len(pts)
                            for i in range(n):
                                j = (i + 1) % n
                                area_accum += pts[i]['x'] * pts[j]['y']
                                area_accum -= pts[j]['x'] * pts[i]['y']
                            area = abs(area_accum) / 2.0
                        else:
                            area = 0.0
                else:
                    # Provide dummy dimensions for rotation logic if needed
                    w_current = 100
                    h_current = 100

                # Rotation Constraints and Grain
                can_rotate = p_data.get('canRotate', True)
                fixed_rot = p_data.get('fixedRotation', False)
                auto_orient = p_data.get('autoOrient', False) 
                grain_axis = p_data.get('grainAxis', p_data.get('grain', 'y')) 
                
                should_rotate_90 = False
                
                # Logic 1: Auto Orient (Longest Side -> Y)
                if area == 0.0 and auto_orient: # Only calc rotation if we calculated dims
                    if w_current > h_current:
                        should_rotate_90 = True
                
                # Logic 2: Explicit Grain Axis (Arrow)
                if str(grain_axis).lower() in ['x', 'h', 'horizontal']:
                    should_rotate_90 = True
                
                if should_rotate_90:
                    # Perform Rotation (Transpose / Flip)
                    if tipo == 'rect':
                        geom['halfW'] = hh
                        geom['halfH'] = hw
                    elif tipo == 'poly':
                        pts = geom.get('pts', [])
                        new_pts = []
                        min_x_new = float('inf')
                        min_y_new = float('inf')
                        
                        for p in pts:
                            # Rotate (x,y) -> (y, -x)
                            nx = p['y']
                            ny = -p['x']
                            new_pts.append({'x': nx, 'y': ny})
                            if nx < min_x_new: min_x_new = nx
                            if ny < min_y_new: min_y_new = ny
                        
                        # Normalize
                        for p in new_pts:
                            p['x'] -= min_x_new
                            p['y'] -= min_y_new
                        
                        geom['pts'] = new_pts
                    
                    fixed_rot = True

                is_fixed = False
                if can_rotate is False: is_fixed = True
                if fixed_rot is True: is_fixed = True

                MoldeDetalhe.objects.create(
                    molde=molde,
                    nome_original=p_data.get('name', 'Peca Sem Nome'),
                    tipo_geom=tipo,
                    area_base_mm2=area,
                    largura_mm=w_current,
                    altura_mm=h_current,
                    # material_padrao removed
                    qtd_padrao=p_data.get('qty', 1),
                    rotacao_fixa=is_fixed,
                    orientacao_fio=str(grain_axis),
                    geometria_json=geom
                )
            
    except Exception as e:
        print(f"Erro ao processar JSON: {e}")
        raise e
