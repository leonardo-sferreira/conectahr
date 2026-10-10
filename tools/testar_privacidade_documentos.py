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
    api_client.logout = lambda token: chamadas.append(("logout",)) or {}
    api_client.central_de_tarefas = lambda token: {}
    api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
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

caso("Enviar documento (Figma 309:1591)")
from documentos_modelo import TIPOS_ENVIO, validar_envio  # noqa: E402

at = app_logado("documentos")
at.button(key="btn_doc_enviar_1").click()
at = at.run()
conferir(at.selectbox(key="env_tipo").value == "certificado_reservista", "'Enviar →' abre o modal já com o tipo da pendência")
at.text_input(key="env_link").set_value("http://exemplo.com/a.pdf")
at.button(key="btn_env_enviar").click()
at = at.run()
conferir("precisa começar com https://" in texto(at) and not any(c[0] == "enviar" for c in chamadas), "link sem https: mensagem no modal, sem chamar a API")
at.text_input(key="env_link").set_value("https://x8ki-letl-twmt.n7.xano.io/vault/reservista.pdf")
at.text_input(key="env_numero").set_value("123456")
at.button(key="btn_env_enviar").click()
at = at.run()
enviado = next((c[1] for c in chamadas if c[0] == "enviar"), {})
conferir(enviado.get("tipo") == "certificado_reservista" and enviado.get("colaborador_id") == 9 and enviado.get("arquivo_url", "").startswith("https://"), "envia tipo, colaborador da sessão e link")
conferir("modal_documento" not in at.session_state, "o modal fecha depois do envio")
at = app_logado("documentos", erro_enviar=ApiError("Link de arquivo nao aceito. Use um endereco https de um dominio aprovado.", 400))
at.button(key="btn_doc_novo").click()
at = at.run()
at.selectbox(key="env_tipo").set_value("cnh")
at.text_input(key="env_link").set_value("https://drive.example.com/cnh.pdf")
at.button(key="btn_env_enviar").click()
at = at.run()
conferir("Link de arquivo nao aceito" in texto(at) and "modal_documento" in at.session_state, "domínio recusado pelo backend: mensagem no modal, que continua aberto")
conferir("holerite" not in TIPOS_ENVIO and "informe_rendimentos" not in TIPOS_ENVIO, "holerite e informe ficam fora (só o RH envia)")
conferir(validar_envio(None, "https://a/b.pdf") == "Escolha o tipo de documento.", "sem tipo")
conferir(validar_envio("ctps", "") == "Informe o link do arquivo.", "sem link")
conferir("https://" in (validar_envio("ctps", "http://a/b.pdf") or ""), "link sem https é recusado antes da API")
conferir(validar_envio("ctps", "https://x8ki-letl-twmt.n7.xano.io/a.pdf", "123") is None, "link https passa para o backend conferir o domínio")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
