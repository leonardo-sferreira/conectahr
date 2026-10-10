"""Testes da tela "Ponto" (tarefas 19 a 21 da change concluir-frontend-streamlit), sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Horários ........... milissegundos UTC do backend aparecem no horário de Brasília
  Ordem (21) ......... a tela mostra uma única próxima marcação, na ordem entrada -> saída almoço ->
                       volta almoço -> saída; a recusa do backend (fora de ordem, dia completo) aparece
  Correção ........... modal com validação; envia campo, horário em ms UTC e motivo; "em análise"
  Ausência ........... modal com validação; envia tipo, datas, motivo e observação; dia justificado
  Estados ............ vazio, sem colaborador, erro e sucesso

Uso (na raiz do repositório):
    python tools/testar_ponto.py
"""

import html as html_lib
import logging
import re
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
BR = timezone(timedelta(hours=-3))
HOJE = datetime.now(timezone.utc).date()  # a data que o backend usa para o registro do dia
SEGUNDA = HOJE - timedelta(days=HOJE.weekday())
chamadas: list[tuple] = []
estado: dict = {}


def ms(dia: date, h: int, m: int) -> int:
    return int(datetime(dia.year, dia.month, dia.day, h, m, tzinfo=BR).timestamp() * 1000)


def registros_padrao(marcas_hoje: int = 2) -> list[dict]:
    regs = []
    if HOJE != SEGUNDA:
        regs.append({"id": 501, "data": SEGUNDA.isoformat(), "hora_entrada": ms(SEGUNDA, 8, 1), "inicio_intervalo": ms(SEGUNDA, 12, 0),
                     "fim_intervalo": ms(SEGUNDA, 13, 2), "hora_saida": ms(SEGUNDA, 17, 31), "horas_trabalhadas": 8.5, "status": "Completo"})
    hoje = {"id": 599, "data": HOJE.isoformat(), "status": "Aberto"}
    for campo, (h, m) in list(zip(("hora_entrada", "inicio_intervalo", "fim_intervalo", "hora_saida"), ((8, 2), (12, 5), (13, 1), (17, 30))))[:marcas_hoje]:
        hoje[campo] = ms(HOJE, h, m)
    regs.append(hoje)
    # registro de outra semana: não entra no espelho
    antigo = SEGUNDA - timedelta(days=7)
    regs.append({"id": 400, "data": antigo.isoformat(), "hora_entrada": ms(antigo, 8, 0), "status": "Completo", "horas_trabalhadas": 8})
    return regs


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _marcar(token):
    chamadas.append(("marcar",))
    _falha_ou("marcar", None)
    hoje = next(r for r in estado["registros"] if r["data"] == HOJE.isoformat())
    for campo in ("hora_entrada", "inicio_intervalo", "fim_intervalo", "hora_saida"):
        if not hoje.get(campo):
            hoje[campo] = ms(HOJE, 13, 1)
            return {"sucesso": True, "registro": hoje}
    raise ApiError("Todos os marcadores de ponto de hoje ja foram registrados.", 400)


def _instalar():
    api_client.auth_me = lambda token: {"autenticado": True}
    api_client.central_de_tarefas = lambda token: {}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.meu_ponto = lambda token: chamadas.append(("meu_ponto",)) or _falha_ou("ponto", {"registros": estado["registros"]})
    api_client.meu_banco_horas = lambda token: _falha_ou("banco", {"saldo_horas": 3.3333})
    api_client.minhas_correcoes_ponto = lambda token: {"correcoes": estado["correcoes"]}
    api_client.minhas_ausencias = lambda token: {"ausencias": estado["ausencias"]}
    api_client.marcar_ponto = _marcar
    api_client.solicitar_correcao_ponto = lambda token, rid, campo, valor, just: chamadas.append(("correcao", rid, campo, valor, just)) or _falha_ou("correcao", {"sucesso": True})
    api_client.registrar_ausencia = lambda token, tipo, i, f, motivo, obs: chamadas.append(("ausencia", tipo, i, f, motivo, obs)) or _falha_ou("ausencia", {"sucesso": True})


_instalar()
falhas: list[str] = []
total = 0


def conferir(ok: bool, descricao: str) -> None:
    global total
    total += 1
    if not ok:
        falhas.append(descricao)
        print("  FALHA:", descricao)
    else:
        print("  ok:", descricao)


def caso(titulo: str) -> None:
    print(f"\n{titulo}")


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def chaves(at: AppTest) -> set:
    return {b.key for b in at.button}


def abrir(at: AppTest, url_path: str) -> AppTest:
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == url_path)
    return at.run()


def app(**extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(registros=registros_padrao(), correcoes=[], ausencias=[])
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Leonardo dos Santos", "email": "leonardo@empresa.com", "perfil": "COLABORADOR", "colaborador_id": 9}
    at.session_state["sessao_validada"] = True
    return abrir(at.run(), "ponto")


# ---------------------------------------------------------------------------
caso("Regras de apresentação (ponto_modelo.py)")
import ponto_modelo as m  # noqa: E402

conferir(m.hora(ms(date(2026, 9, 2), 8, 2)) == "08:02" and m.hora("2026-09-02T11:02:00Z") == "08:02", "UTC do backend vira horário de Brasília")
conferir((m.horas_trabalhadas(8.5), m.horas_trabalhadas(9.0667), m.horas_trabalhadas(None)) == ("8h30", "9h04", "—"), "horas trabalhadas por extenso")
conferir(m.saldo(3.3333) == ("+3h20", "positivo") and m.saldo(-1.5) == ("-1h30", "negativo") and m.saldo(0)[0] == "0h00", "saldo com sinal e cor")
estados = lambda reg: [c["estado"] for c in m.cartoes_hoje(reg)]
conferir(estados(None) == ["proximo", "futuro", "futuro", "futuro"], "sem registro hoje: a próxima é a entrada")
conferir(estados({"hora_entrada": 1, "inicio_intervalo": 2}) == ["feito", "feito", "proximo", "futuro"], "duas marcações: a próxima é a volta do almoço")
conferir(estados({c: 1 for c, _ in m.MARCACOES}) == ["feito"] * 4 and m.proxima_marcacao({c: 1 for c, _ in m.MARCACOES}) is None, "dia completo: nenhuma marcação a fazer")
noite = datetime(2026, 10, 10, 22, 30, tzinfo=BR)  # 01:30 do dia 11 em UTC
conferir(m.hoje_do_backend(noite) == date(2026, 10, 11) and m.titulo_hoje(noite) == "Hoje — sábado, 10/10/2026", "depois das 21h o backend já usa o dia seguinte (UTC); o título segue Brasília")
conferir(m.valor_solicitado_ms(date(2026, 8, 29), time(17, 30)) == int(datetime(2026, 8, 29, 20, 30, tzinfo=timezone.utc).timestamp() * 1000), "horário correto 17:30 vira 20:30 UTC em ms")
linhas = m.espelho_da_semana(registros_padrao(), [{"tipo": "Atestado", "data_inicio": HOJE.isoformat(), "data_fim": HOJE.isoformat(), "status": "Rejeitada"}], [{"registro_ponto_id": 599, "status": "pendente"}], HOJE)
conferir(all(l["data"] >= SEGUNDA for l in linhas) and len(linhas) == (1 if HOJE == SEGUNDA else 2), "espelho só da semana atual")
conferir(linhas[-1]["acao"] == "em_analise" and linhas[-1]["status"] == "EM ANDAMENTO", "correção pendente: 'em análise' no lugar do botão")
dia_aus = SEGUNDA + timedelta(days=1) if HOJE != SEGUNDA else HOJE
regs = [r for r in registros_padrao() if r["data"] != dia_aus.isoformat()]
lin_aus = [l for l in m.espelho_da_semana(regs, [{"tipo": "Atestado", "data_inicio": dia_aus.isoformat(), "data_fim": dia_aus.isoformat(), "status": "Aprovada"}], [], HOJE) if l["ausencia"]]
conferir(len(lin_aus) == 1 and lin_aus[0]["status"] == "JUSTIFICADO" and lin_aus[0]["trabalhado"] == "Atestado", "ausência aprovada: dia justificado no espelho")
conferir(m.validar_correcao(None, time(8), "motivo") and m.validar_correcao("hora_saida", None, "motivo") and m.validar_correcao("hora_saida", time(8), "abc") and m.validar_correcao("hora_saida", time(17, 30), "Esqueci de marcar") is None, "correção: marcação, horário e motivo de 5+ caracteres")
conferir(m.validar_ausencia("Atestado", date(2026, 9, 2), date(2026, 9, 1), "consulta", "") and m.validar_ausencia("Atestado", date(2026, 9, 1), date(2026, 9, 1), None, "") and m.validar_ausencia("Atestado", date(2026, 9, 1), date(2026, 9, 1), "consulta", "") is None, "ausência: datas em ordem e motivo da lista")

# ---------------------------------------------------------------------------
caso("Tela 'Ponto' (Figma 39:18)")
at = app()
t = texto(at)
conferir("Hoje —" in t and "Entrada 08:02" in t and "Saída almoço 12:05" in t, "caixas do dia com as marcações feitas")
conferir("Saldo do banco de horas +3h20" in t, "saldo do banco de horas")
conferir("Controle interno experimental" in t and "Portaria nº 671/2021" in t, "aviso de controle interno experimental")
conferir("Espelho de ponto — semana" in t and "8h30" in t and "COMPLETO" in t, "espelho da semana")
conferir([k for k in chaves(at) if k == "pt_marcar"] == ["pt_marcar"] and {"pt_editar_hora_entrada", "pt_editar_inicio_intervalo"} <= chaves(at), "um só 'Marcar agora'; 'Editar' nas marcações feitas")
conferir(not any(c[0] in ("marcar", "correcao", "ausencia") for c in chamadas), "abrir a tela não marca nem envia nada")

caso("Marcar o ponto (ordem estrita, tarefa 21)")
at.button(key="pt_marcar").click()
at = at.run()
conferir(("marcar",) in chamadas and "Volta almoço 13:01" in texto(at), "'Marcar agora' registra a volta do almoço (a próxima da ordem)")
at = app(registros=registros_padrao(marcas_hoje=4))
conferir("pt_marcar" not in chaves(at), "dia completo: não há 'Marcar agora'")
at = app(erro_marcar=ApiError("O intervalo minimo da matriz ainda nao foi cumprido e nao ha override aprovado para este colaborador.", 400))
at.button(key="pt_marcar").click()
at = at.run()
conferir("intervalo minimo" in texto(at) and not at.exception, "recusa do backend (intervalo mínimo) aparece como alerta")
at = app(registros=[r for r in registros_padrao() if r["data"] != HOJE.isoformat()])
conferir("pt_marcar" in chaves(at) and "Entrada —" in texto(at), "sem registro hoje: a entrada é a próxima")

caso("Solicitar correção (Figma 221:196)")
at = app()
alvo = 501 if HOJE != SEGUNDA else 599
at.button(key=f"pt_corrigir_{alvo}").click()
at = at.run()
at.button(key="pt_corr_enviar").click()
at = at.run()
conferir("Escolha a marcação." in texto(at) and not any(c[0] == "correcao" for c in chamadas), "sem marcação, não envia")
at.selectbox(key="pt_corr_campo").set_value("hora_saida")
at.time_input(key="pt_corr_hora").set_value(time(17, 30))
at.text_area(key="pt_corr_motivo").set_value("Esqueci de marcar a saída.")
at.button(key="pt_corr_enviar").click()
at = at.run()
dia_alvo = SEGUNDA if HOJE != SEGUNDA else HOJE
enviado = next((c for c in chamadas if c[0] == "correcao"), None)
conferir(enviado is not None and enviado[1:3] == (alvo, "hora_saida") and enviado[3] == ms(dia_alvo, 17, 30) and enviado[4] == "Esqueci de marcar a saída.", "envia registro, campo, horário em ms UTC e motivo")
conferir("modal_ponto" not in at.session_state, "o modal fecha")
at = app()
at.button(key="pt_editar_hora_entrada").click()
at = at.run()
conferir(at.selectbox(key="pt_corr_campo").value == "hora_entrada", "'Editar' abre a correção já com a marcação escolhida")
at = app(erro_correcao=ApiError("Ja existe uma solicitacao de correcao pendente para este campo.", 400))
at.button(key="pt_editar_hora_entrada").click()
at = at.run()
at.time_input(key="pt_corr_hora").set_value(time(8, 0))
at.text_area(key="pt_corr_motivo").set_value("Marquei atrasado.")
at.button(key="pt_corr_enviar").click()
at = at.run()
conferir("Ja existe uma solicitacao" in texto(at) and "modal_ponto" in at.session_state, "recusa do backend no modal, que continua aberto")
at = app(correcoes=[{"registro_ponto_id": alvo, "status": "pendente"}])
conferir(f"pt_corrigir_{alvo}" not in chaves(at) and "Correção em análise" in texto(at), "com pedido pendente: 'Correção em análise'")

caso("Registrar ausência (Figma 221:285)")
at = app()
at.button(key="pt_btn_ausencia").click()
at = at.run()
at.button(key="pt_aus_enviar").click()
at = at.run()
conferir("Escolha o motivo." in texto(at) and not any(c[0] == "ausencia" for c in chamadas), "sem motivo, não envia")
at.selectbox(key="pt_aus_motivo").set_value("consulta")
at.text_area(key="pt_aus_obs").set_value("Consulta de rotina.")
at.button(key="pt_aus_enviar").click()
at = at.run()
aus = next((c for c in chamadas if c[0] == "ausencia"), None)
conferir(aus is not None and aus[1] == "Atestado" and aus[2] == aus[3] == date.today().isoformat() and aus[4] == "consulta" and aus[5] == "Consulta de rotina.", "envia tipo, datas, motivo e observação")
at = app(erro_ausencia=ApiError("Nao informe diagnostico nem codigo CID na observacao. O diagnostico fica somente no atestado.", 400))
at.button(key="pt_btn_ausencia").click()
at = at.run()
at.selectbox(key="pt_aus_motivo").set_value("doenca")
at.text_area(key="pt_aus_obs").set_value("CID J11")
at.button(key="pt_aus_enviar").click()
at = at.run()
conferir("Nao informe diagnostico" in texto(at), "recusa do backend (CID na observação) aparece no modal")

caso("Estados: sem colaborador, erro e saldo indisponível")
at = app(erro_ponto=ApiError("Nao existe um colaborador vinculado a conta autenticada.", 404))
conferir("não marca ponto" in texto(at) and not at.exception, "conta sem colaborador: mensagem")
at = app(erro_ponto=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro ao carregar vira alerta")
at = app(erro_banco=ApiError("Erro", 500))
conferir("Não foi possível carregar o saldo agora." in texto(at) and "Espelho de ponto" in texto(at), "sem o saldo, o resto da tela continua")
at = app(registros=[])
conferir("Nenhuma marcação nesta semana." in texto(at) and "pt_marcar" in chaves(at), "vazio: semana sem marcações")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
