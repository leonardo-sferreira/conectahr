"""Testes da tela Trajetória (change trajetoria-do-colaborador; Figma 64:42), sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Regras ............. 360 (pares sem nome), selos e textos de prazo, contestação, respostas alteradas, validações
  Tela ............... plano de carreira sem promoção, blocos do Figma, vazios, conta sem ficha e erro
  Modais ............. responder e enviar avaliação, contestar, check-in de meta e progresso do PDI; recusa do backend

Uso (na raiz do repositório):
    python tools/testar_trajetoria.py
"""

import copy
import html as html_lib
import logging
import re
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import notificacoes_modelo  # noqa: E402
import trajetoria_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
chamadas: list[tuple] = []
estado: dict = {}

TRAJETORIA = {
    "sucesso": True, "colaborador_id": 7, "nivel_atual": "l2", "proximo_nivel": "l3",
    "competencias_proximo_nivel": [{"id": 31, "nome": "Liderança técnica"}, {"id": 32, "nome": "Mentoria"}],
    "ciclo": {"id": 4, "nome": "Ciclo 2026.2", "data_fim": "2026-12-15"},
    "autoavaliacao_status": "enviada", "gestor_status": "pendente", "gestor_nome": "Ana Ribeiro", "pares_total": 3, "pares_enviadas": 2,
    "a_preencher": [{"id": 90, "relacao": "par", "status": "pendente", "avaliado_nome": "Bruno Melo", "ciclo_nome": "Ciclo 2026.2"}],
    "recebidas": [
        {"id": 80, "relacao": "par", "nota": 4.25, "comentario": "", "data_avaliacao": "2026-10-10T12:00:00Z", "ciclo_nome": "Ciclo 2026.2",
         "avaliador_nome": None, "contestacao_status": None, "contestacao_resposta": None},
        {"id": 81, "relacao": "gestor", "nota": 3, "comentario": "", "data_avaliacao": "2026-04-02T12:00:00Z", "ciclo_nome": "Ciclo 2026.1",
         "avaliador_nome": "Ana Ribeiro", "contestacao_status": "revisada", "contestacao_resposta": "Nota mantida após revisão."},
    ],
    "metas": [
        {"id": 50, "titulo": "Concluir certificação AWS", "data_prazo": "2026-08-15", "progresso_percentual": 40, "status": "em_andamento"},
        {"id": 51, "titulo": "Liderar migração do módulo de auditoria", "data_prazo": "2099-11-30", "progresso_percentual": 65, "status": "em_andamento"},
    ],
    "pdi": [{"id": 60, "titulo": "Curso de liderança técnica", "data_prazo": "2026-08-01", "progresso_percentual": 20, "status": "em_andamento"}],
    "reconhecimentos": [
        {"id": 70, "created_at": "2026-08-20T10:00:00Z", "mensagem": "Ajudou toda a equipe na virada do fim de mês.", "remetente_nome": "Carlos Souza", "remetente_perfil": "Colaborador"},
        {"id": 71, "created_at": "2026-08-05T10:00:00Z", "mensagem": "Excelente condução da migração de dados.", "remetente_nome": "Ana Ribeiro", "remetente_perfil": "RH"},
    ],
}
VAZIA = {"sucesso": True, "colaborador_id": 7, "nivel_atual": "l5", "proximo_nivel": None, "competencias_proximo_nivel": [], "ciclo": None,
         "autoavaliacao_status": None, "gestor_status": None, "gestor_nome": None, "pares_total": 0, "pares_enviadas": 0,
         "a_preencher": [], "recebidas": [], "metas": [], "pdi": [], "reconhecimentos": []}
FORMULARIO = {"sucesso": True, "avaliacao_id": 90, "status": "em_andamento", "avaliado_nome": "Bruno Melo",
              "competencias": [{"id": 1, "nome": "Comunicação", "descricao": "Clareza com o time."}, {"id": 2, "nome": "Qualidade técnica", "descricao": ""}],
              "respostas": [{"id": 5, "competencia_avaliacao_id": 1, "nota": 3, "comentario": ""}]}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}
# Início (primeira rodada do app), sem rede.
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
# Bloco "Ciclo de metas" (change ciclo-de-metas): sem ciclo aberto aqui; testado em tools/testar_ciclo_metas.py.
api_client.meu_ciclo_metas = lambda token: {"hoje": "2026-10-20", "perguntas_ativas": [], "ciclos": []}
api_client.minha_trajetoria = lambda token: chamadas.append(("ler",)) or _falha_ou("ler", copy.deepcopy(estado.get("dados", TRAJETORIA)))
api_client.competencias_avaliacao = lambda token, aid: chamadas.append(("form", aid)) or _falha_ou("form", copy.deepcopy(FORMULARIO))
api_client.responder_avaliacao = lambda token, aid, cid, nota, com: chamadas.append(("resp", aid, cid, nota, com)) or _falha_ou("resp", {"sucesso": True})
api_client.enviar_avaliacao = lambda token, aid, com: chamadas.append(("enviar", aid, com)) or _falha_ou("enviar", {"sucesso": True})
api_client.contestar_avaliacao = lambda token, aid, motivo: chamadas.append(("contestar", aid, motivo)) or _falha_ou("contestar", {"sucesso": True})
api_client.checkin_meta = lambda token, mid, prog, com, dif, ev: chamadas.append(("checkin", mid, prog, com, dif, ev)) or {"sucesso": True}
api_client.progresso_pdi = lambda token, pid, prog, ev: chamadas.append(("pdi", pid, prog, ev)) or {"sucesso": True}

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


def app(perfil: str = "COLABORADOR", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 3, "nome": "Leonardo Teste", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": 7}
    at.session_state["sessao_validada"] = True
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "trajetoria")
    return at.run()


def abrir(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


def aviso(at: AppTest) -> str:
    return str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else [t.value for t in at.toast])


# ---------------------------------------------------------------------------
caso("Regras (trajetoria_modelo.py)")
l360 = m.linhas_360(TRAJETORIA)
conferir([l["titulo"] for l in l360] == ["Autoavaliação", "Avaliação do gestor", "Avaliação de pares"], "360: autoavaliação, gestor e pares")
conferir(l360[0]["badge"] == "Enviada" and l360[0]["detalhe"] == "Preenchida por você" and l360[1]["detalhe"] == "Ana Ribeiro" and l360[1]["badge"] == "Pendente",
         "autoavaliação enviada; gestor com o nome e pendente")
conferir(l360[2]["detalhe"] == "2 de 3 respondidas" and l360[2]["badge"] == "Pendente", "pares: só a contagem (Figma: '2 de 3 respondidas')")
conferir(m.linhas_360(VAZIA) == [] and m.titulo_360(TRAJETORIA) == "Avaliação 360 — Ciclo 2026.2", "sem ciclo, sem 360; título com o ciclo")
lm = m.linhas_metas(TRAJETORIA["metas"], date(2026, 10, 20))
conferir(lm[0]["detalhe"] == "Prazo era 15/08/2026 · 40% concluído" and (lm[0]["badge"], lm[0]["tom"]) == ("Atrasada", "err"), "meta atrasada como no Figma")
conferir(lm[1]["detalhe"] == "Prazo 30/11/2099 · 65% concluído" and lm[1]["badge"] == "Pendente", "meta no prazo")
lp = m.linhas_pdi(TRAJETORIA["pdi"], date(2026, 7, 1))
conferir(lp[0]["detalhe"] == "Previsto para 01/08/2026 · 20% concluído" and lp[0]["badge"] == "Pendente", "PDI no prazo")
conferir(m.linhas_pdi(TRAJETORIA["pdi"], date(2026, 10, 20))[0]["badge"] == "Atrasado", "PDI atrasado")
lr = m.linhas_recebidas(TRAJETORIA)
conferir(lr[0]["titulo"] == "Avaliação de par" and "Ana" not in lr[0]["detalhe"] and "Nota 4,2" in lr[0]["detalhe"] and lr[0]["pode_contestar"],
         "recebida de par: sem nome, com a nota; pode contestar")
conferir(lr[1]["badge"] == "Contestação revisada" and lr[1]["detalhe"].startswith("Ana Ribeiro"), "recebida do gestor: nome e contestação revisada")
aberta = m.linhas_recebidas({"recebidas": [dict(TRAJETORIA["recebidas"][0], contestacao_status="aberta")]})[0]
conferir(aberta["badge"] == "Contestação em análise" and not aberta["pode_contestar"], "contestação aberta: não contesta de novo")
rc = m.reconhecimentos(TRAJETORIA)
conferir(rc[0]["nome"] == "Carlos Souza" and rc[1]["nome"] == "Ana Ribeiro (RH)" and rc[0]["data"] == "20/08/2026", "reconhecimentos: '(RH)' e a data")
comps = FORMULARIO["competencias"]
conferir(m.respostas_alteradas(comps, FORMULARIO["respostas"], {1: 3, 2: None}, {}) == [], "respostas: nada mudou, nada a gravar")
conferir(m.respostas_alteradas(comps, FORMULARIO["respostas"], {1: 4, 2: 5}, {2: " Ótima "}) == [(1, 4, ""), (2, 5, "Ótima")], "respostas: só as alteradas")
conferir("faltam 1" in m.validar_envio(comps, {1: 3}) and m.validar_envio(comps, {1: 3, 2: 4}) is None and m.validar_envio([], {}) is not None,
         "envio exige nota em todas as competências")
conferir(m.validar_contestacao("abc") is not None and m.validar_contestacao("Nota não reflete as entregas.") is None, "contestação: motivo mínimo")
conferir(notificacoes_modelo.destino({"tipo": "avaliacao_disponivel", "recurso": "avaliacao"}) == "ir_trajetoria", "sino: avaliação disponível abre a Trajetória")

caso("Tela (Figma 64:42)")
at = app()
t = texto(at)
conferir("Trajetória Profissional" in t and "Avaliação 360, metas, PDI e evolução de carreira" in t, "título e subtítulo do Figma")
conferir("Nível atual" in t and "L2" in t and "L3" in t and "Liderança técnica" in t and "Mentoria" in t, "plano de carreira: L2 → L3 com as competências")
conferir("Sem promoção automática — decisão sempre humana" in t and not any("promov" in str(b.label).lower() for b in at.button), "sem nenhuma ação de promover")
conferir("Avaliação 360 — Ciclo 2026.2" in t and "2 de 3 respondidas" in t and "Ana Ribeiro" in t, "360 do ciclo com o gestor e a contagem dos pares")
conferir("Para você avaliar" in t and "Avaliar como par: Bruno Melo" in t and "traj_abrir_responder" in chaves(at), "avaliação a preencher com 'Responder'")
conferir("Avaliações recebidas" in t and "Nota mantida após revisão." in t and "traj_abrir_contestar" in chaves(at), "recebidas, com a resposta do RH e 'Contestar'")
conferir("Metas ativas" in t and "Concluir certificação AWS" in t and "PDI — Plano de Desenvolvimento Individual" in t, "metas e PDI")
conferir("Reconhecimentos recebidos" in t and "Ana Ribeiro (RH)" in t and "Carlos Souza" in t, "reconhecimentos com quem enviou")
conferir(chamadas.count(("ler",)) == 1, "uma leitura só (minha_trajetoria)")
at = app(dados=VAZIA)
t = texto(at)
conferir("Você está no nível mais alto" in t and "Nenhum ciclo de avaliação em andamento." in t and "Nenhuma meta ativa." in t
         and "Nenhuma ação de PDI em andamento." in t and "Nenhum reconhecimento recebido ainda." in t, "estados vazios de cada bloco")
conferir(not {"traj_abrir_responder", "traj_abrir_contestar", "traj_abrir_checkin", "traj_abrir_pdi"} & chaves(at), "sem itens, sem ações")
at = app(erro_ler=ApiError("Nao existe um colaborador vinculado a esta conta.", 404))
conferir("não tem ficha de colaborador" in texto(at) and "Metas ativas" not in texto(at), "conta sem ficha: aviso no lugar dos blocos")
at = app(erro_ler=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at), "erro do backend aparece")

caso("Modal: responder e enviar avaliação")
at = abrir(app(), "traj_abrir_responder")
conferir(("form", 90) in chamadas and at.radio(key="traj_nota_90_1").value == 3 and at.radio(key="traj_nota_90_2").value is None,
         "abre com as competências e a nota já salva")
at.radio(key="traj_nota_90_2").set_value(4)
at.button(key="traj_resp_salvar").click()
at = at.run()
conferir(("resp", 90, 2, 4, "") in chamadas and not any(c[0] == "enviar" for c in chamadas) and "traj_modal" not in at.session_state
         and "continuar depois" in aviso(at), "Salvar grava só a resposta nova e fecha")
at = abrir(app(), "traj_abrir_responder")
at.button(key="traj_resp_enviar").click()
at = at.run()
conferir("faltam 1" in texto(at) and not any(c[0] in ("resp", "enviar") for c in chamadas), "Enviar sem todas as notas: mensagem, sem chamar a API")
at.radio(key="traj_nota_90_2").set_value(5)
at.button(key="traj_resp_enviar").click()
at = at.run()
conferir("Marque a confirmação" in texto(at) and not any(c[0] == "enviar" for c in chamadas), "Enviar pede a confirmação de que é definitivo")
at.checkbox(key="traj_confirma_90").check()
at.text_area(key="traj_geral_90").set_value("Bom colega de time.")
at.button(key="traj_resp_enviar").click()
at = at.run()
conferir(("resp", 90, 2, 5, "") in chamadas and ("enviar", 90, "Bom colega de time.") in chamadas and "Avaliação enviada." in aviso(at), "Enviar grava e envia")
at = abrir(app(erro_enviar=ApiError("Esta avaliacao ja foi enviada ou cancelada.", 400)), "traj_abrir_responder")
at.radio(key="traj_nota_90_2").set_value(5)
at.checkbox(key="traj_confirma_90").check()
at.button(key="traj_resp_enviar").click()
at = at.run()
conferir("ja foi enviada" in texto(at) and at.session_state["traj_modal"] == "responder", "recusa do backend no modal, que continua aberto")
at = abrir(app(erro_form=ApiError("Somente o avaliador designado pode responder esta avaliacao.", 403)), "traj_abrir_responder")
conferir("Somente o avaliador designado" in texto(at), "competências recusadas: mensagem do backend")

caso("Modal: contestar")
at = abrir(app(), "traj_abrir_contestar")
conferir([o.split(" — ")[0] for o in at.selectbox(key="traj_cont_avaliacao").options] == ["Avaliação de par", "Avaliação do gestor"]
         and "Ciclo 2026.2" in at.selectbox(key="traj_cont_avaliacao").options[0], "oferece as avaliações sem contestação aberta, com ciclo e nota")
at.selectbox(key="traj_cont_avaliacao").set_value(80)
at.text_area(key="traj_cont_motivo").set_value("ok")
at.button(key="traj_cont_ok").click()
at = at.run()
conferir("pelo menos 5 caracteres" in texto(at) and not any(c[0] == "contestar" for c in chamadas), "motivo curto: mensagem, sem chamar a API")
at.text_area(key="traj_cont_motivo").set_value("A nota não considera as entregas do trimestre.")
at.button(key="traj_cont_ok").click()
at = at.run()
conferir(("contestar", 80, "A nota não considera as entregas do trimestre.") in chamadas and "O RH vai revisar" in aviso(at), "contestação enviada")

caso("Modais: check-in de meta e progresso do PDI")
at = abrir(app(), "traj_abrir_checkin")
at.selectbox(key="traj_ck_meta").set_value(50)
at = at.run()
conferir(at.number_input(key="traj_ck_prog_50").value == 40, "check-in abre com o progresso atual da meta")
at.number_input(key="traj_ck_prog_50").set_value(60)
at.text_area(key="traj_ck_com").set_value("Simulados feitos.")
at.button(key="traj_ck_ok").click()
at = at.run()
conferir(("checkin", 50, 60, "Simulados feitos.", "", "") in chamadas and "60% concluído" in aviso(at), "check-in registrado")
at = abrir(app(), "traj_abrir_pdi")
conferir(at.selectbox(key="traj_pdi_acao").value == 60 and at.number_input(key="traj_pdi_prog_60").value == 20, "PDI com uma ação: já vem escolhida")
at.number_input(key="traj_pdi_prog_60").set_value(50)
at.button(key="traj_pdi_ok").click()
at = at.run()
conferir(("pdi", 60, 50, "") in chamadas and "50%" in aviso(at), "progresso do PDI salvo")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
