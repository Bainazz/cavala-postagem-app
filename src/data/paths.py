from pathlib import Path

# arquivo atual: .../src/data/paths.py
# BASE deve ser a pasta RAIZ do projeto (contendo 'src' e as pastas de assets)
DATA_DIR = Path(__file__).resolve().parent            # .../src/data
SRC_DIR = DATA_DIR.parent                             # .../src
BASE = SRC_DIR.parent                                 # .../

def asset_path(*parts: str) -> Path:
    return BASE.joinpath(*parts)