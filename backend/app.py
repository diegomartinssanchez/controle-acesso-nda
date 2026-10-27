"""
Servidor HTTP Flask com API REST, Interface Web e Monitoramento em Tempo Real.
Execucao: python backend/app.py
"""
import io
import csv
from functools import wraps
from flask import Flask, jsonify, request, Response, render_template, redirect, url_for, session
import database

app = Flask(__name__)
app.secret_key = "segredo-nda-controle-acesso"

database.init_db()

def login_obrigatorio(f):
    """Protege rotas exigindo autenticacao previa."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("autenticado"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# --- ROTAS WEB (LOGIN & CRUD) ---

@app.route("/")
def index():
    return redirect(url_for("painel_monitoramento"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Valida credenciais simples de acesso administrativo."""
    if request.method == "POST":
        usuario = request.form.get("usuario")
        senha = request.form.get("senha")
        if usuario == "admin" and senha == "admin123":
            session["autenticado"] = True
            return redirect(url_for("painel_monitoramento"))
        return render_template("login.html", erro="Credenciais invalidas")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/monitoramento")
@login_obrigatorio
def painel_monitoramento():
    """Renderiza a interface de monitoramento da equipe de seguranca."""
    return render_template("monitoramento.html")

@app.route("/colaboradores")
@login_obrigatorio
def listar_colaboradores():
    colabs = database.listar_todos_colaboradores()
    return render_template("colaboradores.html", colaboradores=colabs)

@app.route("/colaboradores/novo", methods=["POST"])
@login_obrigatorio
def novo_colaborador():
    database.criar_colaborador(
        nome=request.form["nome"],
        matricula=request.form["matricula"],
        tag_rfid=request.form["tag_rfid"].strip(),
        cargo=request.form["cargo"],
        tem_acesso=1 if request.form.get("tem_acesso") else 0,
        ativo=1 if request.form.get("ativo") else 0
    )
    return redirect(url_for("listar_colaboradores"))

@app.route("/colaboradores/editar/<int:colab_id>", methods=["GET", "POST"])
@login_obrigatorio
def editar_colaborador(colab_id):
    if request.method == "POST":
        database.atualizar_colaborador(
            colab_id=colab_id,
            nome=request.form["nome"],
            matricula=request.form["matricula"],
            tag_rfid=request.form["tag_rfid"].strip(),
            cargo=request.form["cargo"],
            tem_acesso=1 if request.form.get("tem_acesso") else 0,
            ativo=1 if request.form.get("ativo") else 0
        )
        return redirect(url_for("listar_colaboradores"))
    colaborador = database.buscar_colaborador_por_id(colab_id)
    return render_template("editar.html", c=colaborador)

@app.route("/colaboradores/excluir/<int:colab_id>")
@login_obrigatorio
def excluir_colaborador(colab_id):
    database.excluir_colaborador(colab_id)
    return redirect(url_for("listar_colaboradores"))

# --- ROTAS REST (POLLING, EMBARCADO & PANDAS) ---

@app.route("/api/monitoramento", methods=["GET"])
def get_monitoramento():
    """Endpoint de polling para o dashboard de seguranca."""
    return jsonify(database.obter_dados_monitoramento()), 200

@app.route("/api/colaboradores", methods=["GET"])
def get_colaboradores():
    return jsonify(database.listar_colaboradores_ativos()), 200

@app.route("/api/eventos", methods=["POST"])
def post_eventos():
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "JSON invalido ou ausente"}), 400
    database.salvar_eventos(dados)
    return jsonify({"status": "sucesso", "registrados": len(dados) if isinstance(dados, list) else 1}), 201

@app.route("/api/eventos/exportar", methods=["GET"])
def exportar_csv():
    eventos = database.buscar_todos_eventos()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["timestamp", "tag_rfid", "nome", "tipo_evento"], delimiter=";")
    writer.writeheader()
    for ev in eventos:
        writer.writerow(ev)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=eventos.csv"}
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)