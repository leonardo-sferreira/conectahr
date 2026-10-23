"""Testes da Central de Pendências e da tela Ausências (tarefas 11 a 13, 20, 21 e 24 da change
concluir-frontend-streamlit), sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Escopo ............. o colaborador só vê "Minhas pendências"; Gestor, RH e Admin veem as filas que o
                       backend devolve; ninguém recebe botão para decidir o próprio pedido
  Férias ............. "Decidir" mostra a conferência de conflitos e aprova ou rejeita
  Correções .......... aprovar direto; rejeitar exige motivo
  Ausências (RH) ..... aprovar, rejeitar com justificativa, registrar a aprovada, abrir o comprovante
  Estados ............ vazio, erro ao carregar e recusa do backend

Uso (na raiz do repositório):
    python tools/testar_decisoes.py
"""

import html as html_lib
import logging
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import decisoes_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}  # sino do topo (sem rede)

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
chamadas: list[tuple] = []
estado: dict = {}

ORGANOGRAMA = {
    "departamentos": [{"id": 1, "nome": "Recursos Humanos"}, {"id": 2, "nome": "TI"}],
    "colaboradores": [
        {"id": 7, "nome": "Ana Ribeiro", "departamento_id": 1},
        {"id": 9, "nome": "Leonardo dos Santos", "departamento_id": 2},
        {"id": 11, "nome": "Juliana Prado", "departamento_id": 2},
        {"id": 12, "nome": "Carlos Souza", "departamento_id": 1},
    ],
}


def ms(dia: date, h: int, mi: int = 0) -> int:
    """Horário de Brasília -> milissegundos UTC."""
    return int(datetime(dia.year, dia.month, dia.day, h + 3, mi, tzinfo=timezone.utc).timestamp() * 1000)


DIA_COR = date(2026, 8, 25)  # terça-feira


def fila_ferias():
    return [
        {"id": 71, "colaborador_id": 9, "data_inicio": "2027-01-10", "data_fim": "2027-01-20", "quantidade_dias": 11, "status": "Pendente", "observacao_colaborador": "Viagem em família.", "data_solicitacao": "2026-08-15T12:00:00Z"},
        {"id": 72, "colaborador_id": 7, "data_inicio": "2026-12-05", "data_fim": "2026-12-19", "quantidade_dias": 15, "status": "Pendente", "data_solicitacao": "2026-09-02T12:00:00Z"},
        {"id": 73, "colaborador_id": 12, "data_inicio": "2026-11-02", "data_fim": "2026-11-11", "quantidade_dias": 10, "status": "Pendente", "data_solicitacao": "2026-07-20T12:00:00Z"},
    ]


def correcoes():
    return [
        {"id": 31, "colaborador_id": 12, "campo": "hora_saida", "valor_solicitado": ms(DIA_COR, 18), "valor_original": None, "justificativa": "Esqueci de marcar a saída.", "status": "pendente"},
        {"id": 32, "colaborador_id": 7, "campo": "hora_entrada", "valor_solicitado": ms(DIA_COR, 8), "justificativa": "Celular sem sinal.", "status": "pendente"},
    ]


def ausencias():
    return {
        "Pendente": [
            {"id": 51, "colaborador_id": 9, "tipo": "Atestado", "data_inicio": "2026-09-01", "data_fim": "2026-09-01", "motivo_tipo": "consulta", "observacao": "Afastamento de 1 dia.", "comprovante": {"path": "/x.pdf"}, "status": "Pendente"},
            {"id": 52, "colaborador_id": 7, "tipo": "Falta", "data_inicio": "2026-09-25", "data_fim": "2026-09-25", "motivo_tipo": "outro", "status": "Pendente"},
        ],
        "Aprovada": [{"id": 53, "colaborador_id": 11, "tipo": "Licenca", "data_inicio": "2026-09-14", "data_fim": "2026-09-18", "status": "Aprovada", "updated_at": "2026-09-02T10:00:00Z"}],
        "Registrado": [{"id": 54, "colaborador_id": 12, "tipo": "Falta", "data_inicio": HOJE.isoformat(), "data_fim": HOJE.isoformat(), "status": "Registrado", "updated_at": HOJE.isoformat() + "T09:00:00Z"}],
        "Rejeitada": [],
    }


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _instalar():
    api_client.auth_me = lambda token: {"autenticado": True}
    api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}  # menu Equipe (tarefa 83)
    api_client.prazo_correcao = lambda token: {"prazo_dias": None}  # prazo de correção (tarefa 79)
    api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
    api_client.meu_humor = lambda token: {"ciclo": 0, "respondeu": True}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.organograma = lambda token: ORGANOGRAMA
    api_client.central_de_tarefas = lambda token: chamadas.append(("central",)) or _falha_ou("central", {
        "meu_ponto_status_hoje": estado.get("ponto_hoje"),
        "fila_ferias_pendentes": estado["fila"], "fila_documentos_pendentes": [{"id": 1}, {"id": 2}], "fila_desligamentos_pendentes": [],
        "fila_ausencias_pendentes": estado.get("fila_aus", []), "e_superior": estado.get("e_superior", False),
    })
    api_client.solicitacoes_rh = lambda token: _falha_ou("solicitacoes", {"solicitacoes": estado.get("solicitacoes", [])})
    api_client.correcoes_ponto = lambda token: chamadas.append(("correcoes",)) or _falha_ou("correcoes", {"correcoes": estado["correcoes"]})
    api_client.verificar_conflito_ferias = lambda token, fid: chamadas.append(("conflito", fid)) or _falha_ou("conflito", {
        "antecedencia_dias": 148, "periodo_aquisitivo_cumprido": True, "ferias_sobrepostas": [], "ausencias_sobrepostas": [],
        "colegas_de_ferias_no_periodo": [{"id": 1}], "tamanho_equipe": 4,
    })
    api_client.aprovar_ferias = lambda token, fid: chamadas.append(("aprovar_ferias", fid)) or _falha_ou("decidir", {"sucesso": True})
    api_client.rejeitar_ferias = lambda token, fid: chamadas.append(("rejeitar_ferias", fid)) or _falha_ou("decidir", {"sucesso": True})
    api_client.aprovar_correcao_ponto = lambda token, cid: chamadas.append(("aprovar_cor", cid)) or _falha_ou("decidir", {"sucesso": True})
    api_client.rejeitar_correcao_ponto = lambda token, cid, motivo: chamadas.append(("rejeitar_cor", cid, motivo)) or _falha_ou("decidir", {"sucesso": True})
    # Minhas pendências
    api_client.minhas_solicitacoes = lambda token: {"solicitacoes": [
        {"tipo": "alteracao_cadastral", "status": "em_analise", "created_at": "2026-08-25T10:00:00Z"},
        {"tipo": "declaracao", "status": "atendida", "created_at": "2025-01-01T10:00:00Z", "data_decisao": "2025-01-05T10:00:00Z"},
    ]}
    api_client.minhas_ferias = lambda token: _falha_ou("minhas_ferias", {"ferias": [{"id": 80, "data_inicio": "2027-01-10", "data_fim": "2027-01-20", "status": "Pendente", "data_solicitacao": "2026-08-15T12:00:00Z"}]})
    api_client.minhas_ausencias = lambda token: {"ausencias": []}
    api_client.minhas_pendencias_documento = lambda token: {"pendencias": [{"tipo_documento": "cnh", "status": "pendente", "prazo": (HOJE + timedelta(days=30)).isoformat()}]}
    api_client.minhas_correcoes_ponto = lambda token: {"correcoes": [{"campo": "hora_saida", "valor_solicitado": ms(DIA_COR, 18), "status": "pendente"}]}
    # Ausências do RH
    api_client.ausencias_rh = lambda token, status: chamadas.append(("ausencias", status)) or _falha_ou("ausencias", {"ausencias": estado["ausencias"][status]})
    api_client.aprovar_ausencia = lambda token, aid, obs=None: chamadas.append(("aprovar_aus", aid)) or _falha_ou("decidir", {"sucesso": True})
    api_client.rejeitar_ausencia = lambda token, aid, texto: chamadas.append(("rejeitar_aus", aid, texto)) or _falha_ou("decidir", {"sucesso": True})
    api_client.registrar_ausencia_aprovada = lambda token, aid, obs=None: chamadas.append(("registrar_aus", aid)) or _falha_ou("decidir", {"sucesso": True})
    api_client.abrir_comprovante_ausencia = lambda token, aid: chamadas.append(("comprovante", aid)) or _falha_ou("comprovante", {"comprovante_url": f"https://arquivos.exemplo.com/a{aid}.pdf"})


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


USUARIOS = {
    "COLABORADOR": {"id": 1, "nome": "Leonardo dos Santos", "perfil": "COLABORADOR", "colaborador_id": 9},
    "GESTOR": {"id": 3, "nome": "Carlos Souza", "perfil": "GESTOR", "colaborador_id": 12},
    "RH": {"id": 2, "nome": "Ana Ribeiro", "perfil": "RH", "colaborador_id": 7},
    "ADMIN": {"id": 4, "nome": "Admin Teste", "perfil": "ADMIN", "colaborador_id": None},
}


def app(perfil: str = "GESTOR", pagina: str = "central-de-pendencias", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(fila=fila_ferias(), correcoes=correcoes(), ausencias=ausencias())
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = dict(USUARIOS[perfil], email="pessoa@empresa.com")
    at.session_state["sessao_validada"] = True
    at.session_state["menu_grupos"] = {"RH": True, "Equipe": True, "Admin": True}  # grupos do menu abertos (o fechado é testado em testar_menu)
    return abrir(at.run(), pagina)


# ---------------------------------------------------------------------------
caso("Regras de apresentação (decisoes_modelo.py)")
mapa = m.pessoas(ORGANOGRAMA)
lf = m.linhas_ferias(fila_ferias(), mapa, 12)
conferir([l["id"] for l in lf] == [73, 71, 72], "férias: do pedido mais antigo para o mais novo")
conferir(lf[1]["periodo"] == "10 a 20/01/2027" and lf[1]["dias"] == "11 dias" and lf[1]["pedido_em"] == "15/08/2026", "período, dias e data do pedido")
conferir(lf[0]["proprio"] and not lf[1]["proprio"], "o próprio pedido fica marcado")
conferir([l["id"] for l in m.linhas_ferias(fila_ferias(), mapa, None, 2)] == [71], "filtro de departamento")
lc = m.linhas_correcoes(correcoes(), mapa, None)
conferir(lc[0]["campo"] == "Saída" and lc[0]["dia"] == "25/08/2026" and lc[0]["horario"] == "18:00", "correção: campo, dia e horário pedido em Brasília")
rep_p = [{"id": 1, "colaborador_id": 9, "tipo": "inclusao", "valor_solicitado": "2026-10-09T16:00:00Z", "status": "pendente"},
         {"id": 2, "colaborador_id": 9, "tipo": "desconsideracao", "marcacao_id": 5, "valor_original": "2026-10-07T11:01:00Z", "status": "pendente"}]
lr = m.linhas_correcoes(rep_p, mapa, None)
conferir((lr[0]["campo"], lr[0]["dia"], lr[0]["horario"]) == ("Incluir marcação", "09/10/2026", "13:00") and (lr[1]["campo"], lr[1]["dia"], lr[1]["horario"]) == ("Desconsiderar marcação", "07/10/2026", "08:01"),
         "correção no REP-P: incluir ou desconsiderar, com o dia e o horário")
itens_rep = {s["titulo"]: s["itens"] for s in m.minhas_pendencias({}, [], [], [], [], rep_p, HOJE)}["Ponto"]
conferir([i["titulo"] for i in itens_rep] == ["Correção de ponto — sexta-feira, 09/10", "Correção de ponto — quarta-feira, 07/10"], "minhas pendências: correções do REP-P com o dia")
alt = [{"id": 3, "colaborador_id": 9, "tipo": "alteracao", "marcacao_id": 5, "valor_original": "2026-10-07T11:15:00Z", "valor_solicitado": "2026-10-07T11:00:00Z", "status": "pendente"}]
la = m.linhas_correcoes(alt, mapa, None)[0]
conferir((la["campo"], la["horario"], la["original"]) == ("Corrigir horário", "08:00", "08:15"), "corrigir horário na fila de decisão: o novo horário e o de antes")
item_alt = {s["titulo"]: s["itens"] for s in m.minhas_pendencias({}, [], [], [], [], alt, HOJE)}["Ponto"][0]
conferir("Corrigir horário de 08:15 para 08:00" in str(item_alt), f"minhas pendências: corrigir de X para Y ({item_alt})")
conf = {"antecedencia_dias": 148, "periodo_aquisitivo_cumprido": True, "ferias_sobrepostas": [], "ausencias_sobrepostas": [], "colegas_de_ferias_no_periodo": [{}], "tamanho_equipe": 4}
conferir(" · ".join(m.conferencia_ferias(conf)) == "Antecedência de 148 dias · período aquisitivo cumprido · sem sobreposição com férias ou ausências · 1 de 4 colegas do departamento de férias no período", "conferência de conflitos em frases")
conferir(not m.tem_alerta(conf) and m.tem_alerta(dict(conf, ferias_sobrepostas=[{}])) and m.tem_alerta(dict(conf, periodo_aquisitivo_cumprido=False)), "alerta só com sobreposição ou período não cumprido")
conferir(m.validar_motivo("ok") and m.validar_motivo("Não confere com a portaria.") is None, "motivo da recusa: 5 caracteres ou mais")
secoes = m.minhas_pendencias({"meu_ponto_status_hoje": "Incompleto"}, api_client.minhas_solicitacoes("t")["solicitacoes"], api_client.minhas_ferias("t")["ferias"], [],
                             api_client.minhas_pendencias_documento("t")["pendencias"], api_client.minhas_correcoes_ponto("t")["correcoes"], HOJE)
titulos = {s["titulo"]: s["itens"] for s in secoes}
conferir(list(titulos) == ["Solicitações ao RH", "Férias", "Documentos pendentes", "Ponto"], "minhas pendências: seções na ordem do Figma, só as que têm itens")
conferir(len(titulos["Solicitações ao RH"]) == 1 and titulos["Solicitações ao RH"][0]["badge"] == "Em análise", "decisão antiga (mais de 30 dias) sai da lista")
conferir(titulos["Ponto"][1]["titulo"] == "Correção de ponto — terça-feira, 25/08" and titulos["Ponto"][0]["titulo"] == "Jornada de hoje incompleta", "ponto: jornada incompleta e correção em análise")
conferir(titulos["Documentos pendentes"][0]["titulo"] == "Envio de CNH", "documento pendente com o nome do tipo")
la = m.linhas_ausencias(ausencias()["Pendente"], mapa, 7)
conferir(la[0]["motivo"] == "Consulta · Afastamento de 1 dia." and la[0]["comprovante"] and not la[1]["comprovante"] and la[1]["proprio"], "ausência: motivo, comprovante e a própria marcada")
r = m.resumo_ausencias(ausencias(), HOJE)
conferir((r["pendentes"], r["aprovadas"], r["registradas_mes"], r["rejeitadas_mes"]) == (2, 1, 1, 0), "números do topo de Ausências")

# ---------------------------------------------------------------------------
caso("Escopo por perfil (tarefa 13)")
at = app("COLABORADOR")
t = texto(at)
conferir(("correcoes",) not in chamadas and "Férias para decidir" not in t and "central_aba" not in [s.key for s in at.button_group], "colaborador: sem filas nem abas de decisão")
conferir("Alteração cadastral" in t and "Envio de CNH" in t and "Férias — 10 a 20/01/2027" in t, "colaborador: Minhas pendências (F13)")
at = app("GESTOR")
t = texto(at)
conferir(("central",) in chamadas and ("correcoes",) in chamadas and "Férias para decidir" in t and at.button_group(key="central_aba").value == "ferias", "gestor: filas que o backend devolve no escopo dele")
conferir("central_dep" not in [s.key for s in at.selectbox], "gestor: sem filtro de departamento (só a própria equipe)")
conferir({"central_fe_71", "central_fe_72"} <= chaves(at) and "central_fe_73" not in chaves(at) and "Seu pedido: outra pessoa decide" in t, "o próprio pedido não tem 'Decidir'")
at = app("RH")
conferir("central_dep" in [s.key for s in at.selectbox] and "central_fe_72" not in chaves(at), "RH: filtro de departamento; também não decide o próprio pedido")
at.selectbox(key="central_dep").set_value(2)
at = at.run()
conferir("central_fe_71" in chaves(at) and "central_fe_73" not in chaves(at), "RH: filtro de departamento na fila")
at = app("ADMIN")
conferir({"central_fe_71", "central_fe_72", "central_fe_73"} <= chaves(at), "Admin sem colaborador: decide todos")

caso("Decidir férias (Figma 436:1473)")
at = app("GESTOR")
at.button(key="central_fe_71").click()
at = at.run()
t = texto(at)
conferir(("conflito", 71) in chamadas and "Antecedência de 148 dias" in t and "1 de 4 colegas" in t, "o modal mostra a conferência de conflitos")
at.button(key="central_fe_aprovar").click()
at = at.run()
conferir(("aprovar_ferias", 71) in chamadas and "modal_central" not in at.session_state, "'Aprovar' aprova e fecha o modal")
at = app("GESTOR")
at.button(key="central_fe_72").click()
at = at.run()
at.button(key="central_fe_rejeitar").click()
at = at.run()
conferir(("rejeitar_ferias", 72) in chamadas, "'Rejeitar' rejeita")
at = app("GESTOR", erro_decidir=ApiError("Voce nao tem permissao para decidir esta solicitacao de ferias.", 403))
at.button(key="central_fe_71").click()
at = at.run()
at.button(key="central_fe_aprovar").click()
at = at.run()
conferir("nao tem permissao" in texto(at) and "modal_central" in at.session_state, "recusa do backend (fora do escopo) no modal, que continua aberto")
at = app("GESTOR", erro_conflito=ApiError("Erro inesperado. Tente novamente.", 500))
at.button(key="central_fe_71").click()
at = at.run()
conferir("Não foi possível conferir agora" in texto(at) and not at.button(key="central_fe_aprovar").disabled, "sem a conferência, a decisão continua possível (ela só informa)")

caso("Correções de ponto (Figma 436:1308 e 436:1506)")
at = app("RH")
at.button_group(key="central_aba").set_value("correcoes")
at = at.run()
t = texto(at)
conferir("Esqueci de marcar a saída." in t and "18:00" in t and "rh_recusar_cor_31" in chaves(at) and "rh_recusar_cor_32" not in chaves(at), "fila de correções; a própria sem botões")
at.button(key="central_cor_aprovar_31").click()
at = at.run()
conferir(("aprovar_cor", 31) in chamadas, "'Aprovar' decide direto")
at = app("RH")
at.button_group(key="central_aba").set_value("correcoes")
at = at.run()
at.button(key="rh_recusar_cor_31").click()
at = at.run()
at.text_area(key="central_cor_motivo").set_value("não")
at.button(key="central_cor_ok").click()
at = at.run()
conferir("5 caracteres" in texto(at) and not any(c[0] == "rejeitar_cor" for c in chamadas), "rejeitar sem motivo: mensagem, sem chamar a API")
at.text_area(key="central_cor_motivo").set_value("Não confere com a portaria.")
at.button(key="central_cor_ok").click()
at = at.run()
conferir(("rejeitar_cor", 31, "Não confere com a portaria.") in chamadas, "rejeitar envia o motivo")
at = app("GESTOR", erro_decidir=ApiError("Voce nao tem permissao para decidir esta correcao de ponto.", 403))
at.button_group(key="central_aba").set_value("correcoes")
at = at.run()
at.button(key="central_cor_aprovar_32").click()
at = at.run()
conferir("nao tem permissao" in texto(at) and not at.exception, "gestor fora do departamento: a recusa do backend vira alerta (tarefa 21)")

caso("Estados da Central")
at = app("GESTOR", fila=[], correcoes=[])
conferir("Nenhum pedido de férias para decidir." in texto(at), "vazio: fila de férias")
at = app("GESTOR", erro_correcoes=ApiError("Erro inesperado. Tente novamente.", 500))
at.button_group(key="central_aba").set_value("correcoes")
at = at.run()
conferir("Erro inesperado" in texto(at) and not at.exception, "erro só nas correções: alerta, a tela continua")
at = app("GESTOR", erro_central=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro ao carregar a central vira alerta")
at = app("GESTOR")
at.button_group(key="central_aba").set_value("minhas")
at = at.run()
conferir("Alteração cadastral" in texto(at), "gestor também tem 'Minhas pendências'")
at = app("COLABORADOR", erro_minhas_ferias=ApiError("Erro inesperado.", 500))
conferir("Parte das suas pendências não carregou" in texto(at) and "Envio de CNH" in texto(at), "falha parcial em Minhas pendências: aviso e o resto continua")

# ---------------------------------------------------------------------------
caso("Ausências do RH (Figma 243:846)")
at = app("RH", "ausencias")
t = texto(at)
conferir("Aprovadas, falta registrar" in t and {("ausencias", s) for s in ("Pendente", "Aprovada", "Registrado", "Rejeitada")} <= set(chamadas), "números do topo com as quatro listas")
conferir({"rh_recusar_aus_51", "aus_aprovar_51", "rh_abrir_aus_51"} <= chaves(at) and "aus_aprovar_52" not in chaves(at), "pendentes: Rejeitar e Aprovar; a própria sem botões; comprovante quando houver")
at.button(key="aus_aprovar_51").click()
at = at.run()
conferir(("aprovar_aus", 51) in chamadas, "'Aprovar' aprova")
at = app("RH", "ausencias")
at.button(key="rh_abrir_aus_51").click()
at = at.run()
conferir(("comprovante", 51) in chamadas and any(b.proto.url.endswith("/a51.pdf") for b in at.get("link_button")), "'Ver' pede o link do comprovante")
at = app("RH", "ausencias")
at.button(key="rh_recusar_aus_51").click()
at = at.run()
at.button(key="aus_rej_ok").click()
at = at.run()
conferir("5 caracteres" in texto(at) and not any(c[0] == "rejeitar_aus" for c in chamadas), "rejeitar sem justificativa: mensagem, sem chamar a API")
at.text_area(key="aus_rej_texto").set_value("Atestado sem data legível.")
at.button(key="aus_rej_ok").click()
at = at.run()
conferir(("rejeitar_aus", 51, "Atestado sem data legível.") in chamadas, "rejeitar envia a justificativa")
at = app("RH", "ausencias")
at.button_group(key="aus_aba").set_value("Aprovadas")
at = at.run()
at.button(key="aus_registrar_53").click()
at = at.run()
conferir("Aprovada em" in texto(at) and "02/09/2026" in texto(at), "modal Registrar com a data da aprovação")
at.button(key="aus_reg_ok").click()
at = at.run()
conferir(("registrar_aus", 53) in chamadas, "'Registrar' registra a ausência aprovada")
at = app("RH", "ausencias", erro_decidir=ApiError("Nao informe diagnostico nem codigo CID na observacao.", 400))
at.button(key="rh_recusar_aus_51").click()
at = at.run()
at.text_area(key="aus_rej_texto").set_value("CID J11 sem comprovante.")
at.button(key="aus_rej_ok").click()
at = at.run()
conferir("CID" in texto(at) and "modal_ausencia" in at.session_state, "recusa do backend (CID na observação) no modal")
for perfil in ("COLABORADOR", "GESTOR"):
    at = app(perfil, "ausencias")
    conferir("só do RH e do Admin" in texto(at) and not any(c[0] == "ausencias" for c in chamadas), f"{perfil.lower()}: a tela não carrega")
at = app("RH", "ausencias", erro_ausencias=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro ao carregar vira alerta")
at = app("RH", "ausencias")
at.button_group(key="aus_aba").set_value("Rejeitadas")
at = at.run()
conferir("Nenhuma ausência nesta aba." in texto(at), "vazio: aba sem ausências")

# ---------------------------------------------------------------------------
caso("Hierarquia em férias e ausências; superior sem o perfil Gestor (tarefa 83)")
FILA_AUS = [
    {"id": 61, "colaborador_id": 11, "tipo": "Atestado", "data_inicio": "2026-09-01", "data_fim": "2026-09-02", "status": "Pendente"},
    {"id": 62, "colaborador_id": 9, "tipo": "Falta", "data_inicio": "2026-09-05", "data_fim": "2026-09-05", "status": "Pendente"},
    {"id": 63, "colaborador_id": 11, "tipo": "Falta", "data_inicio": "2026-08-01", "data_fim": "2026-08-01", "status": "Aprovada"},
]
la = m.linhas_ausencias_fila(FILA_AUS, mapa, 9)
conferir([l["id"] for l in la] == [61, 62] and la[0]["tipo"] == "Atestado" and la[1]["proprio"] and "motivo" not in la[0] and "comprovante" not in la[0],
         "fila de ausências: só pendentes, sem motivo nem comprovante; a própria marcada")
at = app("COLABORADOR", e_superior=True, fila_aus=FILA_AUS)
t = texto(at)
conferir("Ausências para decidir" in t and ("correcoes",) in chamadas, "colaborador que é superior direto vê as filas de decisão")
at.button_group(key="central_aba").set_value("ausencias")
at = at.run()
t = texto(at)
conferir("central_aus_aprovar_61" in chaves(at) and "central_aus_aprovar_62" not in chaves(at) and "Sua ausência: outra pessoa decide" in t, "aba Ausências: decide a da equipe, não a própria")
conferir("visto só pelo RH" not in t, "aba Ausências sem texto de fluxo")
at.button(key="central_aus_aprovar_61").click()
at = at.run()
conferir(("aprovar_aus", 61) in chamadas, "Aprovar ausência chama o backend")
at = app("GESTOR", fila_aus=FILA_AUS)
at.button_group(key="central_aba").set_value("ausencias")
at = at.run()
at.button(key="rh_recusar_aus_c_61").click()
at = at.run()
at.button(key="aus_rej_ok").click()
at = at.run()
conferir(not any(c[0] == "rejeitar_aus" for c in chamadas) and "modal_central" in at.session_state, "rejeitar sem justificativa: mensagem, sem chamar a API")
at.text_area(key="central_aus_motivo").set_value("Período coincide com a entrega do projeto.")
at.button(key="aus_rej_ok").click()
at = at.run()
conferir(("rejeitar_aus", 61, "Período coincide com a entrega do projeto.") in chamadas and "modal_central" not in at.session_state, "rejeitar com justificativa chama o backend e fecha")
at = app("GESTOR", fila_aus=FILA_AUS, erro_decidir=ApiError("Voce nao tem permissao para decidir esta ausencia.", 403))
at.button_group(key="central_aba").set_value("ausencias")
at = at.run()
at.button(key="central_aus_aprovar_61").click()
at = at.run()
conferir("permissão" in texto(at) or "permissao" in texto(at), "recusa do backend (fora da hierarquia) vira alerta")
at = app("COLABORADOR", e_superior=False, fila_aus=FILA_AUS)
conferir("Ausências para decidir" not in texto(at), "colaborador que não é superior: só Minhas pendências")
at = app("COLABORADOR", erro_central=ApiError("Erro inesperado. Tente novamente.", 500))
conferir(not at.exception and "Ausências para decidir" not in texto(at), "erro na central: o colaborador continua vendo as próprias pendências")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
