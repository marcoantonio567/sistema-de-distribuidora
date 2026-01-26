import os
import shutil
from pathlib import Path

def clean_pycache():
    root_dir = Path('.')
    pycache_dirs = list(root_dir.rglob('__pycache__'))
    pyc_files = list(root_dir.rglob('*.pyc'))
    
    print(f"Encontrados {len(pycache_dirs)} diretórios __pycache__")
    print(f"Encontrados {len(pyc_files)} arquivos .pyc")
    
    for p in pyc_files:
        try:
            if p.exists():
                p.unlink()
                print(f"Removido arquivo: {p}")
        except Exception as e:
            print(f"Erro ao remover {p}: {e}")
            
    for d in pycache_dirs:
        try:
            if d.exists():
                shutil.rmtree(d)
                print(f"Removido diretório: {d}")
        except Exception as e:
            print(f"Erro ao remover {d}: {e}")

    print("Limpeza concluída!")

if __name__ == "__main__":
    clean_pycache()
