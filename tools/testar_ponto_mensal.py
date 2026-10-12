"""Testes do espelho de ponto mensal no REP-P (change ponto-rep-p-e-ferias-clt, tarefas 4.2 a 4.4; Figma 464:826,
465:856 e 465:894), sem navegador e sem rede.

Cobre, caso a caso, o fluxo de `docs/fluxos/ponto-mensal.md`: os pares de marcações da ARP com a incluída "(I)" e a
desconsiderada "(D)"; a situação de cada dia (marcação, hoje, férias, ausência, feriado e ponto facultativo, folga,
sem registro); os dias antes da admissão e os futuros em branco; o cabeçalho do art. 84 e o CSV; o pedido de correção
pela seleção da linha da planilha (inclusão e desconsideração); o prazo do RH (tarefa 79).

Uso (na raiz do repositório):
    python tools/testar_ponto_mensal.py
"""

import csv
import html as html_lib
import io
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
import ponto_mensal_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
BR = timezone(timedelta(hours=-3))
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


def ms(d: date, h: int, mi: int = 0) -> int:
    return int(datetime.combine(d, time(h, mi), tzinfo=BR).timestamp() * 1000)


_nsr = [1000]


def mc(mid: int, d: date, h: int, mi: int = 0) -> dict:
    _nsr[0] += 1
    return {"id": mid, "nsr": _nsr[0], "data": d.isoformat(), "data_hora_marcacao": ms(d, h, mi), "data_hora_marcacao_txt": f"{d.isoformat()}T{h:02d}:{mi:02d}:00-0300"}


def jornada(base_id: int, d: date, horarios=((8, 0), (12, 0), (13, 0), (17, 30))) -> list[dict]:
    return [mc(base_id + i, d, h, mi) for i, (h, mi) in enumerate(horarios)]


def reg(rid: int, d: date, status: str = "Completo", horas: float = 8.5) -> dict:
    return {"id": rid, "data": d.isoformat(), "status": status, "horas_trabalhadas": horas}


# ---------------------------------------------------------------------------
caso("Marcações e tratamentos de um dia")
D = date(2026, 10, 7)
marcs = [mc(1, D, 8, 1), mc(2, D, 8, 3), mc(3, D, 12, 2), mc(4, D, 13, 0), mc(5, D, 17, 30)]
trats = [{"id": 1, "data": D.isoformat(), "tipo": "desconsideracao", "marcacao_id": 1, "motivo": "Marquei duas vezes"},
         {"id": 2, "data": D.isoformat(), "tipo": "inclusao", "data_hora": ms(D, 18, 5), "motivo": "Saída esquecida"},
         {"id": 3, "data": D.isoformat(), "tipo": "inclusao", "data_hora": ms(D, 19, 0), "motivo": "Errado"},
         {"id": 4, "data": D.isoformat(), "tipo": "inclusao", "anula_tratamento_id": 3, "data_hora": ms(D, 19, 0), "motivo": "Desfaz o 3"}]
validas, desc = m.batidas_do_dia(marcs, trats)
conferir([m.texto_batida(b) for b in validas] == ["08:03", "12:02", "13:00", "17:30", "18:05 (I)"], "válidas em ordem, a incluída com (I); o tratamento desfeito não vale")
conferir([m.texto_desconsiderada(b) for b in desc] == ["08:01 (D)"], "a desconsiderada sai dos pares, com (D)")
conferir(abs(m.horas_dos_pares(validas[:4]) - (3 + 59 / 60 + 4.5)) < 1e-9, "horas pelos pares completos")

caso("Situação de cada dia (outubro de 2026, hoje = 15/10)")
H = date(2026, 10, 15)
d = lambda n: date(2026, 10, n)  # noqa: E731
marcacoes = jornada(10, d(1)) + jornada(20, d(2))[:3] + jornada(130, d(13)) + jornada(140, d(14))[:3] + jornada(150, d(15))[:3]
tratamentos = [{"id": 9, "data": d(14).isoformat(), "tipo": "inclusao", "data_hora": ms(d(14), 18, 5), "motivo": "Ficou até mais tarde"}]
regs = [reg(1, d(1)), reg(2, d(2), "Incompleto", 4), reg(13, d(13)), reg(14, d(14), "Ajustado", 9.08), reg(15, d(15), "Aberto", 4)]
aus = [{"tipo": "Atestado", "data_inicio": "2026-10-06", "data_fim": "2026-10-06", "status": "Aprovada"},
       {"tipo": "Falta", "data_inicio": "2026-10-07", "data_fim": "2026-10-07", "status": "Pendente"},
       {"tipo": "Falta", "data_inicio": "2026-10-05", "data_fim": "2026-10-05", "status": "Rejeitada"}]
cor = [{"id": 70, "registro_ponto_id": 13, "tipo": "desconsideracao", "marcacao_id": 132, "status": "pendente"},
       {"id": 71, "registro_ponto_id": 14, "tipo": "inclusao", "valor_solicitado": ms(d(14), 7, 50), "status": "rejeitada",
        "motivo_decisao": "Não confere com a portaria.", "data_decisao": "2026-10-14T12:00:00Z"}]
fer = [{"data_inicio": "2026-10-08", "data_fim": "2026-10-09", "status": "Aprovada"}, {"data_inicio": "2026-10-10", "data_fim": "2026-10-10", "status": "Pendente"}]
feri = [{"data": "2026-10-12", "nome": "Nossa Senhora Aparecida", "abrangencia": "nacional", "tipo": "feriado"},
        {"data": "2026-10-28", "nome": "Dia do Servidor Público", "abrangencia": "nacional", "tipo": "ponto_facultativo"}]
linhas = m.espelho_do_mes(regs, aus, cor, fer, feri, 2026, 10, H, "2026-10-01", marcacoes=marcacoes, tratamentos=tratamentos)
por = {l["data"].day: l for l in linhas}
conferir(len(linhas) == 31 and all(por[n]["em_branco"] and por[n]["situacao"] == "" for n in range(16, 32)), "todos os dias do mês; os futuros em branco")
conferir(por[1]["status"] == "COMPLETO" and [b["hora"] for b in por[1]["batidas"]] == ["08:00", "12:00", "13:00", "17:30"] and por[1]["trabalhado"] == "8h30"
         and por[1]["acao"] == "corrigir", "dia completo: os pares, as horas e a correção")
conferir(por[2]["situacao"] == "INCOMPLETO · corrigir" and m.situacao_curta(por[2]) == "Incompleto (falta a saída)", "dia passado incompleto, com 'corrigir' e 'falta a saída'")
conferir(por[3]["situacao"] == "Folga" and por[3]["acao"] == "corrigir", "sábado sem marcação: folga, com correção")
conferir(por[5]["status"] == "FALTA INJUSTIFICADA" and "recusada pelo RH" in por[5]["nota"], "ausência recusada: falta injustificada")
conferir(por[6]["situacao"] == "Atestado" and por[6]["acao"] is None, "atestado aprovado: sem correção")
conferir(por[7]["situacao"] == "Ausência em análise" and por[7]["acao"] is None, "ausência pendente: em análise, sem correção")
conferir(por[8]["situacao"] == "Férias" and por[9]["situacao"] == "Férias" and por[10]["situacao"] == "Folga", "férias aprovadas; as pendentes não contam")
conferir(por[12]["situacao"] == "Feriado — Nossa Senhora Aparecida" and por[12]["acao"] == "corrigir", "feriado com o nome, com correção para quem trabalhou")
conferir(por[13]["nota"] == "Em análise: desconsiderar 13:00" and [b["hora"] for b in m.desconsideraveis(por[13])] == ["08:00", "12:00", "17:30"],
         "pedido em análise: aviso, e a marcação sai da desconsideração")
conferir(por[14]["situacao"] == "AJUSTADO" and por[14]["batidas"][-1]["incluida"] and "Correção recusada (inclusão de 07:50): Não confere com a portaria." == por[14]["nota"],
         "dia ajustado com a incluída; o motivo da recusa aparece")
conferir(por[15]["situacao"] == "HOJE · em jornada" and por[15]["acao"] is None, "hoje em jornada, sem correção")
D11 = date(2026, 10, 11)
impar = m.espelho_do_mes([reg(11, D11, "Ajustado", 9)], [], [], [], [], 2026, 10, H, "2026-10-01",
                         marcacoes=[mc(900, D11, 18, 3)],
                         tratamentos=[{"id": 31, "data": D11.isoformat(), "tipo": "inclusao", "data_hora": ms(D11, 9, 0), "motivo": "Entrada"},
                                      {"id": 32, "data": D11.isoformat(), "tipo": "inclusao", "data_hora": ms(D11, 18, 0), "motivo": "Saida"}])[10]
conferir(impar["status"] == "INCOMPLETO" and impar["situacao"] == "INCOMPLETO · corrigir" and impar["acao"] == "corrigir"
         and [m.texto_batida(b) for b in impar["batidas"]] == ["09:00 (I)", "18:00 (I)", "18:03"],
         "tratamento com marcação sem par: INCOMPLETO, mesmo gravado como Ajustado")
so_feri = {l["data"].day: l for l in m.espelho_do_mes([], [], [], [], feri, 2026, 10, date(2026, 10, 31), "2026-10-01", marcacoes=[])}
conferir(so_feri[28]["situacao"] == "Ponto facultativo — Dia do Servidor Público" and so_feri[28]["status"] != "SEM REGISTRO", "ponto facultativo pelo tipo, sem falta")
so_sem = {l["data"].day: l for l in m.espelho_do_mes([], [], [], [], [], 2026, 10, H, "2026-10-01", marcacoes=[])}
conferir(so_sem[15]["situacao"] == "HOJE · sem marcação" and so_sem[5]["situacao"] == "Sem registro", "hoje sem marcação; dia útil sem nada no mês corrente: sem registro")
fechado = {l["data"].day: l for l in m.espelho_do_mes([], [], [], [], [], 2026, 9, H, "2026-09-01", marcacoes=[])}
conferir(fechado[1]["situacao"] == "Falta injustificada" and fechado[5]["situacao"] == "Folga", "mês encerrado: dia útil sem nada vira falta injustificada")

caso("Início na admissão (tarefa 4.3)")
adm = {l["data"].day: l for l in m.espelho_do_mes([], [], [], [], [], 2026, 10, date(2026, 10, 20), "2026-10-15", marcacoes=[])}
conferir(all(adm[n]["em_branco"] and adm[n]["situacao"] == "" and adm[n]["acao"] is None for n in range(1, 15)), "admissão em 15/10: dias 1 a 14 em branco, sem situação")
conferir(adm[15]["situacao"] == "Sem registro" and m.resumo_do_mes(list(adm.values()))["faltas_injustificadas"] == 0, "a partir do dia 15 conta; nenhuma falta antes")
conferir(m.primeiro_dia("2026-09-01", [{"data": "2025-12-03"}]) == date(2026, 9, 1), "o início é a admissão, mesmo com registro anterior")
conferir(m.primeiro_dia(None, [{"data": "2025-12-03"}]) == date(2025, 12, 3), "sem admissão no cadastro, o primeiro registro")
conferir(m.meses_disponiveis("2026-08-20", [], H) == [(2026, 10), (2026, 9), (2026, 8)] and len(m.meses_disponiveis("2020-01-01", [], H)) == 82, "meses da admissão até hoje, sem limite")

caso("Resumo, planilha e legenda")
r = m.resumo_do_mes(linhas)
conferir(r == {"horas": "34h05", "dias_trabalhados": 5, "sem_registro": 1, "faltas_injustificadas": 1, "atestados": 1, "em_analise": 1, "saldo": None,
             "positivas": None, "negativas": None},
         f"resumo do mês, sem jornada: sem saldo ({r})")
conferir(m.colunas_planilha(2) == ["Data", "Dia", "Ent. 1", "Saí. 1", "Ent. 2", "Saí. 2", "Desconsideradas", "Horas", "Situação"], "colunas da planilha")
conferir(m.pares_do_mes(linhas) == 2 and m.linhas_planilha(linhas)[13][:6] == ["14/10/2026", "qua", "08:00", "12:00", "13:00", "18:05 (I)"],
         "data completa (dd/mm/aaaa); a incluída entra no par, em ordem")
conferir(m.pares_do_mes([{"batidas": [{}] * 5}]) == 3, "quinta marcação abre o 3º par")
dia7 = m.espelho_do_mes([reg(7, D, "Ajustado", 9.5)], [], [], [], [], 2026, 10, H, "2026-10-01", marcacoes=marcs[:4], tratamentos=trats[:2])[6]
conferir(m.linhas_planilha([dia7])[0][-3:] == ["08:01 (D)", "9h30", "AJUSTADO"] and m.marcacoes_texto(dia7) == "08:01 (D) · 08:03 · 12:02 · 13:00 · 18:05 (I)",
         "desconsiderada na coluna própria; texto do dia com (I) e (D)")
conferir(m.legenda("2026-10-05").endswith("antes da admissão (05/10/2026) ou dias que ainda não chegaram"), "legenda com a admissão")
conferir(m.descricao_dia(por[2]) == "sexta-feira, 02/10 — Incompleto (falta a saída)", "descrição do dia selecionado")
conferir(m.linha_selecionada(linhas, [1])["data"] == d(2) and m.linha_selecionada(linhas, [20]) is None and m.linha_selecionada(linhas, []) is None,
         "seleção da planilha: linha em branco não conta")
ajuste = m.valores_ajuste(linhas, lambda l: l["acao"] == "corrigir")
conferir(ajuste[1] is False and ajuste[20] is None and len(ajuste) == len(linhas), "coluna Ajuste: caixa no dia que aceita correção, vazia no dia em branco")

caso("Saldo do dia e descanso (design D13 e D14, tarefa 9.4)")
conferir((m.saldo_do_dia(7.5, 480, True), m.saldo_do_dia(6 + 20 / 60, 360, True), m.saldo_do_dia(7 + 52 / 60, 480, True), m.saldo_do_dia(4, 480, False),
          m.saldo_do_dia(8 + 11 / 60, 480, True)) == (-30, 20, 0, 240, 11), "cenários da spec: 7h30 = -30, 6h20 em 6h = +20, 7h52 = 0, sábado 4h = +240, 8h11 = +11")
conferir((m.minutos_texto(-30, True), m.minutos_texto(20, True), m.minutos_texto(0, True), m.minutos_texto(540)) == ("-0h30", "+0h20", "0h00", "9h00"), "saldo com sinal")
conferir(m.texto_descanso(540, 660) == "Descanso de 9h00 (mínimo 11h)", "selo do descanso")
clt = m.espelho_do_mes(regs + [dict(reg(16, d(16)), saldo_minutos=-30, descanso_minutos=540)], aus, cor, fer, feri, 2026, 10, date(2026, 10, 20), "2026-10-01",
                       marcacoes=marcacoes + jornada(160, d(16)), tratamentos=tratamentos, jornada_horas=8, descanso_minimo=660)
pc = {l["data"].day: l for l in clt}
conferir(pc[1]["saldo"] == 30 and pc[2]["saldo"] == -240, "dia gravado antes do saldo: a conta da tela (8h30 = +30; incompleto de 4h = -4h00)")
conferir(pc[16]["saldo"] == -30 and pc[16]["situacao"] == "COMPLETO · Descanso de 9h00 (mínimo 11h)" and pc[16]["descanso"] == 540,
         "saldo gravado pelo backend vale; descanso abaixo do mínimo no selo (cenário da spec)")
conferir(pc[5]["saldo"] == -480 and pc[3]["saldo"] == 0 and pc[6]["saldo"] == 0 and pc[8]["saldo"] == 0 and pc[12]["saldo"] == 0 and pc[7]["saldo"] is None
         and pc[19]["saldo"] == -480, "falta = menos a jornada; folga, atestado, férias e feriado = 0; ausência em análise sem saldo; sem registro = menos a jornada")
conferir(pc[20]["saldo"] is None and pc[21]["saldo"] is None, "hoje e os dias futuros sem saldo")
rc = m.resumo_do_mes(clt)
conferir(rc["saldo"] == m.minutos_texto(sum(l["saldo"] or 0 for l in clt), True), "saldo do mês é a soma dos dias")
conferir(rc["positivas"] == m.minutos_texto(sum(l["saldo"] for l in clt if (l["saldo"] or 0) > 0), True) and rc["positivas"].startswith("+")
         and rc["negativas"] == m.minutos_texto(sum(l["saldo"] for l in clt if (l["saldo"] or 0) < 0)) and rc["negativas"].startswith("-"),
         f"horas positivas e negativas separadas ({rc['positivas']} / {rc['negativas']})")
cols = m.colunas_planilha(2, True)
conferir(cols[-3:] == ["Horas", "Saldo", "Situação"] and m.linhas_planilha(clt)[15][-3:] == ["8h30", "-0h30", "COMPLETO · Descanso de 9h00 (mínimo 11h)"],
         "coluna Saldo entre Horas e Situação")
conferir(m.legenda(None, True).endswith("(diferença de até 10 min no dia não conta)") and "Saldo" in m.csv_do_mes(clt).decode("utf-8-sig").splitlines()[0], "legenda e CSV com o saldo")
conferir(not m.tem_saldo(linhas) and "Saldo" not in m.colunas_planilha(2), "PJ (sem jornada): sem a coluna Saldo (cenário da spec)")
BRT = m.para_brasilia(ms(d(16), 22)).tzinfo
ontem22 = [mc(800, d(15), 8), mc(801, d(15), 22)]
aviso = m.aviso_descanso(ontem22, [], datetime(2026, 10, 16, 7, 0, tzinfo=BRT), 660)
conferir(aviso and aviso["descanso"] == 540 and aviso["falta"] == 120 and m.quando(aviso["ultima"], d(16)) == "Ontem, 15/10, às 22:00",
         "aviso: saiu às 22:00, marca às 07:00, faltam 2h00 (cenário da spec)")
conferir(m.aviso_descanso(ontem22, [], datetime(2026, 10, 16, 9, 0, tzinfo=BRT), 660) is None, "11h cumpridas: sem aviso")
conferir(m.aviso_descanso(ontem22 + [mc(802, d(16), 6)], [], datetime(2026, 10, 16, 7, 0, tzinfo=BRT), 660) is None, "já marcou hoje: sem aviso (só na primeira do dia)")
conferir(m.aviso_descanso(ontem22, [], datetime(2026, 10, 16, 7, 0, tzinfo=BRT), None) is None, "PJ: sem aviso")
desc22 = [{"id": 5, "data": d(15).isoformat(), "tipo": "desconsideracao", "marcacao_id": 801}]
conferir(m.aviso_descanso(ontem22, desc22, datetime(2026, 10, 16, 7, 0, tzinfo=BRT), 660) is None, "a desconsiderada não conta: vale a última válida (08:00)")

caso("Cabeçalho do art. 84 e CSV (tarefa 4.4)")
REP = {"empregador": {"razao_social": "ConectaRH Tecnologia Ltda (ficticio)", "tipo_identificador": "cnpj", "identificador": "12345678000190",
                      "local_prestacao": "Av. Paulista, 1000 - Sao Paulo/SP", "cno_caepf": ""},
       "trabalhador": {"nome": "Leonardo dos Santos", "cpf": "12345678909", "data_admissao": "2026-10-05", "cargo": "Analista de RH"},
       "jornada": {"horas_diarias": 8, "horas_semanais": 44, "intervalo_minutos": 60}}
cab = m.cabecalho_espelho(REP, 2026, 10, datetime(2026, 10, 14, 13, 5))
campos = dict(cab["campos"])
conferir(cab["emissao"] == "Emitido em 14/10/2026 13:05 · Período 01/10/2026 a 31/10/2026", "emissão e período")
conferir(campos["Empregador"].startswith("ConectaRH") and campos["CNPJ"] == "12.345.678/0001-90" and campos["Local"].startswith("Av. Paulista"), "empregador, CNPJ e local")
conferir(campos["Trabalhador"] == "Leonardo dos Santos" and campos["CPF"] == "123.456.789-09" and campos["Admissão"] == "05/10/2026" and campos["Cargo"] == "Analista de RH",
         "trabalhador com CPF, admissão e cargo")
conferir(campos["Horário contratual"] == "8h00 por dia · 44h00 por semana · intervalo de 1h00" and m.horario_contratual(None) == "Não informado", "horário contratual pela jornada")
conteudo = m.csv_do_mes(linhas, cab)
texto_csv = conteudo.decode("utf-8-sig")
tabela = list(csv.reader(io.StringIO(texto_csv), delimiter=";"))
conferir(conteudo.startswith("﻿".encode()) and tabela[0] == ["Espelho de ponto eletrônico"] and tabela[1][0].startswith("Emitido em"), "CSV com BOM, título e emissão")
conferir(["CNPJ", "12.345.678/0001-90"] in tabela and ["CPF", "123.456.789-09"] in tabela and ["Admissão", "05/10/2026"] in tabela and ["Cargo", "Analista de RH"] in tabela
         and ["Horário contratual", "8h00 por dia · 44h00 por semana · intervalo de 1h00"] in tabela, "CSV com os campos do cabeçalho")
cab_tab = next(i for i, l in enumerate(tabela) if l and l[0] == "Data")
conferir(tabela[cab_tab][-3:] == ["Situação", "Observação", "NSR"] and tabela[cab_tab + 1][0] == "01/10/2026"
         and tabela[cab_tab + 1][-1].split() == [str(b["nsr"]).rjust(9, "0") for b in por[1]["batidas"]],
         "CSV com a planilha, a observação e o NSR de cada marcação")
conferir(tabela[cab_tab + 14][5] == "18:05 (I)" and tabela[-1][0].startswith("(I) incluída"), "CSV com (I) e a legenda")

caso("Prazo para pedir correção (tarefa 79)")
conferir(m.limite_prazo(H, None) is None and m.limite_prazo(H, 5) == date(2026, 10, 10) and m.texto_prazo(1) == "1 dia", "limite e texto do prazo")
com_prazo = {l["data"].day: l for l in m.espelho_do_mes(regs, aus, cor, fer, feri, 2026, 10, H, "2026-10-01", prazo_dias=3, marcacoes=marcacoes, tratamentos=tratamentos)}
conferir(com_prazo[1]["acao"] is None and m.NOTA_PRAZO in com_prazo[1]["nota"] and com_prazo[2]["situacao"] == "INCOMPLETO", "fora do prazo: sem correção, com o aviso")
conferir(com_prazo[12]["acao"] == "corrigir" and com_prazo[14]["acao"] == "corrigir" and com_prazo[13]["nota"].startswith("Em análise"), "dentro do prazo: com correção; pedidos em análise visíveis")
conferir(m.aviso_prazo(list(com_prazo.values()), H, 3).startswith("Dias antes de 12/10/2026") and m.aviso_prazo(list(com_prazo.values()), H, None) == "", "aviso acima da planilha")

# ---------------------------------------------------------------------------
HOJE = datetime.now(BR).date()
ANT = HOJE.replace(day=1) - timedelta(days=1)  # último dia do mês anterior
dias_uteis = [x for x in (ANT.replace(day=n) for n in range(1, ANT.day + 1)) if x.weekday() < 5]
D_REG, D_SEM = dias_uteis[0], dias_uteis[1]
IDX_REG, IDX_SEM = D_REG.day - 1, D_SEM.day - 1
chamadas: list[tuple] = []
estado: dict = {}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


MARC_REG = jornada(500, D_REG)
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}
api_client.prazo_correcao = lambda token: _falha_ou("prazo", {"prazo_dias": estado.get("prazo")})
api_client.central_de_tarefas = lambda token: {}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.meu_ponto = lambda token: {"registros": [reg(50, D_REG)], "marcacoes": MARC_REG, "tratamentos": []}
api_client.comprovantes_ponto = lambda token: {"marcacoes": [], **REP}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 1}
api_client.minhas_correcoes_ponto = lambda token: {"correcoes": [{"id": 80, "registro_ponto_id": 50, "tipo": "desconsideracao", "marcacao_id": 503, "status": "pendente"}]}
api_client.minhas_ausencias = lambda token: {"ausencias": []}
api_client.minhas_ferias = lambda token: {"ferias": []}
api_client.calendario = lambda token: _falha_ou("calendario", {"feriados": []})
api_client.meu_perfil_colaborador = lambda token: {"colaborador": {"data_admissao": (ANT.replace(day=1) - timedelta(days=40)).isoformat()}}
api_client.pedir_correcao_ponto = lambda token, data, tipo, just, marcacao_id=None, data_hora_ms=None: (
    chamadas.append(("pedido", data, tipo, just, marcacao_id, data_hora_ms)) or _falha_ou("pedido", {"sucesso": True}))


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def pedir(at: AppTest, indice: int) -> AppTest:
    """Marca "Ajuste" no dia (o AppTest não edita o st.data_editor: põe direto o estado que a marca grava)."""
    at.session_state["modal_ponto"] = ("pedido", date(ANT.year, ANT.month, indice + 1).isoformat())
    return at.run()


def app(**extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Leonardo dos Santos", "email": "leo@empresa.com", "perfil": "COLABORADOR", "colaborador_id": 9}
    at.session_state["sessao_validada"] = True
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "ponto")
    at = at.run()
    at.button_group(key="pt_visao").set_value("Mês")
    at = at.run()
    at.selectbox(key="pt_mes_ano").set_value((ANT.year, ANT.month))
    return at.run()


caso("Tela: mês anterior (Figma 464:826)")
at = app()
t = texto(at)
conferir(not at.exception, "a tela abre sem erro")
conferir("Espelho de ponto eletrônico" in t and "12.345.678/0001-90" in t and "123.456.789-09" in t and "Analista de RH" in t and "8h00 por dia" in t, "cabeçalho do art. 84")
conferir("Horas no mês" in t and "Horas positivas" in t and "Horas negativas" in t and "Atestados" not in t and "Correções em análise: 1" in t,
         "resumo com horas positivas e negativas, sem atestados")
df = at.dataframe[0].value
conferir(len(df) == ANT.day and list(df.columns)[:4] == ["Data", "Dia", "Ent. 1", "Saí. 1"] and df.iloc[IDX_REG]["Ent. 1"] == "08:00"
         and df.iloc[IDX_SEM]["Situação"] == "Falta injustificada", "planilha com todos os dias, os pares e a falta em mês encerrado")
conferir(any(b.key == "pt_baixar_mes" for b in at.get("download_button")) and 'Marque "Ajuste" no fim da linha' in t, "baixar CSV e a orientação do ajuste")
conferir(list(df.columns)[-1] == "Ajuste" and str(df.iloc[IDX_SEM]["Ajuste"]) == "False", "coluna Ajuste no fim da linha")

caso("Tela: pedir a inclusão num dia sem marcação (Figma 465:856)")
at = pedir(at, IDX_SEM)
conferir("Falta injustificada" in texto(at), "o pedido mostra a situação do dia")
conferir([o for o in at.radio(key="pt_ped_tipo").options] == ["Incluir uma marcação que faltou"], "sem marcação no dia: só a inclusão")
at.button(key="pt_ped_enviar").click()
at = at.run()
conferir("Informe o horário da marcação que faltou." in texto(at) and not chamadas, "sem horário: não envia")
at.time_input(key="pt_ped_hora").set_value(time(8, 5))
at.text_area(key="pt_ped_motivo").set_value("Esqueci de marcar a entrada.")
at.button(key="pt_ped_enviar").click()
at = at.run()
conferir(("pedido", D_SEM.isoformat(), "inclusao", "Esqueci de marcar a entrada.", None, ms(D_SEM, 8, 5)) in chamadas and "modal_ponto" not in at.session_state,
         "envia a data, a inclusão e o horário de Brasília; o modal fecha")

caso("Tela: pedir a desconsideração (Figma 465:894)")
at = pedir(app(), IDX_REG)
at.radio(key="pt_ped_tipo").set_value("desconsideracao")
at = at.run()
opcoes = at.selectbox(key="pt_ped_marcacao").options
conferir(len(opcoes) == 3 and not any("17:30" in o for o in opcoes), "a marcação já em análise não pode ser pedida de novo")
at.selectbox(key="pt_ped_marcacao").set_value(500)
at.text_area(key="pt_ped_motivo").set_value("Marquei duas vezes.")
at.button(key="pt_ped_enviar").click()
at = at.run()
conferir(("pedido", D_REG.isoformat(), "desconsideracao", "Marquei duas vezes.", 500, None) in chamadas, "envia a marcação a desconsiderar")
at = pedir(app(erro_pedido=ApiError("O prazo para pedir correcao deste dia acabou.", 400)), IDX_SEM)
at.time_input(key="pt_ped_hora").set_value(time(17, 0))
at.text_area(key="pt_ped_motivo").set_value("Saí às 17h.")
at.button(key="pt_ped_enviar").click()
at = at.run()
conferir("prazo para pedir correcao" in texto(at) and "modal_ponto" in at.session_state, "recusa do backend no modal, que continua aberto")

caso("Tela: prazo e falhas parciais")
at = app(prazo=1)
t = texto(at)
conferir(at.dataframe[0].value.iloc[IDX_SEM]["Ajuste"] is None and "passaram do prazo de 1 dia" in t and "Prazo para pedir correção: 1 dia" in t, "fora do prazo: sem a caixa de ajuste, com o aviso")
at = app(erro_calendario=ApiError("Erro inesperado.", 500))
conferir(not at.exception and at.dataframe[0].value.iloc[IDX_SEM]["Situação"] == "Falta injustificada", "sem o calendário, o mês aparece do mesmo jeito")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
