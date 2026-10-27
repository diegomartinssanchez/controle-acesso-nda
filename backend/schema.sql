-- DDL para controle de acesso e auditoria de eventos
CREATE TABLE IF NOT EXISTS colaboradores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    matricula TEXT UNIQUE NOT NULL,
    tag_rfid TEXT UNIQUE NOT NULL,
    cargo TEXT NOT NULL,
    tem_acesso INTEGER NOT NULL DEFAULT 0,
    ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    tag_rfid TEXT NOT NULL,
    nome TEXT,
    tipo_evento TEXT NOT NULL
);