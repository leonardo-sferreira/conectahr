"""Testes da tela "Ponto" → "Hoje" no REP-P (change ponto-rep-p-e-ferias-clt, tarefa 4.2; Figma 463:825 e 465:932),
sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Regras ............. horários de Brasília, o papel de cada marcação (entrada, almoço, volta, saída), selo do dia, comprovantes de 48 horas,
                       validação do pedido de correção (inclusão, desconsideração, motivo de 5 a 150)
  Hoje ............... relógio, "Marcar ponto" sem limite, marcações do dia com NSR e comprovante em PDF
  Estados ............ vazio, sucesso (com o comprovante), erro (antes da admissão), bloqueado (sem empregador),
                       permissão negada (comprovantes), sem colaborador e saldo indisponível
  Ausência ........... modal com validação; envia tipo, datas, motivo e observação
  Sem visão semanal .. só "Hoje" e "Mês"

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
import ponto_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
BR = timezone(timedelta(hours=-3))
HOJE = datetime.now(BR).date()  # o backend usa a data de Brasília para o dia da marcação
ONTEM = HOJE - timedelta(days=1)
EMPREGADOR = {"razao_social": "ConectaRH Tecnologia Ltda (ficticio)", "tipo_identificador": "cnpj", "identificador": "12345678000190",
              "cno_caepf": "", "local_prestacao": "Av. Paulista, 1000 - Sao Paulo/SP", "inpi_registro": "BR512026000000"}
TRABALHADOR = {"nome": "Leonardo dos Santos", "cpf": "12345678909", "data_admissao": "2026-01-05", "cargo": "Analista de RH"}
chamadas: list[tuple] = []
estado: dict = {}


def ms(dia: date, h: int, mi: int, s: int = 0) -> int:
    return int(datetime(dia.year, dia.month, dia.day, h, mi, s, tzinfo=BR).timestamp() * 1000)


def marcacao(mid: int, nsr: int, dia: date, h: int, mi: int) -> dict:
    return {"id": mid, "nsr": nsr, "data": dia.isoformat(), "data_hora_marcacao": ms(dia, h, mi),
            "data_hora_marcacao_txt": f"{dia.isoformat()}T{h:02d}:{mi:02d}:00-0300", "hash": f"{nsr:064x}"}


def marcacoes_padrao() -> list[dict]:
    return [marcacao(10, 1276, ONTEM, 13, 0), marcacao(11, 1279, ONTEM, 17, 48), marcacao(20, 1284, HOJE, 0, 2), marcacao(21, 1285, HOJE, 0, 5)]


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _marcar(token):
    chamadas.append(("marcar",))
    _falha_ou("marcar", None)
    nsr = max([mc["nsr"] for mc in estado["marcacoes"]] or [0]) + 1
    nova = marcacao(100 + nsr, nsr, HOJE, 0, 9)
    nova["data_hora_marcacao"] += 22_000  # 00:09:22
    estado["marcacoes"].append(nova)
    return {"sucesso": True, "marcacao": nova, "comprovante": {"empregador": EMPREGADOR, "trabalhador": TRABALHADOR}}


def _instalar():
    api_client.auth_me = lambda token: {"autenticado": True}
    api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}  # menu Equipe (tarefa 83)
    api_client.prazo_correcao = lambda token: {"prazo_dias": None}
    api_client.central_de_tarefas = lambda token: {}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.meu_ponto = lambda token: chamadas.append(("meu_ponto",)) or _falha_ou("ponto", {"registros": [], "marcacoes": estado["marcacoes"], "tratamentos": []})
    api_client.comprovantes_ponto = lambda token: _falha_ou("comprovantes", {"marcacoes": estado["marcacoes"], "empregador": EMPREGADOR, "trabalhador": TRABALHADOR,
                                                                           "jornada": estado.get("jornada")})
    api_client.meu_banco_horas = lambda token: _falha_ou("banco", {"saldo_horas": 3.3333})
    api_client.minhas_correcoes_ponto = lambda token: {"correcoes": []}
    api_client.minhas_ausencias = lambda token: {"ausencias": []}
    api_client.marcar_ponto = _marcar
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


def downloads(at: AppTest) -> dict:
    return {b.key: b for b in at.get("download_button")}


def app(**extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(marcacoes=marcacoes_padrao())
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Leonardo dos Santos", "email": "leonardo@empresa.com", "perfil": "COLABORADOR", "colaborador_id": 9}
    at.session_state["sessao_validada"] = True
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "ponto")
    return at.run()


# ---------------------------------------------------------------------------
caso("Regras de apresentação (ponto_modelo.py)")
conferir(m.hora(ms(date(2026, 9, 2), 8, 2)) == "08:02" and m.hora("2026-09-02T11:02:00Z") == "08:02", "UTC do backend vira horário de Brasília")
conferir((m.horas_trabalhadas(8.5), m.horas_trabalhadas(9.0667), m.horas_trabalhadas(None)) == ("8h30", "9h04", "—"), "horas por extenso")
conferir(m.saldo(3.3333) == ("+3h20", "positivo") and m.saldo(-1.5) == ("-1h30", "negativo") and m.saldo(0)[0] == "0h00", "saldo com sinal e cor")
noite = datetime(2026, 10, 10, 22, 30, tzinfo=BR)
conferir(m.hoje_brasilia(noite) == date(2026, 10, 10) and m.titulo_hoje(noite) == "Hoje — sábado, 10/10/2026", "depois das 21h ainda é o mesmo dia (Brasília)")
conferir([m.rotulo_marcacao(i, 4) for i in range(4)] == ["Entrada", "Saída para o almoço", "Volta do almoço", "Saída"], "dia de quatro marcações: entrada, almoço, volta e saída")
conferir([m.rotulo_marcacao(i, 2) for i in range(2)] == ["Entrada", "Saída"] and [m.rotulo_marcacao(i, 3) for i in range(3)] == ["Entrada", "Saída para o almoço", "Volta do almoço"],
         "jornada sem almoço; dia ainda em andamento depois do almoço")
conferir([m.rotulo_marcacao(i, 6) for i in range(6)] == ["Entrada", "Saída para o almoço", "Volta do almoço", "Saída para intervalo", "Volta do intervalo", "Saída"],
         "mais de quatro marcações: intervalos no meio, sem limite")
dia = date(2026, 10, 14)
fora_de_ordem = [marcacao(3, 1286, dia, 13, 1), marcacao(1, 1284, dia, 8, 2), marcacao(2, 1285, dia, 12, 5), marcacao(9, 1280, dia - timedelta(days=1), 17, 0)]
hoje_l = m.linhas_hoje(fora_de_ordem, dia)
conferir([(l["rotulo"], l["hora"], l["nsr"]) for l in hoje_l] == [("Entrada", "08:02", "000001284"), ("Saída para o almoço", "12:05", "000001285"), ("Volta do almoço", "13:01", "000001286")],
         "Hoje: só as do dia, em ordem de NSR, com hora e NSR de 9 dígitos")
conferir(m.texto_proxima(0).startswith("A próxima marcação será a entrada.") and m.texto_proxima(2).startswith("A próxima marcação será a volta do almoço.")
         and m.texto_proxima(3) == "A próxima marcação será a saída (para o almoço, um intervalo ou o fim da jornada). Você pode marcar quantas vezes precisar.",
         "texto da próxima marcação")
conferir(m.situacao_hoje(3) == ("Em jornada · 3 marcações hoje", "amb") and m.situacao_hoje(4)[0].startswith("Fora de jornada") and m.situacao_hoje(0) is None, "selo do dia")
agora = datetime(2026, 10, 14, 13, 5, tzinfo=BR)
recentes = m.comprovantes_recentes(fora_de_ordem + [marcacao(7, 1200, dia - timedelta(days=3), 8, 0)], agora)
conferir([c["nsr"] for c in recentes] == ["000001286", "000001285", "000001284", "000001280"] and recentes[0]["quando"] == "14/10/2026 13:01"
         and recentes[0]["rotulo"] == "Volta do almoço", "comprovantes: últimas 48 horas, do mais recente, com o papel no dia")
conferir(m.validar_pedido(None, None, None, "motivo") == "Escolha o que precisa ser corrigido." and m.validar_pedido("inclusao", None, None, "motivo")
         and m.validar_pedido("desconsideracao", None, None, "motivo") and m.validar_pedido("inclusao", time(13), None, "abc")
         and m.validar_pedido("inclusao", time(13), None, "x" * 151) and m.validar_pedido("inclusao", time(13), None, "Esqueci de marcar") is None
         and m.validar_pedido("desconsideracao", None, 7, "Marquei duas vezes") is None, "pedido: tipo, horário ou marcação, e motivo de 5 a 150")
conferir(m.valor_solicitado_ms(date(2026, 8, 29), time(17, 30)) == int(datetime(2026, 8, 29, 20, 30, tzinfo=timezone.utc).timestamp() * 1000), "17:30 de Brasília vira 20:30 UTC em ms")
conferir(m.validar_ausencia("Atestado", date(2026, 9, 2), date(2026, 9, 1), "consulta", "") and m.validar_ausencia("Atestado", date(2026, 9, 1), date(2026, 9, 1), "consulta", "") is None,
         "ausência: datas em ordem e motivo da lista")

caso("Tela 'Hoje' (Figma 463:825)")
at = app()
t = texto(at)
conferir(not at.exception, "a tela abre sem erro")
conferir(m.titulo_hoje() in t and "Horário de Brasília (UTC-03:00), pelo servidor" in t and re.search(r"\b\d{2}:\d{2}:\d{2}\b", t), "título, relógio com segundos e a nota do servidor")
conferir("Entrada" in t and "00:02" in t and "000001284" in t and "Saída" in t and "000001285" in t, "marcações de hoje com o papel, a hora e o NSR")
conferir("A próxima marcação será a volta do almoço" in t and "Fora de jornada · 2 marcações hoje" in t, "próxima marcação e selo")
d = downloads(at)
conferir("pt_cp_hoje_20" in d and "pt_cp_hoje_21" in d, "comprovante em PDF de cada marcação de hoje")
conferir("Comprovantes das últimas 48 horas" in t and "pt_cp_10" in d and "pt_cp_11" in d and "NSR 000001279" in t, "comprovantes das últimas 48 horas, com os de ontem")
conferir("Saldo do banco de horas" in t and "+3h20" in t and "pt_btn_ausencia" in {b.key for b in at.button}, "saldo e ausência")
conferir("não vale como REP-P para a fiscalização" in t, "aviso de que ainda não vale como REP-P para a fiscalização")
conferir(at.button_group(key="pt_visao").options == ["Hoje", "Mês"] and "Semana" not in t, "só Hoje e Mês, sem visão semanal")

caso("Marcar o ponto (sem ordem nem limite, art. 74)")
for _ in range(3):
    at.button(key="pt_marcar").click()
    at = at.run()
t = texto(at)
conferir(chamadas.count(("marcar",)) == 3 and "Volta do intervalo" in t and "Saída para intervalo" in t, "três marcações seguidas, todas gravadas (5 no dia)")
conferir("Ponto marcado às 00:09:22 (UTC-03:00). NSR 000001288." in t and "pt_baixar_ultimo" in downloads(at), "sucesso com hora, segundos, NSR e o comprovante na hora")
conferir("Em jornada · 5 marcações hoje" in t, "o selo acompanha a quantidade")

caso("Descanso entre jornadas: aviso, não bloqueio (design D13, Figma 'Modal/Aviso de descanso')")
# Mínimo de 50 horas no teste, para a última marcação de ontem sempre cair dentro do descanso, a qualquer hora do dia.
JORNADA = {"horas_diarias": 8, "descanso_minimo_minutos": 3000}
at = app(marcacoes=[marcacao(30, 1300, ONTEM, 22, 0)], jornada=JORNADA)
at.button(key="pt_marcar").click()
at = at.run()
t = texto(at)
conferir(("marcar",) not in chamadas and at.session_state["modal_ponto"][0] == "descanso", "dentro do descanso: abre o aviso e ainda não marca")
conferir("Última marcação" in t and "Ontem, " in t and "às 22:00" in t and "(mínimo 50h00)" in t and "seu gestor e o RH serão avisados" in t, "aviso com a última marcação, o descanso e quem é avisado")
at.button(key="pt_desc_desistir").click()
at = at.run()
conferir(("marcar",) not in chamadas and "modal_ponto" not in at.session_state, "desistir não grava nada")
at.button(key="pt_marcar").click()
at = at.run()
at.button(key="pt_desc_confirmar").click()
at = at.run()
conferir(chamadas.count(("marcar",)) == 1 and "Ponto marcado às" in texto(at), "confirmar grava a marcação")
at = app(marcacoes=[marcacao(30, 1300, ONTEM, 22, 0)], jornada={"horas_diarias": 8, "descanso_minimo_minutos": 1})
at.button(key="pt_marcar").click()
at = at.run()
conferir(chamadas.count(("marcar",)) == 1 and "modal_ponto" not in at.session_state, "descanso cumprido: marca direto")
at = app(marcacoes=[marcacao(30, 1300, ONTEM, 22, 0)], jornada={"horas_diarias": None, "descanso_minimo_minutos": None})
at.button(key="pt_marcar").click()
at = at.run()
conferir(chamadas.count(("marcar",)) == 1, "PJ (sem jornada): sem aviso")

caso("Estados (Figma 465:932)")
at = app(marcacoes=[])
t = texto(at)
conferir("Você ainda não marcou o ponto hoje." in t and "Nenhuma marcação nas últimas 48 horas." in t, "vazio: sem marcação hoje")
at = app(erro_marcar=ApiError("Sua admissao e em 05/10/2026. O ponto pode ser marcado a partir dessa data.", 403))
at.button(key="pt_marcar").click()
at = at.run()
t = texto(at)
conferir("Sua admissao e em 05/10/2026" in t and "Nada foi gravado." in t, "erro antes da admissão: a mensagem e 'Nada foi gravado.'")
at = app(erro_marcar=ApiError("O ponto ainda nao esta liberado: o RH precisa cadastrar os dados do empregador em Ponto eletronico (REP-P).", 403))
at.button(key="pt_marcar").click()
at = at.run()
conferir('O ponto ainda não está liberado: o RH precisa cadastrar os dados do empregador em "Ponto eletrônico (REP-P)".' in texto(at), "bloqueado: empregador não cadastrado")
at = app(erro_comprovantes=ApiError("Acesso negado.", 403))
conferir("Você não tem permissão para ver este comprovante. Cada pessoa vê só os próprios." in texto(at), "permissão negada nos comprovantes")
at = app(erro_ponto=ApiError("Nao existe um colaborador vinculado a conta autenticada.", 404))
conferir("Sem cadastro de colaborador" in texto(at), "sem colaborador vinculado")
at = app(erro_ponto=ApiError("Erro inesperado.", 500))
conferir("Erro inesperado." in texto(at), "erro ao carregar")
at = app(erro_banco=ApiError("Erro inesperado.", 500))
conferir("Não foi possível carregar o saldo agora." in texto(at) and "Entrada" in texto(at) and "000001284" in texto(at), "sem o saldo, o resto da tela segue")

caso("Registrar ausência (Figma 221:285)")
at = app()
at.button(key="pt_btn_ausencia").click()
at = at.run()
at.button(key="pt_aus_enviar").click()
at = at.run()
conferir("Escolha o motivo." in texto(at) and not any(c[0] == "ausencia" for c in chamadas), "sem motivo: não envia")
at.selectbox(key="pt_aus_motivo").set_value("consulta")
at.text_area(key="pt_aus_obs").set_value("Consulta marcada")
at.button(key="pt_aus_enviar").click()
at = at.run()
conferir(("ausencia", "Atestado", date.today().isoformat(), date.today().isoformat(), "consulta", "Consulta marcada") in chamadas, "envia tipo, datas, motivo e observação")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
