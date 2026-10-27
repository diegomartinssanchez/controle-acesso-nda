"""
Script utilitario para semear o banco com eventos de teste.
Execucao: python analytics/popular_dados_teste.py
"""
import requests

BACKEND_URL = "http://localhost:5000"

eventos_teste = [
    # Dia 2026-10-26 (Dia principal da analise)
    {"timestamp": "2026-10-26 08:30:00", "tag_rfid": "701044494601", "nome": "Wagner", "tipo_evento": "ENTRADA"},
    {"timestamp": "2026-10-26 08:35:10", "tag_rfid": "427389875583", "nome": "Diego", "tipo_evento": "ACESSO_NEGADO"},
    {"timestamp": "2026-10-26 08:35:40", "tag_rfid": "427389875583", "nome": "Diego", "tipo_evento": "ACESSO_NEGADO"},
    {"timestamp": "2026-10-26 08:40:00", "tag_rfid": "999888777111", "nome": None, "tipo_evento": "INVASAO"},
    {"timestamp": "2026-10-26 12:00:00", "tag_rfid": "701044494601", "nome": "Wagner", "tipo_evento": "SAIDA"},
    {"timestamp": "2026-10-26 13:15:00", "tag_rfid": "701044494601", "nome": "Wagner", "tipo_evento": "ENTRADA"},
    {"timestamp": "2026-10-26 14:02:15", "tag_rfid": "427389875583", "nome": "Diego", "tipo_evento": "ACESSO_NEGADO"},
    {"timestamp": "2026-10-26 17:45:00", "tag_rfid": "701044494601", "nome": "Wagner", "tipo_evento": "SAIDA"},
    {"timestamp": "2026-10-26 18:10:00", "tag_rfid": "999888777111", "nome": None, "tipo_evento": "INVASAO"},
    # Dia anterior (para validar filtros de data)
    {"timestamp": "2026-10-25 09:00:00", "tag_rfid": "701044494601", "nome": "Wagner", "tipo_evento": "ENTRADA"},
    {"timestamp": "2026-10-25 18:00:00", "tag_rfid": "701044494601", "nome": "Wagner", "tipo_evento": "SAIDA"}
]

def enviar():
    """Envia o lote de eventos para o backend."""
    try:
        res = requests.post(f"{BACKEND_URL}/api/eventos", json=eventos_teste, timeout=3)
        if res.status_code == 201:
            print("Base de dados de teste populada com sucesso!")
        else:
            print(f"Erro ao enviar: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Falha de conexao com o backend: {e}")

if __name__ == "__main__":
    enviar()