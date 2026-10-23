"""Testes das telas de Privacidade e Documentos do frontend Streamlit, sem navegador e sem rede.

Tarefas 5, 59 e 67 (aviso de privacidade, Configurações → Privacidade, "Baixar meus dados") e
26 a 28, 62 e 68 (Documentos, Documentos pendentes, envio) da change concluir-frontend-streamlit.

Roda o app com o AppTest do Streamlit e uma API simulada (as funções de `frontend/api_client.py`
trocadas por versões em memória, com dados fictícios). Confere:

  Aviso ............ o texto da tela é o do documento, sem a coluna Registro e sem a nota interna;
                     abre sem login pelo link da tela Entrar, sem chamar a API
  Menu da conta .... Configurações e "Sair da conta"
  Privacidade ...... cartões, preferências (gravar e desfazer em erro), pedidos, estados vazio,
                     erro e conta sem colaborador; exportação só com os dados do próprio usuário
  Documentos ....... selos por status, arquivo bloqueado (62), pendências, "Ver" auditado,
                     acesso negado ao arquivo, nenhuma opção de exclusão (28), envio validado

Uso (na raiz do repositório):
    python tools/testar_privacidade_documentos.py

Sai com código 1 se algum caso falhar.
"""

import html as html_lib
import inspect
import json
import logging
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
from api_client import ApiError  # noqa: E402

api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}  # sino do topo (sem rede)

# Configurações: abas Segurança e Notificações (change configuracoes-seguranca-notificacoes), sem rede.
api_client.minhas_sessoes = lambda token: {"sessoes": [], "sessao_atual_id": None}
api_client.minhas_preferencias_aviso = lambda token: {"preferencias": []}

APP = RAIZ / "frontend" / "app.py"

chamadas: list[tuple] = []
estado: dict = {}

DOCUMENTOS = [
    {"id": 11, "tipo": "rg", "nome_documento": "RG", "status": "aprovado", "estado_verificacao": "liberado", "created_at": "2026-01-02T10:00:00Z"},
    {"id": 12, "tipo": "ctps", "nome_documento": "CTPS", "status": "pendente_analise", "estado_verificacao": "liberado", "created_at": "2026-08-30T10:00:00Z"},
    {"id": 13, "tipo": "aso_admissional", "nome_documento": "ASO admissional", "status": "vencido", "data_validade": "2026-01-01"},
    {"id": 14, "tipo": "comprovante_residencia", "nome_documento": "Comprovante de residência", "status": "rejeitado", "updated_at": "2026-08-15T10:00:00Z"},
    {"id": 15, "tipo": "comprovante_residencia", "nome_documento": "Comprovante de residência", "status": "substituido", "updated_at": "2026-08-15T10:00:00Z"},
    {"id": 16, "tipo": "cnh", "nome_documento": "CNH", "status": "pendente_analise", "estado_verificacao": "bloqueado",
     "motivo_bloqueio": "Extensao de arquivo nao permitida: .exe.", "created_at": "2026-10-01T10:00:00Z"},
]
PENDENCIAS = [
    {"tipo_documento": "ctps", "status": "atendida", "atendida_por_documento_id": 12, "prazo": "2026-10-10"},
    {"tipo_documento": "certificado_reservista", "status": "pendente", "prazo": "2026-10-10"},
    {"tipo_documento": "comprovante_escolaridade", "status": "pendente", "prazo": "2026-10-15", "observacao": "Pedido pelo RH em 02/10"},
    {"tipo_documento": "cpf", "status": "cancelada", "prazo": "2026-10-01"},
]
PEDIDOS = [
    {"id": 1, "tipo": "privacidade_lgpd", "subtipo_lgpd": "correcao", "status": "em_analise", "created_at": "2026-09-20T12:00:00Z", "prazo_resposta": "2026-10-05"},
    {"id": 2, "tipo": "privacidade_lgpd", "subtipo_lgpd": "portabilidade", "status": "atendida", "created_at": "2026-09-03T12:00:00Z", "prazo_resposta": "2026-09-18"},
    {"id": 3, "tipo": "declaracao", "status": "recebida"},
]


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _instalar_api_simulada():
    api_client.auth_me = lambda token: {"autenticado": True}
    api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}  # menu Equipe (tarefa 83)
    api_client.prazo_correcao = lambda token: {"prazo_dias": None}  # prazo de correção (tarefa 79)
    api_client.logout = lambda token: chamadas.append(("logout",)) or {}
    api_client.central_de_tarefas = lambda token: {}
    api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.meu_humor = lambda token: {"ciclo": 0, "respondeu": True}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.minhas_preferencias_privacidade = lambda token: chamadas.append(("prefs",)) or _falha_ou(
        "prefs", dict(estado["preferencias"], padrao=False, menor_de_idade=False)
    )

    def _salvar(token, ocultar_aniversario, ocultar_mural):
        chamadas.append(("salvar_prefs", ocultar_aniversario, ocultar_mural))
        _falha_ou("salvar", None)
        estado["preferencias"] = {"ocultar_aniversario": ocultar_aniversario, "ocultar_mural": ocultar_mural}
        return {"sucesso": True}

    api_client.salvar_preferencias_privacidade = _salvar
    api_client.minhas_solicitacoes = lambda token: _falha_ou("pedidos", {"solicitacoes": estado["pedidos"]})
    api_client.criar_pedido_privacidade = lambda token, subtipo, descricao: chamadas.append(("pedido", subtipo, descricao)) or {"sucesso": True}
    api_client.meus_dados = lambda token, formato="json": chamadas.append(("meus_dados", formato)) or {
        "sucesso": True, "formato": formato, "usuario": {"id": 1, "nome": "Leonardo dos Santos"}, "documentos": [], "csv": "categoria,id\n"
    }
    api_client.meus_documentos = lambda token: chamadas.append(("meus_documentos",)) or _falha_ou("documentos", {"documentos": estado["documentos"]})
    api_client.minhas_pendencias_documento = lambda token: {"pendencias": estado["pendencias"]}
    api_client.abrir_arquivo_documento = lambda token, doc_id: chamadas.append(("arquivo", doc_id)) or _falha_ou(
        "arquivo", {"arquivo_url": f"https://x8ki-letl-twmt.n7.xano.io/arquivo/{doc_id}.pdf", "expira_em_segundos": 300}
    )
    api_client.enviar_documento = lambda token, dados: chamadas.append(("enviar", dados)) or _falha_ou("enviar", {"sucesso": True})
    api_client.preparar_envio_arquivo = lambda token, cid, ext: chamadas.append(("preparar", cid, ext)) or _falha_ou("preparar", {
        "upload_url": f"https://armazenamento.exemplo/upload/abc.{ext}?token=t", "arquivo_url": f"https://armazenamento.exemplo/object/documentos/abc.{ext}"})
    api_client.subir_arquivo = lambda url, conteudo, tipo: chamadas.append(("subir", url, len(conteudo), tipo)) or _falha_ou("subir", None)


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
    """Texto visível dos st.html, sem as tags e com as entidades resolvidas."""
    bruto = " ".join(str(e.value) for e in at.get("html"))
    bruto = re.sub(r"</?strong>", "", bruto)  # tags em linha não separam palavras
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def botoes(at: AppTest) -> list[str]:
    return [b.label for b in at.button]


def app_logado(destino: str, perfil: str = "COLABORADOR", colaborador_id=9, **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(
        preferencias={"ocultar_aniversario": False, "ocultar_mural": True},
        pedidos=list(PEDIDOS),
        documentos=list(DOCUMENTOS),
        pendencias=list(PENDENCIAS),
    )
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Leonardo dos Santos", "email": "leonardo@empresa.com", "perfil": perfil, "colaborador_id": colaborador_id}
    at.session_state["sessao_validada"] = True
    if destino == "configuracoes":
        at.session_state["cfg_aba"] = "Privacidade"  # a aba padrão é Segurança (change configuracoes-seguranca-notificacoes)
    return abrir(at.run(), destino)


def abrir(at: AppTest, url_path: str) -> AppTest:
    """Abre a página pela URL, como o navegador. O AppTest.switch_page só acha páginas de arquivo;
    as nossas são funções (st.Page(callable)), então o teste usa o registro de páginas do AppTest.
    Trocar de página com uma marca `ir_*` também funcionaria, mas o clique de um botão na rodada
    seguinte se perderia (a troca reinicia a rodada)."""
    alvo = "" if url_path == "inicio" else url_path  # a página padrão (Início) é registrada sem caminho
    pagina = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == alvo)
    at._page_hash = pagina
    return at.run()


# ---------------------------------------------------------------------------
caso("Aviso: o texto da tela é o do documento (tarefa 59)")
import aviso_privacidade  # noqa: E402

aviso = aviso_privacidade.carregar()
conferir(len(aviso["tabela"]["linhas"]) == 18 and all(len(l) == 3 for l in aviso["tabela"]["linhas"]), "18 finalidades, cada uma com 3 colunas (a coluna Registro fica de fora)")
markdown = aviso_privacidade.ARQUIVO.read_text(encoding="utf-8")
paragrafos = [
    aviso_privacidade.texto_simples(re.sub(r"^(?:- \*\*[^*]+:\*\* |- |\d+\. |#+ )", "", l)).strip().rstrip(".")
    for l in markdown.splitlines()
    if l.strip() and not l.startswith((">", "|", "**Versão:**"))
]
at = AppTest.from_file(str(APP), default_timeout=30)
at.session_state["ir_aviso"] = True
at = at.run()
tela = texto(at)
faltando = [p for p in paragrafos if p.replace("Aviso de privacidade do ConectaRH", "Aviso de privacidade") not in tela]
conferir(not faltando, f"todo parágrafo do documento aparece na tela ({len(paragrafos) - len(faltando)} de {len(paragrafos)})")
for p in faltando:
    print("     falta:", p[:100])
conferir("Rascunho de 10/10/2026" in tela and "Bases legais e prazos: a confirmar com o jurídico" in tela, "selos da versão (Figma 285:874)")
conferir(not re.search(r"\bF\d\d\b", tela) and "Registro" not in tela and "Nota da documentação" not in tela, "sem os códigos F01–F19, a coluna Registro e a nota interna")
conferir("grava o endereço IP e o dispositivo" in tela and "6 meses" in tela, "IP e dispositivo: gravados e guardados por 6 meses (tarefa 70)")

caso("Aviso sem login: link da tela Entrar (tarefa 5, Figma 282:868)")
chamadas.clear()
at = AppTest.from_file(str(APP), default_timeout=30).run()
conferir("btn_link_aviso" in [b.key for b in at.button] and "Como usamos seus dados:" in texto(at), "tela Entrar mostra 'Como usamos seus dados: Aviso de privacidade →'")
at.button(key="btn_link_aviso").click()
at = at.run()
conferir("Quais dados guardamos e por quê" in texto(at) and "token" not in at.session_state, "o link abre o aviso sem sessão")
conferir(not chamadas, "o aviso não chama a API")
at.button(key="btn_aviso_voltar").click()
at = at.run()
conferir("Bem-vindo de volta" in texto(at), "'← Voltar para Entrar' volta ao login")

# ---------------------------------------------------------------------------
caso("Menu da conta (Figma 198:158)")
at = app_logado("inicio")
conferir("Perfil: Colaborador" in texto(at) and {"Configurações", "Sair da conta"} <= set(botoes(at)), "chip abre perfil, Configurações e Sair da conta")
at.button(key="btn_menu_config").click()
at = at.run()
conferir("Cuide da sua senha, dos seus acessos" in texto(at), "'Configurações' abre Configurações → Privacidade")
at = abrir(at, "inicio")
at.button(key="btn_menu_sair").click()
at = at.run()
conferir(("logout",) in chamadas and "token" not in at.session_state, "'Sair da conta' encerra a sessão no backend e apaga o token")
conferir("Você saiu da sua conta." in texto(at), "volta a Entrar com o aviso de saída")

# ---------------------------------------------------------------------------
caso("Tema claro e escuro (menu da conta, Figma 198:158)")


def css(at: AppTest) -> str:
    return " ".join(str(e.value) for e in at.get("html"))


at = app_logado("inicio")
conferir(at.button_group(key="menu_tema").value == "Claro" and "crh-tema-escuro" not in css(at), "sem escolha, o app abre no tema claro")
at.button_group(key="menu_tema").set_value("Escuro")
at = at.run()
conferir(at.session_state["tema"] == "escuro" and "crh-tema-escuro" in css(at), "'Escuro' troca o tema na hora")
conferir("crh_tema=escuro" in css(at), "a escolha fica num cookie de preferência (só \"claro\" ou \"escuro\")")
at = abrir(at, "documentos")
conferir("crh-tema-escuro" in css(at) and "Documentos cadastrais" in texto(at), "o tema vale nas outras telas")
at.button_group(key="menu_tema").set_value("Claro")
at = at.run()
conferir(at.session_state["tema"] == "claro" and "crh-tema-escuro" not in css(at) and "crh_tema=claro" in css(at), "'Claro' volta e grava a nova escolha")
at = AppTest.from_file(str(APP), default_timeout=30)
at.session_state["tema"] = "escuro"
at = at.run()
conferir("crh-tema-escuro" not in css(at) and "Bem-vindo de volta" in texto(at), "a tela Entrar continua grafite no tema escuro")
at.button(key="btn_link_aviso").click()
at = at.run()
conferir("crh-tema-escuro" in css(at), "o aviso sem login também segue o tema")

# ---------------------------------------------------------------------------
caso("Configurações → Privacidade: sucesso (Figma 286:878)")
at = app_logado("configuracoes")
t = texto(at)
for trecho in ("Aviso de privacidade", "Meus dados", "Fale com o encarregado", "O que os colegas veem", "Meus pedidos de privacidade"):
    conferir(trecho in t, f"cartão '{trecho}'")
conferir("Rascunho de 10/10/2026" in t, "versão do aviso no cartão")
conferir("a definir" in t and "privacidade@conectarh.com" in t, "encarregado e contato vêm do aviso")
conferir(at.toggle(key="pref_aniversario").value is True and at.toggle(key="pref_mural").value is False, "botões mostram o que está gravado (mural oculto)")
conferir("Correção de dados" in t and "Em análise" in t and "responder até 05/10/2026" in t, "pedido em análise com o prazo de resposta")
conferir("Cópia dos meus dados" in t and "Concluído" in t, "pedido atendido aparece como Concluído")
conferir("Declaração" not in t and t.count("Aberto em") == 2, "só os pedidos de privacidade entram na lista")
conferir(not any(isinstance(c, tuple) and c[0] in ("salvar_prefs", "meus_dados") for c in chamadas), "abrir a tela não grava nada nem exporta dados")

caso("Preferências: gravar e desfazer quando o backend recusa")
at.toggle(key="pref_mural").set_value(True)
at = at.run()
conferir(("salvar_prefs", False, False) in chamadas, "ligar o mural grava ocultar_mural=False junto com ocultar_aniversario")
estado["erro_salvar"] = ApiError("Erro inesperado. Tente novamente.", 500)
at.toggle(key="pref_aniversario").set_value(False)
at = at.run()
conferir(at.toggle(key="pref_aniversario").value is True, "com erro, o botão volta ao valor gravado")

caso("Privacidade: vazio, erro e conta sem colaborador")
at = app_logado("configuracoes", pedidos=[])
conferir("Você ainda não fez nenhum pedido." in texto(at), "vazio: sem pedidos")
at = app_logado("configuracoes", pedidos=[], erro_prefs=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado. Tente novamente." in texto(at) and "Meus dados" in texto(at), "erro nas preferências fica no cartão; o resto da tela continua")
at = app_logado("configuracoes", perfil="ADMIN", colaborador_id=None, **{
    "erro_prefs": ApiError("Nao existe um colaborador vinculado a esta conta.", 404),
    "erro_pedidos": ApiError("Nao existe um colaborador vinculado a esta conta.", 404),
})
conferir("não tem cadastro de colaborador" in texto(at) and "Perfil: Admin" in texto(at), "conta de Admin sem colaborador: mensagem em vez de erro")
at = app_logado("configuracoes")
at.button(key="btn_ler_aviso").click()
at = at.run()
conferir("Quais dados guardamos e por quê" in texto(at) and "btn_aviso_voltar_priv" in [b.key for b in at.button], "'Ler aviso completo →' abre o aviso logado com '← Voltar para Privacidade'")

caso("Fazer um pedido (Figma 224:2379)")
at = app_logado("configuracoes")
at.button(key="btn_fazer_pedido").click()
at = at.run()
conferir([r.key for r in at.radio] == ["pedido_subtipo"] and len(at.radio(key="pedido_subtipo").options) == 3, "modal abre com as 3 opções do Figma")
at.button(key="btn_pedido_enviar").click()
at = at.run()
conferir("Escolha o que você precisa." in texto(at) and not any(c[0] == "pedido" for c in chamadas), "sem escolher o tipo, não envia")
at.radio(key="pedido_subtipo").set_value("correcao")
at.text_area(key="pedido_descricao").set_value("Meu sobrenome está escrito errado no cadastro.")
at.button(key="btn_pedido_enviar").click()
at = at.run()
conferir(("pedido", "correcao", "Meu sobrenome está escrito errado no cadastro.") in chamadas, "envia o pedido privacidade_lgpd com o subtipo e o detalhe")
conferir("modal_privacidade" not in at.session_state and not at.radio, "o modal fecha depois do envio")

caso("Baixar meus dados (Figma 286:1062 e 286:1092)")
at = app_logado("configuracoes")
at.button(key="btn_baixar_dados").click()
at = at.run()
conferir(at.radio(key="exp_formato").value == "json" and "Não inclui respostas de pesquisa de clima" in texto(at), "modal abre em JSON e diz o que o arquivo inclui")
conferir(not any(c[0] == "meus_dados" for c in chamadas), "abrir o modal não exporta nada (a auditoria só registra a exportação de fato)")
at.radio(key="exp_formato").set_value("csv")
at.button(key="btn_exp_baixar").click()
at = at.run()
conferir(("meus_dados", "csv") in chamadas, "'Baixar arquivo' pede o CSV ao backend")
conferir("Arquivo gerado. O download começou (meus_dados.csv)." in texto(at) and "Gerar de novo" in botoes(at), "estado de sucesso com o nome do arquivo")
at.button(key="btn_exp_fechar").click()
at = at.run()
conferir("exportacao_gerada" not in at.session_state and "modal_privacidade" not in at.session_state, "'Fechar' apaga o arquivo da sessão")

caso("Baixar meus dados e pedido (modelo)")
from privacidade_modelo import arquivo_exportado, validar_pedido  # noqa: E402

nome, conteudo, mime = arquivo_exportado({"sucesso": True, "formato": "json", "usuario": {"id": 1}, "csv": ""}, "json")
conferir(nome == "meus_dados.json" and json.loads(conteudo) == {"usuario": {"id": 1}} and mime == "application/json", "JSON sem os campos técnicos")
nome, conteudo, _ = arquivo_exportado({"csv": "categoria,id\ndocumentos,1\n"}, "csv")
conferir(nome == "meus_dados.csv" and conteudo.decode("utf-8-sig").startswith("categoria,id"), "CSV é o texto montado pelo backend")
conferir(list(inspect.signature(api_client.meus_dados).parameters) == ["token", "formato"], "a exportação não recebe id de ninguém: só o token")
conferir(validar_pedido(None, "texto qualquer") and validar_pedido("correcao", "abc") and validar_pedido("correcao", "Meu sobrenome está errado") is None, "pedido exige o tipo e um detalhe de 5 caracteres ou mais")

# ---------------------------------------------------------------------------
caso("Documentos: lista e selos (Figma 41:26)")
at = app_logado("documentos")
t = texto(at)
conferir("Documentos cadastrais" in t and "Enviar documento" in botoes(at), "título da lista e botão 'Enviar documento'")
for trecho in ("Enviado em 02/01/2026", "Aprovado", "Em análise", "Válido até 01/01/2026", "Vencido", "Rejeitado em 15/08/2026",
               "Comprovante de residência (anterior)", "Substituído em 15/08/2026"):
    conferir(trecho in t, f"lista mostra '{trecho}'")
conferir("Arquivo bloqueado" in t and "Extensao de arquivo nao permitida" in t, "arquivo bloqueado na verificação: selo próprio e o motivo (tarefa 62)")
excluir = [b for b in botoes(at) if re.search(r"exclu|apagar|remover|deletar|arquivar", b, re.I)]
conferir(not excluir, "nenhuma opção de excluir ou arquivar na tela (tarefa 28)")
conferir(not [n for n in dir(api_client) if re.search(r"exclu|delet|apagar", n, re.I)], "o cliente da API não tem função de exclusão")

caso("Documentos pendentes (Figma 309:1249)")
conferir("Documentos obrigatórios da sua admissão" in t, "com pendência aberta, o título muda para a admissão")
ordem = [t.find(x) for x in ("CTPS", "Certificado de reservista", "Comprovante de escolaridade")]
conferir(all(i >= 0 for i in ordem) and ordem == sorted(ordem), "enviados primeiro, depois os que faltam pelo prazo")
conferir("Cpf" not in t and t.count("Pendente") == 2, "pedido cancelado não aparece")
conferir(botoes(at).count("Enviar →") == 2 and botoes(at).count("Ver") == 1, "'Enviar →' nos que faltam e 'Ver' no enviado")
at.button(key="btn_doc_ver_0").click()
at = at.run()
conferir(("arquivo", 12) in chamadas and any(getattr(e, "label", "") == "Abrir arquivo" for e in at.get("link_button")), "'Ver' pede o link ao backend (auditado) e mostra 'Abrir arquivo'")
at = app_logado("documentos", erro_arquivo=ApiError("Voce nao possui permissao para acessar este arquivo.", 403))
at.button(key="btn_doc_ver_0").click()
at = at.run()
conferir("Voce nao possui permissao" in texto(at), "permissão negada ao arquivo vira mensagem, sem derrubar a tela")

caso("Documentos: vazio, sem colaborador e erro")
at = app_logado("documentos", documentos=[], pendencias=[])
conferir("Você ainda não enviou nenhum documento." in texto(at) and "Envie e acompanhe seus documentos obrigatórios" in texto(at), "vazio: sem documentos e sem pendências")
at = app_logado("documentos", perfil="RH", colaborador_id=None, erro_documentos=ApiError("x", 404))
conferir("Sua conta não tem cadastro de colaborador" in texto(at), "conta sem colaborador")
at = app_logado("documentos", erro_documentos=ApiError("Colaborador desligado nao pode consultar documentos.", 403))
conferir("Colaborador desligado nao pode consultar documentos." in texto(at), "bloqueado (desligado): mensagem do backend")

caso("Enviar documento com o arquivo anexado (Figma 309:1591; change anexo-de-arquivos)")
import streamlit  # noqa: E402

from documentos_modelo import TAMANHO_MAXIMO, TIPOS_ENVIO, extensao, validar_envio  # noqa: E402


class ArquivoFicticio:
    """O AppTest não simula o envio de arquivo: o `st.file_uploader` do teste devolve este objeto."""

    def __init__(self, nome: str, conteudo: bytes):
        self.name, self.size, self._conteudo = nome, len(conteudo), conteudo

    def getvalue(self) -> bytes:
        return self._conteudo


anexo: dict = {"arquivo": None, "rotulos": []}
_file_uploader_original = streamlit.file_uploader


def _file_uploader_teste(label, *args, **kwargs):
    anexo["rotulos"].append((label, tuple(kwargs.get("type") or ())))
    return anexo["arquivo"]


streamlit.file_uploader = _file_uploader_teste

from datetime import date  # noqa: E402

from documentos_modelo import campos, linhas_dados, montar_campos, validar_campos  # noqa: E402


def rotulos_campos(at: AppTest) -> list[str]:
    return [w.label for w in list(at.text_input) + list(at.date_input) + list(at.selectbox) if str(w.key).startswith("env_c_")]


at = app_logado("documentos")
at.button(key="btn_doc_enviar_1").click()
at = at.run()
conferir(at.selectbox(key="env_tipo").value == "certificado_reservista", "'Enviar →' abre o modal já com o tipo da pendência")
conferir(("Arquivo", ("pdf", "jpg", "jpeg", "png")) in anexo["rotulos"] and all(t.key != "env_link" for t in at.text_input),
         "o modal pede o arquivo (PDF, JPG ou PNG), sem campo de link")
conferir(rotulos_campos(at) == ["Número do certificado", "Data de emissão"], "reservista: só número do certificado e data de emissão")
at.button(key="btn_env_enviar").click()
at = at.run()
conferir("Preencha \"Número do certificado\"." in texto(at) and not any(c[0] in ("preparar", "enviar") for c in chamadas), "campo obrigatório do tipo em branco: aviso, sem chamar a API")
at.text_input(key="env_c_certificado_reservista_numero_documento").set_value("123456")
at.date_input(key="env_c_certificado_reservista_data_emissao").set_value(date(2020, 5, 4))
at.button(key="btn_env_enviar").click()
at = at.run()
conferir("Anexe o arquivo do documento." in texto(at) and not any(c[0] in ("preparar", "enviar") for c in chamadas), "sem arquivo: mensagem no modal, sem chamar a API")
anexo["arquivo"] = ArquivoFicticio("Reservista.JPG", b"\xff\xd8 foto ficticia")
at.button(key="btn_env_enviar").click()
at = at.run()
enviado = next((c[1] for c in chamadas if c[0] == "enviar"), {})
ordem_chamadas = [c[0] for c in chamadas if c[0] in ("preparar", "subir", "enviar")]
conferir(ordem_chamadas == ["preparar", "subir", "enviar"] and ("preparar", 9, "jpg") in chamadas
         and ("subir", "https://armazenamento.exemplo/upload/abc.jpg?token=t", 16, "image/jpeg") in chamadas,
         "pede o endereço de envio, manda a foto (image/jpeg) e só depois cadastra")
conferir(enviado.get("tipo") == "certificado_reservista" and enviado.get("colaborador_id") == 9
         and enviado.get("arquivo_url") == "https://armazenamento.exemplo/object/documentos/abc.jpg", "cadastra com o tipo, o colaborador da sessão e o endereço do arquivo")
conferir(enviado.get("numero_documento") == "123456" and enviado.get("data_emissao") == "2020-05-04" and "dados" not in enviado
         and enviado.get("nome_documento") == "Certificado de reservista", "reservista: número e emissão nas colunas, sem dados extras")
conferir("modal_documento" not in at.session_state and not any(str(k).startswith("env_") for k in at.session_state), "o modal fecha e limpa os campos depois do envio")

caso("Campos por tipo de documento (change campos-por-tipo-de-documento)")
at = app_logado("documentos")
at.button(key="btn_doc_novo").click()
at = at.run()
at.selectbox(key="env_tipo").set_value("rg")
at = at.run()
conferir(rotulos_campos(at) == ["Número do RG", "Órgão emissor", "Data de expedição", "UF"], "RG: número, órgão emissor, UF e data de expedição")
at.text_input(key="env_c_rg_numero_documento").set_value("12.345.678-9")
at.text_input(key="env_c_rg_orgao_emissor").set_value("ssp")
at.selectbox(key="env_c_rg_estado_de_emissao").set_value("SP")
at.date_input(key="env_c_rg_data_emissao").set_value(date(2015, 2, 1))
at.button(key="btn_env_enviar").click()
at = at.run()
enviado = next((c[1] for c in chamadas if c[0] == "enviar"), {})
conferir(enviado.get("numero_documento") == "12.345.678-9" and enviado.get("estado_de_emissao") == "SP" and enviado.get("data_emissao") == "2015-02-01"
         and enviado.get("dados") == {"orgao_emissor": "ssp"}, "RG: colunas comuns e o órgão emissor em dados")
at = app_logado("documentos")
at.button(key="btn_doc_novo").click()
at = at.run()
at.selectbox(key="env_tipo").set_value("cpf")
at = at.run()
conferir(rotulos_campos(at) == ["Número do CPF"], "CPF: só o número, sem data")
at.text_input(key="env_c_cpf_numero_documento").set_value("111.111.111-11")
at.button(key="btn_env_enviar").click()
at = at.run()
conferir("CPF inválido" in texto(at) and not any(c[0] == "enviar" for c in chamadas), "CPF com dígitos errados: aviso antes da API")
at.selectbox(key="env_tipo").set_value("cnh")
at = at.run()
conferir(sorted(rotulos_campos(at)) == ["Categoria", "Data de emissão", "Número de registro", "UF", "Validade"]
         and at.selectbox(key="env_c_cnh_categoria").options[:3] == ["A", "B", "AB"],
         "trocar o tipo troca os campos: CNH com registro, categoria e validade")
at = app_logado("documentos", erro_enviar=ApiError("O CPF informado nao confere com o do cadastro. Se o cadastro estiver errado, peca a correcao ao RH.", 400))
at.button(key="btn_doc_novo").click()
at = at.run()
at.selectbox(key="env_tipo").set_value("cpf")
at = at.run()
at.text_input(key="env_c_cpf_numero_documento").set_value("529.982.247-25")
at.button(key="btn_env_enviar").click()
at = at.run()
conferir("nao confere com o do cadastro" in texto(at) and "modal_documento" in at.session_state, "CPF diferente da ficha: a recusa do backend aparece no modal")

hoje = date(2026, 10, 13)
conferir(validar_campos("cnh", {"numero_documento": "123.456.789-01", "categoria": "B", "estado_de_emissao": "SP", "data_emissao": date(2022, 1, 10)}, hoje)
         == "Preencha \"Validade\".", "CNH sem validade")
conferir(validar_campos("cnh", {"numero_documento": "1234567890", "categoria": "B", "estado_de_emissao": "SP", "data_emissao": date(2022, 1, 10),
                                "data_validade": date(2032, 1, 10)}, hoje) == "O número de registro da CNH tem 11 dígitos.", "CNH com 10 dígitos")
conferir(validar_campos("comprovante_residencia", {"data_emissao": date(2026, 6, 1)}, hoje) == "Envie um comprovante de residência dos últimos 90 dias."
         and validar_campos("comprovante_residencia", {"data_emissao": date(2026, 9, 1)}, hoje) is None, "comprovante de residência só dos últimos 90 dias")
conferir(validar_campos("certificado_reservista", {"numero_documento": "1", "data_emissao": date(2027, 1, 1)}, hoje) == "\"Data de emissão\" não pode ser uma data futura.",
         "data de emissão futura")
conferir(validar_campos("documentacao_migratoria", {"numero_documento": "V1", "data_emissao": date(2024, 1, 1), "data_validade": date(2023, 1, 1)}, hoje)
         == "A validade não pode ser anterior à data de emissão.", "validade antes da emissão")
conferir(validar_campos("documentacao_responsavel_legal", {"responsavel_nome": "Maria Exemplo", "responsavel_cpf": "529.982.247-25", "vinculo": "mae"}, hoje) is None
         and validar_campos("laudo_deficiencia", {"data_emissao": date(2026, 1, 1)}, hoje) == "Preencha \"CRM do médico\".", "responsável legal e laudo (com CRM)")
conferir(all(c["chave"] not in ("cid", "diagnostico") for t in ("laudo_deficiencia", "aso_admissional") for c in campos(t)), "laudo e ASO sem CID nem diagnóstico (minimização)")
conferir(montar_campos("outro", {"descricao": "Carteira do conselho", "numero_documento": " "})["nome_documento"] == "Carteira do conselho", "outro: o nome é o que a pessoa escreveu")
conferir(linhas_dados({"tipo": "cnh", "numero_documento": "12345678901", "estado_de_emissao": "SP", "data_validade": "2032-01-10", "dados": {"categoria": "AB"}})
         == [("Número de registro", "12345678901"), ("Categoria", "AB"), ("UF", "SP"), ("Validade", "10/01/2032")], "dados para o RH, na ordem do tipo e com data dd/mm/aaaa")
conferir(sorted(TIPOS_ENVIO) == sorted(campos.__globals__["CAMPOS"]), "todo tipo que a pessoa envia tem os seus campos")
conferir({"titulo_eleitor", "certidao_civil", "termo_compromisso_estagio", "cartao_cnpj", "contrato_social"} <= set(TIPOS_ENVIO),
         "tipos novos da admissão (documentos-obrigatorios-por-contrato) podem ser enviados")
conferir(validar_campos("titulo_eleitor", {"numero_documento": "1234 5678 901", "zona": "1", "secao": "2", "estado_de_emissao": "SP"}, hoje)
         == "O número do título de eleitor tem 12 dígitos." and validar_campos("cartao_cnpj", {"numero_documento": "12.345.678/0001-95", "razao_social": "Exemplo Ltda"}, hoje) is None
         and validar_campos("cartao_cnpj", {"numero_documento": "1234", "razao_social": "X"}, hoje) == "O CNPJ tem 14 dígitos.", "título com 12 dígitos e CNPJ com 14")
conferir(validar_campos("termo_compromisso_estagio", {"instituicao": "Universidade Exemplo", "data_emissao": date(2026, 11, 3), "data_validade": date(2027, 11, 2),
                                                      "apolice_seguro": "AP-1"}, hoje) is None
         and validar_campos("termo_compromisso_estagio", {"instituicao": "U", "data_emissao": date(2026, 11, 3), "data_validade": date(2027, 11, 2)}, hoje)
         == "Preencha \"Nº da apólice do seguro\".", "termo de estágio: início pode ser futuro; apólice do seguro obrigatória")

at = app_logado("documentos", erro_preparar=ApiError("O envio de arquivos ainda nao foi configurado. Fale com o RH.", 500))
at.button(key="btn_doc_novo").click()
at = at.run()
at.selectbox(key="env_tipo").set_value("cpf")
at = at.run()
at.text_input(key="env_c_cpf_numero_documento").set_value("529.982.247-25")
at.button(key="btn_env_enviar").click()
at = at.run()
conferir("ainda nao foi configurado" in texto(at) and "modal_documento" in at.session_state and not any(c[0] in ("subir", "enviar") for c in chamadas),
         "armazenamento sem configuração: mensagem no modal, nada é enviado nem cadastrado")
at = app_logado("documentos", erro_subir=ApiError("Não foi possível enviar o arquivo. Confira se é PDF, JPG ou PNG de até 10 MB e tente de novo.", 400))
at.button(key="btn_doc_novo").click()
at = at.run()
at.selectbox(key="env_tipo").set_value("cpf")
at = at.run()
at.text_input(key="env_c_cpf_numero_documento").set_value("529.982.247-25")
at.button(key="btn_env_enviar").click()
at = at.run()
conferir("Não foi possível enviar o arquivo" in texto(at) and not any(c[0] == "enviar" for c in chamadas), "envio recusado pelo armazenamento: o documento não é cadastrado")
anexo["arquivo"] = None
streamlit.file_uploader = _file_uploader_original

conferir("holerite" not in TIPOS_ENVIO and "informe_rendimentos" not in TIPOS_ENVIO, "holerite e informe ficam fora (só o RH envia)")
conferir(validar_envio(None, "rg.pdf", 10) == "Escolha o tipo de documento.", "sem tipo")
conferir(validar_envio("ctps", "contrato.zip", 10) == "Envie um arquivo PDF, JPG ou PNG.", "tipo de arquivo não aceito")
conferir(validar_envio("ctps", "ctps.pdf", TAMANHO_MAXIMO + 1) == "O arquivo pode ter no máximo 10 MB.", "arquivo acima de 10 MB")
conferir(validar_envio("ctps", "ctps.pdf", 0) == "O arquivo está vazio. Escolha outro.", "arquivo vazio")
conferir(validar_envio("ctps", "CTPS frente.PNG", TAMANHO_MAXIMO, {"numero_documento": "123"}, hoje) is None and extensao("CTPS frente.PNG") == "png"
         and extensao("semponto") == "", "PNG de até 10 MB passa; extensão em minúsculas")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
