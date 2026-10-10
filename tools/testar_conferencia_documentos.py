"""Testes da "Conferência de documentos" do RH (tarefa 27 da change concluir-frontend-streamlit), sem
navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Regras da tela ..... ninguém decide o próprio documento; arquivo bloqueado só pode ser recusado;
                       só recusado, vencido ou substituído pode ser arquivado; nada de exclusão
  Perfis ............. o grupo "RH" do menu e a tela só para RH e Admin; 403 do backend vira mensagem
  Ações .............. aprovar, recusar (motivo obrigatório), arquivar, abrir o arquivo, pedir
                       documento, processar vencidos e nova regra, com os dados certos para a API
  Abas ............... "Para conferir", "Pendências pedidas" e "Obrigatórios por cargo"

Uso (na raiz do repositório):
    python tools/testar_conferencia_documentos.py
"""

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
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
ONTEM = (HOJE - timedelta(days=1)).isoformat()
DAQUI_10 = (HOJE + timedelta(days=10)).isoformat()

chamadas: list[tuple] = []
estado: dict = {}

ORGANOGRAMA = {
    "departamentos": [{"id": 1, "nome": "Recursos Humanos"}, {"id": 2, "nome": "TI"}, {"id": 3, "nome": "Financeiro"}],
    "cargos": [{"id": 3, "nome": "Motorista"}],
    "colaboradores": [
        {"id": 7, "nome": "Ana Ribeiro", "departamento_id": 1},
        {"id": 11, "nome": "Juliana Prado", "departamento_id": 2},
        {"id": 12, "nome": "Carlos Souza", "departamento_id": 1},
        {"id": 13, "nome": "Pedro Rocha", "departamento_id": 3},
    ],
}


def documentos_padrao():
    return [
        {"id": 101, "colaborador_id": 7, "tipo": "cnh", "nome_documento": "CNH", "status": "pendente_analise", "estado_verificacao": "liberado", "created_at": "2026-09-28T10:00:00Z", "data_validade": "2031-03-15"},
        {"id": 102, "colaborador_id": 11, "tipo": "aso_admissional", "nome_documento": "ASO admissional", "status": "pendente_analise", "estado_verificacao": "liberado", "created_at": "2026-09-30T10:00:00Z"},
        {"id": 103, "colaborador_id": 12, "tipo": "comprovante_residencia", "nome_documento": "Comprovante de residência", "status": "pendente_analise", "estado_verificacao": "bloqueado", "motivo_bloqueio": "Extensao nao permitida: .exe.", "created_at": "2026-10-01T10:00:00Z"},
        {"id": 104, "colaborador_id": 13, "tipo": "cnh", "nome_documento": "CNH", "status": "vencido", "data_validade": "2026-09-20", "created_at": "2021-09-20T10:00:00Z"},
        {"id": 105, "colaborador_id": 13, "tipo": "rg", "nome_documento": "RG", "status": "aprovado", "data_validade": ONTEM, "updated_at": HOJE.isoformat() + "T08:00:00Z"},
        {"id": 106, "colaborador_id": 11, "tipo": "rg", "nome_documento": "RG", "status": "arquivado"},
        {"id": 107, "colaborador_id": 12, "tipo": "cpf", "nome_documento": "CPF", "status": "rejeitado", "updated_at": "2026-09-01T10:00:00Z"},
    ]


def pendencias_padrao():
    return [
        {"colaborador_id": 11, "tipo_documento": "ctps", "status": "pendente", "prazo": DAQUI_10, "solicitado_por_user_id": 1},
        {"colaborador_id": 12, "tipo_documento": "comprovante_escolaridade", "status": "pendente", "prazo": ONTEM, "solicitado_por_user_id": 2},
        {"colaborador_id": 13, "tipo_documento": "rg", "status": "atendida", "prazo": "2026-10-01", "solicitado_por_user_id": 2},
        {"colaborador_id": 13, "tipo_documento": "cpf", "status": "cancelada", "prazo": "2026-10-01", "solicitado_por_user_id": 2},
    ]


REGRAS = [
    {"tipo_documento": "ctps", "tipo_contrato": "CLT", "prazo_dias_para_envio": 10, "retencao_prazo_dias": 1825, "retencao_evento_inicial": "desligamento", "obrigatorio": True},
    {"tipo_documento": "cnh", "cargo_id": 3, "prazo_dias_para_envio": 10, "retencao_prazo_dias": 1825, "retencao_evento_inicial": "data_validade", "obrigatorio": True},
    {"tipo_documento": "documentacao_responsavel_legal", "idade_maxima": 17, "prazo_dias_para_envio": 10},
]


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _instalar_api_simulada():
    api_client.auth_me = lambda token: {"autenticado": True}
    api_client.central_de_tarefas = lambda token: {}
    api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.organograma = lambda token: ORGANOGRAMA
    api_client.documentos_rh = lambda token: chamadas.append(("documentos",)) or _falha_ou("documentos", {"documentos": estado["documentos"]})
    api_client.pendencias_documento = lambda token: {"pendencias": estado["pendencias"]}
    api_client.documentos_obrigatorios = lambda token: _falha_ou("regras", {"regras": REGRAS})

    def _decisao(nome, novo):
        def f(token, doc_id, texto=None):
            chamadas.append((nome, doc_id, texto))
            _falha_ou(nome, None)
            for d in estado["documentos"]:
                if d["id"] == doc_id:
                    d["status"] = novo
            return {"sucesso": True}
        return f

    api_client.aprovar_documento = _decisao("aprovar", "aprovado")
    api_client.rejeitar_documento = _decisao("rejeitar", "rejeitado")
    api_client.arquivar_documento = _decisao("arquivar", "arquivado")
    api_client.abrir_arquivo_documento = lambda token, doc_id: chamadas.append(("arquivo", doc_id)) or _falha_ou("arquivo", {"arquivo_url": f"https://x8ki-letl-twmt.n7.xano.io/vault/{doc_id}.pdf"})
    api_client.pedir_documento = lambda token, cid, tipo, prazo, obs: chamadas.append(("pedir", cid, tipo, prazo, obs)) or _falha_ou("pedir", {"sucesso": True})
    api_client.processar_vencimentos = lambda token: chamadas.append(("vencimentos",)) or {"total_vencidos": 2, "total_alertas": 5}
    api_client.criar_regra_documento = lambda token, regra: chamadas.append(("regra", regra)) or {"sucesso": True}


_instalar_api_simulada()

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
    bruto = re.sub(r"</?strong>", "", bruto)
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def chaves(at: AppTest) -> set:
    return {b.key for b in at.button}


def abrir(at: AppTest, url_path: str) -> AppTest:
    """Abre a página pela URL (o AppTest.switch_page só acha páginas de arquivo; ver o outro teste)."""
    alvo = "" if url_path == "inicio" else url_path
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == alvo)
    return at.run()


def app(perfil: str = "RH", colaborador_id=7, **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(documentos=documentos_padrao(), pendencias=pendencias_padrao())
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Ana Ribeiro", "email": "ana@empresa.com", "perfil": perfil, "colaborador_id": colaborador_id}
    at.session_state["sessao_validada"] = True
    at = at.run()
    return abrir(at, "conferencia-de-documentos")


# ---------------------------------------------------------------------------
caso("Regras de apresentação (conferencia_modelo.py)")
from conferencia_modelo import (  # noqa: E402
    linhas_para_conferir, linhas_pendencias, linhas_regras, pessoas, resumo, validar_motivo, validar_pedido, validar_regra,
)

mapa = pessoas(ORGANOGRAMA)
docs = documentos_padrao()
linhas = {l["id"]: l for l in linhas_para_conferir(docs, mapa, 7)}
conferir(linhas[101]["proprio"] and linhas[101]["acoes"] == [], "o próprio documento (colaborador 7 = RH logado) não tem ação")
conferir(linhas[102]["acoes"] == ["recusar", "aprovar"], "documento em análise: recusar e aprovar")
conferir(linhas[103]["acoes"] == ["recusar"] and linhas[103]["arquivo"] == "bloqueado", "arquivo bloqueado: só recusar, sem abrir")
conferir(linhas[104]["acoes"] == ["arquivar"] and linhas[104]["situacao"] == ("Vencido", "err"), "vencido: só arquivar")
conferir(linhas[107]["acoes"] == ["arquivar"] and linhas[107]["situacao"][0] == "Recusado", "recusado: só arquivar")
conferir(105 not in linhas and 106 not in linhas, "aprovado e arquivado não entram na lista")
conferir([l["status"] for l in linhas_para_conferir(docs, mapa, 7)][:3] == ["pendente_analise"] * 3, "os que aguardam análise vêm primeiro")
conferir({l["id"] for l in linhas_para_conferir(docs, mapa, 7, "cnh")} == {101, 104}, "filtro por tipo")
conferir(linhas[102]["pessoa"] == "Juliana Prado" and linhas[102]["detalhe"] == "TI", "nome e departamento vêm do organograma")
r = resumo(docs, pendencias_padrao(), HOJE)
conferir(r == {"aguardando": 3, "vencidos": 1, "pendencias": 2, "aprovados_mes": 1}, f"indicadores do topo ({r})")
pend = linhas_pendencias(pendencias_padrao(), mapa, 1, HOJE)
conferir(len(pend) == 3 and all(p["documento"] != "CPF" for p in pend), "pendência cancelada não aparece")
conferir(any(p["situacao"] == ("Atrasada", "err") for p in pend) and pend[-1]["situacao"] == ("Atendida", "ok"), "prazo vencido vira 'Atrasada'; atendidas no fim")
conferir([p["pedido_por"] for p in pend if p["documento"] == "CTPS"] == ["Você"] and "RH" in [p["pedido_por"] for p in pend], "'Pedido por': Você ou RH (sem buscar a lista de usuários)")
reg = linhas_regras(REGRAS, {3: "Motorista"}, {})
conferir(reg[0]["vale_para"] == "Contrato CLT" and reg[0]["guardar"] == "5 anos depois do desligamento", "regra: contrato e prazo de guarda por extenso")
conferir(reg[1]["vale_para"] == "Cargo: Motorista" and reg[2]["vale_para"] == "Até 17 anos" and reg[2]["guardar"] == "—", "regra: cargo, idade e guarda vazia")
conferir(validar_motivo("abc") and validar_motivo("Imagem cortada") is None, "motivo da recusa: no mínimo 5 caracteres")
conferir(validar_pedido(None, "ctps", HOJE, HOJE) and validar_pedido(11, "ctps", HOJE - timedelta(days=1), HOJE) and validar_pedido(11, "ctps", HOJE, HOJE) is None, "pedido: colaborador, documento e prazo não passado")
conferir(validar_regra(None, 10, 5) and validar_regra("ctps", 10, 5) is None, "nova regra: documento obrigatório")

# ---------------------------------------------------------------------------
caso("Perfis: menu e acesso")
at = app()
conferir("Conferência de documentos" in texto(at) and "Aguardando análise" in texto(at), "RH abre a tela")
conferir({"nav_Colaboradores", "nav_Pedidos LGPD"} <= chaves(at), "RH vê o grupo 'RH' do menu")
at = app(perfil="COLABORADOR", colaborador_id=9)
conferir("Esta tela é só do RH e do Admin." in texto(at) and ("documentos",) not in chamadas, "colaborador que abre o endereço vê 'permissão negada' sem chamar a API")
conferir("nav_Colaboradores" not in chaves(at), "colaborador não vê o grupo 'RH'")
at = app(perfil="ADMIN", colaborador_id=None, erro_documentos=ApiError("Somente RH ou ADMIN podem listar documentos.", 403))
conferir("Somente RH ou ADMIN" in texto(at), "403 do backend vira mensagem, sem derrubar a tela")

# ---------------------------------------------------------------------------
caso("Aba 'Para conferir' (Figma 418:1108)")
at = app()
k = chaves(at)
conferir("Seu: outro RH decide" in texto(at) and "rh_aprovar_101" not in k and "rh_recusar_101" not in k, "o próprio documento aparece sem botões")
conferir({"rh_recusar_102", "rh_aprovar_102", "rh_recusar_103", "rh_arquivar_104", "rh_arquivar_107"} <= k and "rh_aprovar_103" not in k, "botões conforme a situação de cada linha")
conferir("rh_abrir_103" not in k and "Bloqueado" in texto(at), "arquivo bloqueado não oferece 'Abrir'")
conferir(not [b.label for b in at.button if re.search(r"exclu|apagar|deletar", b.label, re.I)], "nenhuma opção de excluir")
for rotulo, valor in (("Aguardando análise", "3"), ("Vencidos para processar", "1"), ("Pendências abertas", "2"), ("Aprovados no mês", "1")):
    conferir(re.search(rf"{rotulo} {valor}\b", texto(at)) is not None, f"indicador '{rotulo}' = {valor}")

caso("Aprovar")
at.button(key="rh_aprovar_102").click()
at = at.run()
conferir("Juliana Prado" in texto(at) and at.text_area(key="rh_aprovar_obs") is not None, "modal com o resumo e a observação opcional")
at.text_area(key="rh_aprovar_obs").set_value("Conferido.")
at.button(key="rh_aprovar_ok").click()
at = at.run()
conferir(("aprovar", 102, "Conferido.") in chamadas, "aprova o documento 102 com a observação")
conferir("modal_rh" not in at.session_state and "rh_aprovar_102" not in chaves(at), "o modal fecha e a linha sai da lista")

caso("Recusar")
at = app()
at.button(key="rh_recusar_103").click()
at = at.run()
conferir("Arquivo bloqueado na verificação" in texto(at), "recusar arquivo bloqueado mostra o motivo do bloqueio")
at.button(key="rh_recusar_ok").click()
at = at.run()
conferir("pelo menos 5 caracteres" in texto(at) and not any(c[0] == "rejeitar" for c in chamadas), "sem motivo, não recusa")
at.text_area(key="rh_recusar_motivo").set_value("Envie o arquivo em PDF.")
at.button(key="rh_recusar_ok").click()
at = at.run()
conferir(("rejeitar", 103, "Envie o arquivo em PDF.") in chamadas, "recusa com o motivo, que o colaborador vê")
at = app(erro_rejeitar=ApiError("Voce nao pode decidir uma solicitacao propria.", 403))
at.button(key="rh_recusar_102").click()
at = at.run()
at.text_area(key="rh_recusar_motivo").set_value("Imagem cortada.")
at.button(key="rh_recusar_ok").click()
at = at.run()
conferir("Voce nao pode decidir" in texto(at) and "modal_rh" in at.session_state, "erro do backend aparece no modal, que continua aberto")

caso("Arquivar, abrir o arquivo e processar vencidos")
at = app()
at.button(key="rh_arquivar_104").click()
at = at.run()
conferir("Arquivar não apaga" in texto(at) and "Venceu em" in texto(at), "modal explica que arquivar não apaga")
at.button(key="rh_arquivar_ok").click()
at = at.run()
conferir(("arquivar", 104, None) in chamadas and "rh_arquivar_104" not in chaves(at), "arquiva sem observação e a linha sai")
at.button(key="rh_abrir_102").click()
at = at.run()
conferir(("arquivo", 102) in chamadas and any(getattr(e, "label", "") == "Abrir arquivo" for e in at.get("link_button")), "'Abrir' pede o link ao backend (auditado)")
at = app(erro_arquivo=ApiError("Voce nao possui permissao para acessar este arquivo.", 403))
at.button(key="rh_abrir_102").click()
at = at.run()
conferir("Voce nao possui permissao" in texto(at), "acesso negado ao arquivo vira mensagem")
at = app()
at.button(key="rh_btn_vencidos").click()
at = at.run()
conferir(("vencimentos",) in chamadas and 'Viraram "Vencido" 2' in texto(at) and "Alertas enviados 5" in texto(at), "'Processar vencidos' mostra o resultado")
at.button(key="rh_vencidos_fechar").click()
at = at.run()
conferir("modal_rh" not in at.session_state and chamadas.count(("vencimentos",)) == 1, "'Fechar' não processa de novo")

caso("Pedir documento (Figma 244:1059)")
at = app()
at.button(key="rh_btn_pedir").click()
at = at.run()
at.button(key="rh_pedir_ok").click()
at = at.run()
conferir("Escolha o colaborador." in texto(at) and not any(c[0] == "pedir" for c in chamadas), "sem colaborador, não pede")
at.selectbox(key="rh_pedir_colab").set_value(11)
at.selectbox(key="rh_pedir_tipo").set_value("certificado_reservista")
at.text_input(key="rh_pedir_obs").set_value("Frente e verso.")
at.button(key="rh_pedir_ok").click()
at = at.run()
pedido = next((c for c in chamadas if c[0] == "pedir"), None)
conferir(pedido is not None and pedido[1:3] == (11, "certificado_reservista") and pedido[4] == "Frente e verso.", "pede o documento para a pessoa certa, com a observação")
conferir(pedido is not None and pedido[3] == (HOJE + timedelta(days=10)).isoformat(), "prazo padrão de 10 dias, em aaaa-mm-dd")

caso("Abas 'Pendências pedidas' e 'Obrigatórios por cargo'")
at = app()
at.button_group(key="rh_aba").set_value("Pendências pedidas")
at = at.run()
conferir("Atrasada" in texto(at) and "Atendida" in texto(at) and "Pedido por" in texto(at), "pendências com situação e quem pediu")
at.button_group(key="rh_aba").set_value("Obrigatórios por cargo")
at = at.run()
conferir("Contrato CLT" in texto(at) and "Cargo: Motorista" in texto(at) and "rh_btn_regra" in chaves(at), "regras e o botão 'Nova regra'")
at.button(key="rh_btn_regra").click()
at = at.run()
at.selectbox(key="rh_regra_tipo").set_value("ctps")
at.selectbox(key="rh_regra_contrato").set_value("CLT")
at.button(key="rh_regra_ok").click()
at = at.run()
regra = next((c[1] for c in chamadas if c[0] == "regra"), {})
conferir(regra.get("tipo_documento") == "ctps" and regra.get("tipo_contrato") == "CLT" and regra.get("prazo_dias_para_envio") == 10, "nova regra com documento, contrato e prazo")
conferir(regra.get("retencao_prazo_dias") == 1825 and regra.get("retencao_evento_inicial") == "desligamento" and regra.get("cargo_id") is None, "guarda de 5 anos depois do desligamento; sem cargo = todos")
at = app(erro_regras=ApiError("Erro inesperado. Tente novamente.", 500))
at.button_group(key="rh_aba").set_value("Obrigatórios por cargo")
at = at.run()
conferir("Erro inesperado" in texto(at), "erro ao carregar as regras fica na aba")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
