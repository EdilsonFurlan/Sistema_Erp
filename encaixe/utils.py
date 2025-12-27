import struct
import json
import os

def read_mld_file(file_input):
    """
    Lê um arquivo .mld (caminho str ou objeto file-like)
    Retorna um dicionário com versão, thumbnail(bytes) e dados(dict).
    """
    if isinstance(file_input, str):
        if not os.path.exists(file_input):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_input}")
        f = open(file_input, 'rb')
        should_close = True
    else:
        f = file_input
        should_close = False

    try:
        # Garante que está no inicio do stream se for um arquivo aberto
        if hasattr(f, 'seek') and f.tell() != 0:
            f.seek(0)

        # 1. Valida Header (10 bytes)
        header = f.read(10)
        # O header esperado é "MOLDE_RAW\0"
        if header != b'MOLDE_RAW\0':
             raise ValueError("Arquivo .mld inválido ou corrompido.")
        
        # 2. Lê Versão (4 bytes, unsigned int, little-endian)
        try:
            version = struct.unpack('<I', f.read(4))[0]
            
            # 3. Lê Thumbnail
            thumb_size = struct.unpack('<I', f.read(4))[0]
            thumbnail_data = f.read(thumb_size) # Dados binários do PNG
            
            # 4. Lê JSON
            json_size = struct.unpack('<I', f.read(4))[0]
            json_bytes = f.read(json_size)
            
            # Decodifica o JSON
            project_data = json.loads(json_bytes.decode('utf-8'))
            
            return {
                'version': version,
                'thumbnail': thumbnail_data,
                'data': project_data
            }
        except struct.error:
            raise ValueError("Arquivo .mld incompleto ou mal formatado.")
        except json.JSONDecodeError:
            return {
                'version': version,
                'thumbnail': thumbnail_data,
                'data': {}
            }
    finally:
        if should_close:
            f.close()
