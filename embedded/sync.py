"""
Sincronizacao de dados entre a Raspberry e o Backend Flask.
Uso: Importado por embedded/main.py.
"""
import json
import os
import requests

CACHE_FILE = os.path.join(os.path.dirname(__file__), "cache.json")
QUEUE_FILE = os.path.join(os.path.dirname(__file__), "offline_queue.json")

def carregar_cache(backend_url):
    """
    Busca colaboradores e permissoes na API e salva em cache.json.
    Se o backend falhar, carrega os dados locais existentes.
    """
    try:
        res = requests.get(f"{backend_url}/api/colaboradores", timeout=3)
        if res.status_code == 200:
            dados = {str(item["tag_rfid"]): item for item in res.json()}
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            return dados
    except Exception:
        pass

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def enfileirar_evento(evento):
    """Adiciona evento pendente em offline_queue.json caso o backend nao responda."""
    fila = []
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                fila = json.load(f)
        except Exception:
            fila = []
    fila.append(evento)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(fila, f, ensure_ascii=False, indent=2)

def sincronizar_eventos(backend_url, evento_atual=None):
    """
    Tenta enviar o evento atual e descarregar pendencias da fila offline no backend.
    """
    fila = []
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                fila = json.load(f)
        except Exception:
            fila = []

    if evento_atual:
        fila.append(evento_atual)

    if not fila:
        return

    try:
        res = requests.post(f"{backend_url}/api/eventos", json=fila, timeout=3)
        if res.status_code in (200, 201):
            if os.path.exists(QUEUE_FILE):
                os.remove(QUEUE_FILE)
            return
    except Exception:
        pass

    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(fila, f, ensure_ascii=False, indent=2)