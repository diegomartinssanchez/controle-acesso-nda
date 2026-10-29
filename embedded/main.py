"""
Controle de acesso por RFID com contingencia offline e modo simulacao.
Execucao real:     python embedded/main.py
Execucao no PC:    python embedded/main.py --simular
"""
import sys
import time
from datetime import datetime, date
import sync

BACKEND_URL = "http://localhost:5000"
SIMULACAO = "--simular" in sys.argv
INTERVALO_ATUALIZACAO_CACHE = 10

PIN_LED_VERDE = 8
PIN_LED_VERM = 7
PIN_BUZZER = 12

if not SIMULACAO:
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(PIN_LED_VERDE, GPIO.OUT)
    GPIO.setup(PIN_LED_VERM, GPIO.OUT)
    GPIO.setup(PIN_LED_BUZZER if 'PIN_LED_BUZZER' in locals() else PIN_BUZZER, GPIO.OUT)
    buzzer = GPIO.PWM(PIN_BUZZER, 2500)
    leitor = SimpleMFRC522()
else:
    GPIO = None
    buzzer = None
    leitor = None

def acionar_sucesso():
    """Aciona LED verde e buzzer continuo curto para acessos permitidos."""
    if SIMULACAO:
        print("[HARDWARE] LED VERDE ON | BUZZER BIP CURTO")
        return
    GPIO.output(PIN_LED_VERDE, GPIO.HIGH)
    buzzer.start(50)
    time.sleep(0.5)
    buzzer.stop()
    GPIO.output(PIN_LED_VERDE, GPIO.LOW)

def acionar_negado():
    """Aciona LED vermelho e buzzer curto sem bloqueio prolongado."""
    if SIMULACAO:
        print("[HARDWARE] LED VERMELHO ON | BUZZER TOM GRAVE")
        return
    GPIO.output(PIN_LED_VERM, GPIO.HIGH)
    buzzer.start(40)
    time.sleep(0.6)
    buzzer.stop()
    GPIO.output(PIN_LED_VERM, GPIO.LOW)

def acionar_invasao():
    """Aciona LED vermelho e buzzer piscando 10 vezes em alerta critico."""
    if SIMULACAO:
        print("[HARDWARE] ALERTA DE INVASAO! LED VERMELHO + BUZZER PISCANDO 10x")
        return
    for _ in range(10):
        GPIO.output(PIN_LED_VERM, GPIO.HIGH)
        buzzer.start(80)
        time.sleep(0.15)
        GPIO.output(PIN_LED_VERM, GPIO.LOW)
        buzzer.stop()
        time.sleep(0.15)

def ler_tag():
    """Obtem o ID da tag lida no hardware ou digitada no terminal."""
    if SIMULACAO:
        entrada = input("\n[SIMULADOR] Digite a tag RFID (ou 'sair'): ").strip()
        if entrada.lower() == "sair":
            sys.exit(0)
        return entrada
    print("\nAproxime a tag...")
    tag_id, _ = leitor.read()
    return str(tag_id).strip()

def processar_acesso(tag, cache, estado_usuarios):
    """
    Avalia a tag, calcula tempos de permanencia, aciona hardware e retorna o evento.
    """
    agora = datetime.now()
    hoje = date.today().isoformat()
    timestamp = agora.strftime("%Y-%m-%d %H:%M:%S")

    # 1. Tag nao cadastrada
    if tag not in cache:
        print("[ALERTA] Identificacao nao encontrada! Possivel invasao.")
        acionar_invasao()
        return {"timestamp": timestamp, "tag_rfid": tag, "nome": None, "tipo_evento": "INVASAO"}

    colaborador = cache[tag]
    nome = colaborador["nome"]

    # 2. Tag cadastrada, mas sem acesso permitido a sala restrita
    if not colaborador.get("tem_acesso"):
        print(f"[NEGADO] {nome} nao tem permissao para acessar esta sala.")
        acionar_negado()
        return {"timestamp": timestamp, "tag_rfid": tag, "nome": nome, "tipo_evento": "ACESSO_NEGADO"}

    # Inicializa rastreamento local de sessao do usuario
    if tag not in estado_usuarios:
        estado_usuarios[tag] = {
            "dentro": False,
            "ultima_entrada": None,
            "total_segundos_hoje": 0,
            "dia": hoje,
            "entradas_hoje": 0
        }

    usuario = estado_usuarios[tag]
    if usuario["dia"] != hoje:
        usuario["dia"] = hoje
        usuario["total_segundos_hoje"] = 0
        usuario["entradas_hoje"] = 0

    # 3. Alternancia: se esta dentro, registrar SAIDA
    if usuario["dentro"]:
        tempo_sessao = int((agora - usuario["ultima_entrada"]).total_seconds())
        usuario["total_segundos_hoje"] += tempo_sessao
        usuario["dentro"] = False
        minutos = usuario["total_segundos_hoje"] // 60
        print(f"[SAIDA] Ate logo, {nome}! Permanencia acumulada hoje: {minutos} min.")
        acionar_sucesso()
        return {"timestamp": timestamp, "tag_rfid": tag, "nome": nome, "tipo_evento": "SAIDA"}

    # 4. Alternancia: se esta fora, registrar ENTRADA
    usuario["dentro"] = True
    usuario["ultima_entrada"] = agora
    usuario["entradas_hoje"] += 1

    if usuario["entradas_hoje"] == 1:
        print(f"[ENTRADA] Bem-vindo, {nome}!")
    else:
        print(f"[ENTRADA] Bem-vindo de volta, {nome}!")

    acionar_sucesso()
    return {"timestamp": timestamp, "tag_rfid": tag, "nome": nome, "tipo_evento": "ENTRADA"}

def loop_principal():
    """Ciclo principal de leitura e envio de eventos."""
    print(f"Iniciando leitor... (Modo: {'SIMULADOR PC' if SIMULACAO else 'HARDWARE REAL'})")
    cache = sync.carregar_cache(BACKEND_URL)
    print(f"Colaboradores carregados em cache: {len(cache)}")
    
    estado_usuarios = {}
    ultimo_sync_cache = time.time()

    try:
        while True:
            try:
                agora = time.time()

                if agora - ultimo_sync_cache >= INTERVALO_ATUALIZACAO_CACHE:
                    cache_atualizado = sync.carregar_cache(BACKEND_URL)
                    if cache_atualizado:
                        cache = cache_atualizado
                    ultimo_sync_cache = agora

                tag = ler_tag()
                if not tag:
                    time.sleep(0.3)  # Evita sobrecarga de CPU na Raspberry enquanto nao ha cartao
                    continue

                evento = processar_acesso(tag, cache, estado_usuarios)
                sync.sincronizar_eventos(BACKEND_URL, evento)

            except Exception as erro_leitura:
                print(f"[AVISO] Falha durante a leitura/processamento: {erro_leitura}")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nFinalizando aplicacao...")
    finally:
        if not SIMULACAO and GPIO:
            GPIO.cleanup()

if __name__ == "__main__":
    loop_principal()