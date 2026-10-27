# Sistema de Controle de Acesso - Sala Restrita (NDA)

Sistema distribuído de auditoria e controle de acesso a ambiente seguro com RFID, atuadores de feedback audiovisual, persistência em banco relacional, contingência offline com fila local, painel de monitoramento web em tempo real e relatórios analíticos com Pandas.

---

## 1. Arquitetura do Sistema

- **Camada Embarcada (Raspberry Pi / Simulação PC):** Leitura de tags RFID (MFRC522), acionamento de GPIO (LEDs e buzzer PWM), validação local via `cache.json`, histórico diário e fila de contingência `offline_queue.json`.
- **Backend (Flask + SQLite):** Fonte central de permissões, ingestão de auditoria de eventos, endpoints de sincronização e exportação de CSV.
- **Frontend de Gestão e Monitoramento:** Painel administrativo com login simples, CRUD de colaboradores e tela de vigilância com polling assíncrono (atualização a cada 2 segundos via `fetch`).
- **Módulo Analítico (Jupyter + Pandas):** Métricas de acesso diário, cálculo de tempo de permanência por colaborador e ranking de incidentes de segurança.

---

## 2. Pinagem de Hardware (Raspberry Pi - Numeração BOARD)

| Componente | Pino Placa (BOARD) | Função / Notas |
| :--- | :--- | :--- |
| **LED Verde** | Pino 8 | Acesso autorizado / Saída |
| **LED Vermelho** | Pino 7 | Acesso negado / Alerta de invasão |
| **Buzzer** | Pino 12 | Sinalização acústica via PWM (2500 Hz) |
| **MFRC522 SDA** | Pino 24 (CE0) | Interface SPI |
| **MFRC522 SCK** | Pino 23 (SCLK)| Interface SPI |
| **MFRC522 MOSI**| Pino 19 (MOSI)| Interface SPI |
| **MFRC522 MISO**| Pino 21 (MISO)| Interface SPI |
| **MFRC522 RST** | Pino 22 | Reset do leitor RFID |
| **Alimentação** | Pino 1 (3.3V) / Pino 6 (GND) | Linhas de energia e terra |

---

## 3. Estrutura de Pastas

```text
nda-access-control/
├── embedded/
│   ├── main.py              # Aplicação embarcada e simulação de hardware
│   ├── sync.py              # Cache local e fila de contingência offline
│   ├── cache.json           # Colaboradores e permissões locais (gerado em runtime)
│   └── offline_queue.json   # Fila de eventos pendentes de envio (em contingência)
├── backend/
│   ├── app.py               # Servidor Flask, rotas REST e interface Web
│   ├── database.py          # Conexão SQLite e operações de banco
│   ├── schema.sql           # Estrutura das tabelas colaboradores e eventos
│   ├── access_control.db    # Banco SQLite (gerado automaticamente)
│   └── templates/
│       ├── base.html        # Layout base com Bootstrap
│       ├── login.html       # Tela de login
│       ├── colaboradores.html # Interface de CRUD de colaboradores
│       ├── editar.html      # Formulário de edição
│       └── monitoramento.html # Painel de segurança com polling em tempo real
├── analytics/
│   ├── popular_dados_teste.py # Carga de eventos de auditoria para teste
│   └── relatorio.ipynb      # Notebook Jupyter com análises Pandas
└── README.md                # Documentação do projeto