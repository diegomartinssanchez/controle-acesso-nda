"""
Gerenciamento de conexao e operacoes no SQLite.
Uso: Importado diretamente pelo app Flask (sem execucao standalone).
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "access_control.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def get_connection():
    """Retorna uma conexao ativa com suporte a mapeamento por nome de coluna."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa as tabelas do banco e insere colaboradores base caso esteja vazio."""
    with get_connection() as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM colaboradores")
        if cursor.fetchone()[0] == 0:
            colaboradores_iniciais = [
                ("Wagner", "MAT001", "701044494601", "Dev Senior", 1, 1),
                ("Diego",  "MAT002", "427389875583", "UI/UX Designer", 0, 1)
            ]
            cursor.executemany(
                "INSERT INTO colaboradores (nome, matricula, tag_rfid, cargo, tem_acesso, ativo) VALUES (?, ?, ?, ?, ?, ?)",
                colaboradores_iniciais
            )
            conn.commit()

def listar_colaboradores_ativos():
    """Retorna lista de colaboradores ativos para sincronizacao com a Raspberry."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tag_rfid, nome, tem_acesso FROM colaboradores WHERE ativo = 1")
        return [dict(row) for row in cursor.fetchall()]

def listar_todos_colaboradores():
    """Retorna todos os colaboradores cadastrados para a interface web."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, matricula, tag_rfid, cargo, tem_acesso, ativo FROM colaboradores ORDER BY nome ASC")
        return [dict(row) for row in cursor.fetchall()]

def buscar_colaborador_por_id(colab_id):
    """Busca os dados de um unico colaborador pelo ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, matricula, tag_rfid, cargo, tem_acesso, ativo FROM colaboradores WHERE id = ?", (colab_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def criar_colaborador(nome, matricula, tag_rfid, cargo, tem_acesso, ativo):
    """Cadastra um novo colaborador no banco."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO colaboradores (nome, matricula, tag_rfid, cargo, tem_acesso, ativo) VALUES (?, ?, ?, ?, ?, ?)",
            (nome, matricula, tag_rfid, cargo, tem_acesso, ativo)
        )
        conn.commit()

def atualizar_colaborador(colab_id, nome, matricula, tag_rfid, cargo, tem_acesso, ativo):
    """Atualiza dados e permissoes de um colaborador existente."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE colaboradores SET nome=?, matricula=?, tag_rfid=?, cargo=?, tem_acesso=?, ativo=? WHERE id=?",
            (nome, matricula, tag_rfid, cargo, tem_acesso, ativo, colab_id)
        )
        conn.commit()

def excluir_colaborador(colab_id):
    """Remove um colaborador do banco de dados."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM colaboradores WHERE id = ?", (colab_id,))
        conn.commit()

def salvar_eventos(eventos):
    """Insere um unico evento ou uma lista de eventos sincronizados."""
    if not isinstance(eventos, list):
        eventos = [eventos]
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO eventos (timestamp, tag_rfid, nome, tipo_evento) VALUES (:timestamp, :tag_rfid, :nome, :tipo_evento)",
            eventos
        )
        conn.commit()

def buscar_todos_eventos():
    """Retorna todos os eventos ordenados cronologicamente."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, tag_rfid, nome, tipo_evento FROM eventos ORDER BY timestamp ASC")
        return [dict(row) for row in cursor.fetchall()]

def obter_dados_monitoramento():
    """
    Consolida status em tempo real: pessoas na sala, ultimas acoes e alertas.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Ultimos 15 eventos registrados
        cursor.execute("SELECT timestamp, tag_rfid, nome, tipo_evento FROM eventos ORDER BY id DESC LIMIT 15")
        ultimos_eventos = [dict(r) for r in cursor.fetchall()]
        
        # Reconstruir estado atual (dentro da sala)
        # O ultimo evento de ENTRADA ou SAIDA de cada tag determina se ela esta presente
        cursor.execute("""
            SELECT tag_rfid, nome, tipo_evento, timestamp
            FROM eventos
            WHERE tipo_evento IN ('ENTRADA', 'SAIDA')
            ORDER BY id ASC
        """)
        presenca = {}
        for r in cursor.fetchall():
            if r["tipo_evento"] == "ENTRADA":
                presenca[r["tag_rfid"]] = {"nome": r["nome"], "desde": r["timestamp"]}
            elif r["tipo_evento"] == "SAIDA" and r["tag_rfid"] in presenca:
                del presenca[r["tag_rfid"]]
        
        presentes = [{"tag_rfid": k, "nome": v["nome"], "desde": v["desde"]} for k, v in presenca.items()]
        
        # Filtros rapidos para o painel de seguranca
        ultimas_entradas = [e for e in ultimos_eventos if e["tipo_evento"] == "ENTRADA"][:5]
        ultimas_saidas = [e for e in ultimos_eventos if e["tipo_evento"] == "SAIDA"][:5]
        negados = [e for e in ultimos_eventos if e["tipo_evento"] == "ACESSO_NEGADO"][:5]
        invasoes = [e for e in ultimos_eventos if e["tipo_evento"] == "INVASAO"][:5]
        
        return {
            "presentes": presentes,
            "total_presentes": len(presentes),
            "ultimas_entradas": ultimas_entradas,
            "ultimas_saidas": ultimas_saidas,
            "negados": negados,
            "invasoes": invasoes,
            "historico_recente": ultimos_eventos
        }