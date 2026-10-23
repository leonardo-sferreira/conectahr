"""Testes da tela Regras e Conformidade (change tela-de-regras; Figma 287:884 e 288:886), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras de apresentação, selos e
ações por situação (autoaprovação, registro no MTE, conflito), filtros, novo instrumento, nova regra (vai para a
simulação), simulação (regra atual da matriz, conflito, definir prioridade, enviar), aprovar com justificativa, rejeitar
com motivo, nova versão, histórico e a tela só para RH e Admin.

Uso (na raiz do repositório):
    python tools/testar_regras.py
"""

import copy
import html as html_lib
import logging
import re
import sys
from datetime import date, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import regras_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
EU, OUTRA = 10, 11
chamadas: list[tuple] = []
estado: dict = {}

INSTRUMENTOS = [
    {"id": 1, "tipo": "acordo_coletivo", "titulo": "Acordo Coletivo 2026", "entidade_responsavel": "Sindicato dos Trabalhadores", "numero_solicitacao_mediador": "MR12345/2026",
     "numero_registro_mte": "AB123456/2026", "numero_processo_mte": "46000.000001/2026-01", "data_registro": "2026-01-05", "documento_url": "https://ex.com/a.pdf",
     "data_inicio": "2026-01-01", "data_fim": "2026-12-31", "status": "vigente", "criado_por_user_id": OUTRA},
    {"id": 2, "tipo": "convencao_coletiva", "titulo": "Convenção Coletiva Regional", "entidade_responsavel": "Federação", "numero_solicitacao_mediador": "MR99999/2026",
     "numero_registro_mte": None, "numero_processo_mte": None, "data_registro": None, "documento_url": "https://ex.com/c.pdf",
     "data_inicio": "2026-09-01", "data_fim": None, "status": "pendente_aprovacao", "criado_por_user_id": OUTRA},
    {"id": 3, "tipo": "termo_aditivo", "titulo": "Termo aditivo — banco de horas TI", "entidade_responsavel": "Sindicato", "numero_solicitacao_mediador": "MR23456/2026",
     "numero_registro_mte": "AB000001/2026", "numero_processo_mte": "x", "data_registro": "2026-10-01", "documento_url": "https://ex.com/t.pdf",
     "data_inicio": "2026-10-01", "data_fim": "2026-12-31", "status": "pendente_aprovacao", "criado_por_user_id": EU},
    {"id": 4, "tipo": "regime_especial", "titulo": "Regime especial — trabalho noturno TI", "entidade_responsavel": "Empresa", "documento_url": "https://ex.com/r.pdf",
     "data_inicio": "2025-01-01", "data_fim": "2025-12-31", "status": "expirado", "criado_por_user_id": OUTRA},
]
CONFLITO = {"id": 30, "parametro": "antecedencia_ferias", "prioridade": 2, "valor_novo": "20", "abrangencia": "cargo", "cargo_id": 5, "versao": 1,
            "data_inicio": "2026-01-01", "data_fim": None, "pessoas_em_comum": 4}
REGRAS = [
    {"id": 20, "instrumento_normativo_id": 1, "parametro": "horas_diarias", "valor_anterior": "8", "valor_novo": "12", "prioridade": 3, "abrangencia": "departamento",
     "departamento_id": 12, "data_inicio": "2026-09-01", "data_fim": "2026-12-31", "versao": 1, "status": "pendente_aprovacao", "criado_por_user_id": OUTRA, "conflitos": []},
    {"id": 21, "instrumento_normativo_id": 1, "parametro": "antecedencia_ferias", "valor_anterior": "30", "valor_novo": "15", "prioridade": 2, "abrangencia": "departamento",
     "departamento_id": 13, "data_inicio": "2026-11-01", "data_fim": None, "versao": 1, "status": "rascunho", "criado_por_user_id": EU, "conflitos": [CONFLITO]},
    {"id": 22, "instrumento_normativo_id": 1, "parametro": "permite_banco_horas", "valor_anterior": "false", "valor_novo": "true", "prioridade": 2, "abrangencia": "departamento",
     "departamento_id": 13, "data_inicio": "2026-03-01", "data_fim": None, "versao": 2, "status": "vigente", "criado_por_user_id": OUTRA, "conflitos": []},
    {"id": 19, "instrumento_normativo_id": 1, "parametro": "permite_banco_horas", "valor_anterior": None, "valor_novo": "false", "prioridade": 2, "abrangencia": "departamento",
     "departamento_id": 13, "data_inicio": "2026-01-01", "data_fim": "2026-02-28", "versao": 1, "status": "encerrada", "criado_por_user_id": OUTRA, "conflitos": []},
    {"id": 23, "instrumento_normativo_id": 1, "parametro": "maximo_periodos", "valor_anterior": "1", "valor_novo": "3", "prioridade": 5, "abrangencia": "colaborador",
     "colaborador_id": 7, "data_inicio": "2026-05-01", "data_fim": None, "versao": 1, "status": "vigente", "criado_por_user_id": OUTRA, "conflitos": []},
]
ORG = {"departamentos": [{"id": 12, "nome": "TI"}, {"id": 13, "nome": "Comercial"}], "cargos": [{"id": 5, "nome": "Analista"}, {"id": 6, "nome": "Executiva de contas"}],
       "colaboradores": [{"id": 7, "nome": "Carlos Souza"}, {"id": 8, "nome": "Ana Ribeiro"}], "niveis": []}
SIM = {"sucesso": True, "total_afetados": 2, "departamentos": 1, "conflitos": [CONFLITO],
       "detalhes": [{"colaborador_id": 8, "nome": "Ana Ribeiro", "cargo_id": 5, "departamento_id": 13, "valor_matriz": 30, "valor_atual": None, "nivel_atual": "matriz", "valor_proposto": "15"},
                    {"colaborador_id": 9, "nome": "Tatiane Silva", "cargo_id": 6, "departamento_id": 13, "valor_matriz": 30, "valor_atual": None, "nivel_atual": "matriz", "valor_proposto": "15"}]}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _registra(nome):
    return lambda token, *a: chamadas.append((nome, *a)) or _falha_ou(nome, {"sucesso": True, "instrumento": {"id": 50}, "override": {"id": 60}})


api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": True, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.meu_humor = lambda token: {"ciclo": 0, "respondeu": True}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.organograma = lambda token: copy.deepcopy(ORG)
api_client.usuarios = lambda token: {"usuarios": [{"id": OUTRA, "nome": "Ana Ribeiro (RH)"}, {"id": EU, "nome": "Leonardo dos Santos"}]}
api_client.instrumentos_normativos = lambda token: {"instrumentos": copy.deepcopy(INSTRUMENTOS)}
api_client.regras_override = lambda token: {"overrides": copy.deepcopy(estado.get("regras", REGRAS))}
api_client.simular_override = lambda token, rid: chamadas.append(("simular", rid)) or copy.deepcopy(estado.get("sim", SIM))
for _nome in ("criar_instrumento", "enviar_instrumento", "aprovar_instrumento", "rejeitar_instrumento", "criar_override", "enviar_override",
              "aprovar_override", "rejeitar_override", "prioridade_override"):
    setattr(api_client, _nome, _registra(_nome))

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


def botao(at: AppTest, chave: str):
    return next(b for b in at.button if b.key == chave)


def aviso(at: AppTest) -> str:
    return str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else [t.value for t in at.toast])


def app(perfil: str = "RH", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": EU, "nome": "Leonardo dos Santos", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": 8}
    at.session_state["sessao_validada"] = True
    at.session_state["menu_grupos"] = {"RH": True, "Equipe": True, "Admin": True}  # grupos do menu abertos (o fechado é testado em testar_menu)
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "regras")
    return at.run()


nomes = {"departamentos": {12: "TI", 13: "Comercial"}, "cargos": {5: "Analista", 6: "Executiva de contas"}, "pessoas": {7: "Carlos Souza"}}
caso("Regras (regras_modelo.py)")
conferir(m.valor_legivel("antecedencia_ferias", "15") == "15 dias" and m.valor_legivel("permite_banco_horas", "true") == "habilitado"
         and m.valor_legivel("horas_diarias", "8.0") == "8h" and m.valor_legivel("maximo_periodos", "1") == "1 período", "valores legíveis")
conferir(m.titulo_regra(REGRAS[1], nomes) == "Antecedência — Departamento Comercial" and m.titulo_regra(REGRAS[4], nomes) == "Fracionamento — Colaborador Carlos Souza",
         "títulos como no Figma")
conferir(m.linha_regra(REGRAS[1], nomes, {1: "Acordo Coletivo 2026"})["detalhe"].startswith("30 dias → 15 dias") and m.linha_regra(REGRAS[1], nomes, {})["badge"] == "Conflito"
         and "Antecedência — Cargo Analista" in m.linha_regra(REGRAS[1], nomes, {})["conflito"], "linha com de → para, selo e frase do conflito")
conferir(m.acoes_instrumento(INSTRUMENTOS[1], EU)["aprovar"] == "Sem registro no MTE: não dá para aprovar ainda" and m.acoes_instrumento(INSTRUMENTOS[1], EU)["rejeitar"] is None,
         "coletivo sem MTE: aprovar desligado")
conferir(m.acoes_instrumento(INSTRUMENTOS[2], EU) == {"rejeitar": "Você criou este instrumento: outra pessoa precisa aprovar", "aprovar": "Você criou este instrumento: outra pessoa precisa aprovar"}
         and m.acoes_instrumento(INSTRUMENTOS[0], EU) == {"detalhes": None}, "o próprio: nada a decidir; vigente: detalhes")
conferir(m.acoes_regra(REGRAS[1], EU) == {"simular": None, "enviar": "Resolva o conflito antes de enviar"} and m.acoes_regra(REGRAS[0], EU) == {"simular": None, "rejeitar": None, "aprovar": None}
         and m.acoes_regra(REGRAS[2], EU) == {"nova_versao": None, "historico": None}, "ações das regras por situação")
conferir([r["id"] for r in m.filtrar(REGRAS, "Com conflito")] == [21] and [r["id"] for r in m.filtrar(REGRAS, "Vigentes")] == [22, 23]
         and [r["id"] for r in m.filtrar(REGRAS, "Pendentes de aprovação")] == [20], "filtros")
conferir([r["id"] for r in m.historico(REGRAS[2], REGRAS)] == [22, 19], "histórico: versões do mesmo escopo, da mais nova")
d = {"parametro": "antecedencia_ferias", "abrangencia": "departamento", "departamento_id": 13, "valor_novo": "15", "instrumento_normativo_id": 1,
     "data_inicio": HOJE + timedelta(days=10), "data_fim": None, "prioridade": 2}
conferir(m.validar_regra(d, HOJE) is None and "referência" in m.validar_regra(dict(d, departamento_id=None), HOJE)
         and "retroativa" in m.validar_regra(dict(d, data_inicio=HOJE - timedelta(days=3)), HOJE), "validação da regra (retroativa pede justificativa)")
conferir(m.corpo_regra(dict(d, data_inicio=HOJE - timedelta(days=3), justificativa="Acordo assinado antes."), HOJE)["tipo_aplicacao"] == "retroativa"
         and m.corpo_regra(d, HOJE)["tipo_aplicacao"] == "futura" and "cargo_id" not in m.corpo_regra(d, HOJE), "corpo da regra")
conferir("Mediador" in m.validar_instrumento({"tipo": "acordo_coletivo", "titulo": "Acordo", "entidade_responsavel": "S", "data_inicio": HOJE, "documento_url": "https://x"})
         and m.validar_instrumento({"tipo": "norma_legal", "titulo": "Lei", "entidade_responsavel": "União", "data_inicio": HOJE, "documento_url": "https://x"}) is None,
         "validação do instrumento")
vm = m.simulacao(SIM, REGRAS[1], nomes, {1: "Acordo Coletivo 2026"})
conferir(dict(vm["atual"])["Antecedência de férias"] == "30 dias" and dict(vm["atual"])["Origem"] == "Matriz do contrato" and dict(vm["nova"])["Origem"] == "Acordo Coletivo 2026",
         "simulação: regra atual vem da matriz quando nenhuma regra se aplica")
conferir(vm["conflitos"][0]["titulo"] == "Antecedência — Cargo Analista" and "atinge 4 pessoas" in vm["conflitos"][0]["detalhe"] and vm["cartoes"][3] == ("Conflitos", "1", "negativo")
         and vm["pessoas"][1]["cargo"] == "Executiva de contas", "simulação: conflito, cartões e pessoas")

caso("Lista (Figma 287:884)")
at = app()
t = texto(at)
conferir("Regras e Conformidade" in t and "Instrumentos normativos e exceções em análise" in t and "Acordo Coletivo 2026" in t and "Jornada — Departamento TI" in t,
         "título, instrumentos e regras")
conferir("Sem registro no MTE: não dá para aprovar ainda" in t and botao(at, "reg_aprovar_in_2").disabled and "Você criou este instrumento: outra pessoa precisa aprovar" in t
         and botao(at, "reg_aprovar_in_3").disabled, "aprovar desligado: sem MTE e autoaprovação")
conferir("Conflito com \"Antecedência — Cargo Analista\" (mesma prioridade). Resolva antes de publicar" in t and botao(at, "reg_enviar_ov_21").disabled, "conflito na regra e envio desligado")
at.button_group(key="reg_filtro").set_value("Vigentes")
at = at.run()
conferir("reg_card_ov_22" in str([c.key for c in at.get("flex_container")]) or ("Banco de horas — Departamento Comercial" in texto(at) and "Jornada — Departamento TI" not in texto(at)),
         "filtro Vigentes")

caso("Novo instrumento")
at = app()
at.button(key="reg_novo_instr").click()
at = at.run()
at.selectbox(key="reg_in_tipo").set_value("acordo_coletivo")
at.text_input(key="reg_in_titulo").set_value("Acordo Coletivo 2027")
at.text_input(key="reg_in_entidade").set_value("Sindicato dos Trabalhadores")
at.date_input(key="reg_in_inicio").set_value(date(2027, 1, 1))
at.text_input(key="reg_in_documento").set_value("https://ex.com/2027.pdf")
at.button(key="reg_in_ok").click()
at = at.run()
conferir("Mediador é obrigatória" in texto(at) and not any(c[0] == "criar_instrumento" for c in chamadas), "coletivo sem Mediador: mensagem, sem chamar a API")
at.text_input(key="reg_in_mediador").set_value("MR12345/2027")
at.button(key="reg_in_ok").click()
at = at.run()
criado = next((c for c in chamadas if c[0] == "criar_instrumento"), None)
conferir(criado and criado[1]["numero_solicitacao_mediador"] == "MR12345/2027" and criado[1]["data_inicio"] == "2027-01-01" and ("enviar_instrumento", 50) in chamadas,
         "cria e envia para aprovação")

caso("Nova regra e simulação (Figma 288:1234 e 288:886)")
at = app()
at.button(key="reg_nova_regra").click()
at = at.run()
at.selectbox(key="reg_ov_param").set_value("antecedencia_ferias")
at.selectbox(key="reg_ov_ab").set_value("departamento")
at = at.run()
at.selectbox(key="reg_ov_dep").set_value(13)
at.number_input(key="reg_ov_num").set_value(15.0)
at.selectbox(key="reg_ov_instr").set_value(1)
at.date_input(key="reg_ov_inicio").set_value(HOJE + timedelta(days=10))
at.number_input(key="reg_ov_prio").set_value(2)
at.button(key="reg_ov_ok").click()
at = at.run()
criada = next((c for c in chamadas if c[0] == "criar_override"), None)
conferir(criada and criada[1]["departamento_id"] == 13 and criada[1]["valor_novo"] == "15" and criada[1]["tipo_aplicacao"] == "futura"
         and at.session_state["reg_simular"] == 60, "cria o rascunho e abre a simulação")
at = app()
at.session_state["reg_simular"] = 21
at = at.run()
t = texto(at)
conferir("Simulação de impacto" in t and "Antecedência — Departamento Comercial" in t and "30 dias" in t and "Matriz do contrato" in t and "Tatiane Silva" in t
         and "Executiva de contas" in t, "simulação: regra atual x nova e pessoas")
conferir("Antecedência — Cargo Analista" in t and botao(at, "reg_sim_enviar").disabled and "Resolva o conflito antes de enviar" in t, "conflito bloqueia o envio")
at.button(key="reg_conf_prio_30").click()
at = at.run()
at.number_input(key="reg_prio_valor").set_value(3)
at.button(key="reg_prio_ok").click()
at = at.run()
conferir(("prioridade_override", 21, 3) in chamadas and "Prioridade alterada para 3" in aviso(at), "Definir prioridade")
at = app(sim=dict(SIM, conflitos=[]), regras=[dict(REGRAS[1], conflitos=[])] + REGRAS[2:])
at.session_state["reg_simular"] = 21
at = at.run()
at.button(key="reg_sim_enviar").click()
at = at.run()
conferir(("enviar_override", 21) in chamadas, "sem conflito: envia para aprovação")

caso("Aprovar, rejeitar, nova versão e histórico")
at = app()
at.button(key="reg_aprovar_ov_20").click()
at = at.run()
conferir("Ana Ribeiro (RH)" in texto(at) and "A versão anterior continua no histórico" in texto(at), "modal de aprovação com quem criou")
at.text_area(key="reg_apr_just").set_value("Conferi o acordo coletivo e a simulação.")
at.button(key="reg_apr_ok").click()
at = at.run()
conferir(("aprovar_override", 20, "Conferi o acordo coletivo e a simulação.") in chamadas and "vigente" in aviso(at), "aprova com justificativa")
at = app()
at.button(key="reg_rejeitar_ov_20").click()
at = at.run()
at.text_area(key="reg_rej_motivo").set_value("ok")
at.button(key="reg_rej_ok").click()
at = at.run()
conferir("pelo menos 5 caracteres" in texto(at) and not any(c[0] == "rejeitar_override" for c in chamadas), "rejeitar exige motivo")
at.text_area(key="reg_rej_motivo").set_value("Escala 12x36 sem o registro no MTE.")
at.button(key="reg_rej_ok").click()
at = at.run()
conferir(("rejeitar_override", 20, "Escala 12x36 sem o registro no MTE.") in chamadas, "rejeita com motivo")
at = app(regras=[dict(REGRAS[1], status="pendente_aprovacao", criado_por_user_id=OUTRA)] + REGRAS[2:])
at.button(key="reg_aprovar_ov_21").click()
at = at.run()
conferir("Conflito não resolvido com \"Antecedência — Cargo Analista\"" in texto(at) and "reg_apr_ok" not in chaves(at), "com conflito: o aviso de que bloqueia, sem aprovar")
at = app()
at.button(key="reg_nova_versao_ov_22").click()
at = at.run()
conferir(at.selectbox(key="reg_ov_param").value == "permite_banco_horas" and at.selectbox(key="reg_ov_dep").value == 13 and at.text_input(key="reg_ov_atual").value == "habilitado",
         "nova versão vem preenchida com a vigente")
at = app()
at.button(key="reg_historico_ov_22").click()
at = at.run()
conferir("Versão 2" in texto(at) and "Versão 1" in texto(at) and "Encerrada" in texto(at), "histórico com as versões")
at = app("COLABORADOR")
conferir("só do RH e do Admin" in texto(at), "colaborador: só RH e Admin")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
