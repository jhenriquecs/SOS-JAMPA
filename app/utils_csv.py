import os, json

# ===== JSON Functions =====
def ensure_json_file(path):
    """
    Cria um arquivo JSON vazio (lista vazia []) se ele não existir.
    Útil para inicializar arquivos de dados na primeira execução.
    """
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def read_json(path):
    """
    Lê e retorna o conteúdo de um arquivo JSON.
    Retorna uma lista vazia se o arquivo não existir ou estiver corrompido.
    """
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def append_json(path, row_dict):
    """
    Adiciona um novo registro (dicionário) ao final de um arquivo JSON existente.
    Lê o arquivo, adiciona o item e salva novamente.
    """
    data = read_json(path)
    data.append(row_dict)
    write_json(path, data)

def write_json(path, data):
    """
    Sobrescreve o conteúdo de um arquivo JSON com os dados fornecidos.
    Garante a formatação correta (indentação e caracteres especiais).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
