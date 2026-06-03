import zipfile
import pathlib

def create_backup():
    root_dir = pathlib.Path(r"c:\Users\julianag18\Desktop\Proyecto de grado\proyecto_grado-main")
    backup_file = pathlib.Path(r"c:\Users\julianag18\Desktop\Proyecto de grado\backup_pame_bloque1.zip")
    
    ignored_dirs = {'.venv', '.git', '.pytest_cache', '__pycache__'}
    ignored_files = {'.env', 'firebase_credentials.json', 'firebase-key.json'}
    
    print(f"Iniciando backup en: {backup_file}...")
    
    with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in root_dir.rglob('*'):
            # Verificar si está en directorios ignorados
            parts = file_path.relative_to(root_dir).parts
            if any(ignored in parts for ignored in ignored_dirs):
                continue
                
            # Verificar si es un archivo ignorado
            if file_path.name in ignored_files or file_path.suffix == '.pyc':
                continue
                
            # Solo agregar archivos (las carpetas se crean implícitamente)
            if file_path.is_file():
                arcname = file_path.relative_to(root_dir)
                zipf.write(file_path, arcname)
                print(f" Agregado: {arcname}")
                
    print(f"\n¡Backup creado con éxito en: {backup_file}!")

if __name__ == "__main__":
    create_backup()
