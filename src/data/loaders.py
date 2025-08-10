import os
import json

# ----------------------------
# carrega os dados armazenados em .json
# ----------------------------
def carregar_jsons(diretorio, recursivo=False, tipo="item"):
    # ----------------------------
    # carrega json de um diretório e retorna um dicionário mapeando 'nome' -> dados
    # obs: para cartas com nomes repetidos, ia sobrescrever 
    # por isso usamos essa função para 'cavalas' (onde o nome deve ser unico)
    # e uma função custom para 'cartas' (indexando por imagem, nome não unico)
    # ----------------------------
    itens = {}
    if not os.path.isdir(diretorio):
        print(f"[AVISO] Diretório não encontrado: {diretorio}")
        return itens

    walker = os.walk(diretorio) if recursivo else [(diretorio, [], os.listdir(diretorio))]
    for root, _, files in walker:
        for fname in files:
            if not fname.endswith('.json'):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, encoding='utf-8') as f:
                    dados = json.load(f)
                nome = dados.get('nome')
                if not nome:
                    print(f"[AVISO] JSON sem 'nome': {path}")
                    continue
                # aviso para duplicatas por nome (só pra cavalas)
                if nome in itens:
                    print(f"[AVISO] {tipo} duplicado '{nome}' em {path}")
                itens[nome] = dados
            except Exception as e:
                print(f"[ERRO] Falha lendo {path}: {e}")
    return itens


def carregar_cartas(diretorio):
    # ----------------------------
    # carrega cartas indexando pelo caminho da imagem (card_id)
    # permite que cartas com o mesmo nome existam (contanto que tenham imagens diferentes)
    # ----------------------------
    itens = {}
    if not os.path.isdir(diretorio):
        print(f"[AVISO] Diretório não encontrado: {diretorio}")
        return itens

    for root, _, files in os.walk(diretorio):
        for fname in files:
            if not fname.endswith('.json'):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, encoding='utf-8') as f:
                    dados = json.load(f)

                nome = dados.get('nome')
                imagem = dados.get('imagem')  # caminho relativo p/ imagem (único por tipo/raridade)
                if not nome or not imagem:
                    print(f"[AVISO] carta com 'nome' ou 'imagem' ausente: {path}")
                    continue

                key = imagem
                if key in itens:
                    # se duas cartas apontarem para a mesma imagem, tem aviso no terminal
                    print(f"[AVISO] carta duplicada por imagem '{key}' em {path}")

                itens[key] = dados
            except Exception as e:
                print(f"[ERRO] Falha lendo {path}: {e}")
    return itens


def carregar_cavalas(diretorio):
    # ----------------------------
    # carrega cavalas indexando por 'nome' (nome é único)
    # ----------------------------
    return carregar_jsons(diretorio, recursivo=False, tipo="cavala")