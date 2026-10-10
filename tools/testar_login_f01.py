"""Testes do fluxo de entrada (Figma F01) do frontend Streamlit, sem navegador e sem rede.

Roda o app com o AppTest do próprio Streamlit e uma API simulada (as funções de
`frontend/api_client.py` são trocadas por versões em memória, com contas fictícias).
Cobre os caminhos do F01 e os estados de UI da tela Entrar:

  Login do dia a dia ........ e-mail e senha -> código de acesso -> Início
  Primeiro acesso ........... código -> trocar senha temporária -> Onboarding -> Início
  Erros e exceções .......... senha nova inválida, senha temporária errada, código errado,
                              credencial inválida, sessão terminou (401 e prazo vencido)
  Estados ................... carregando (spinner do onboarding), vazio (sem onboarding),
                              sucesso, erro, bloqueado (muitas tentativas), permissão negada (403)

Também confere que um 401 sem token (senha errada no login) NÃO é tratado como sessão
encerrada, e que um 401 com token é.

Uso (na raiz do repositório):
    python tools/testar_login_f01.py

Sai com código 1 se algum caso falhar. Não chama a API real e não precisa de
`.streamlit/secrets.toml`.
"""

import logging
import sys
import time
from pathlib import Path
from unittest import mock

# Console do Windows em cp1252 não mostra acentos; o AppTest também enche o log de avisos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
from api_client import ApiError  # noqa: E402

# Instala a API simulada ANTES de importar as páginas: elas importam as funções pelo nome.

APP = RAIZ / "frontend" / "app.py"

# Contas fictícias. "senha_ok" é a senha atual; no primeiro acesso é a temporária.
CONTAS = {
    "ana@teste.com": {"senha": "Senha1234", "primeiro": False, "nome": "Ana Ribeiro", "perfil": "RH", "colab": 7},
    "novo@teste.com": {"senha": "Temp1234!", "primeiro": True, "nome": "Leonardo dos Santos", "perfil": "COLABORADOR", "colab": 9},
    "admin@teste.com": {"senha": "Temp1234!", "primeiro": True, "nome": "Admin Sem Vinculo", "perfil": "ADMIN", "colab": None},
}
CODIGO_OK = "123456"

chamadas: list[str] = []
estado = {"onboarding": "ok", "login": "normal"}
concluidos: set[int] = set()
# As 13 etapas fixas do backend (onboarding_POST), com o responsável de cada uma.
ITENS = [
    ("dados_pessoais", "rh", True), ("acesso", "rh", True), ("troca_senha", "colaborador", False),
    ("documentos_obrigatorios", "colaborador", False), ("aprovacoes", "rh", False), ("gestor", "rh", False),
    ("departamento", "rh", False), ("contrato", "rh", False), ("jornada", "rh", False),
    ("metas_iniciais", "gestor", False), ("acompanhamento_30_dias", "gestor", False),
    ("acompanhamento_60_dias", "gestor", False), ("acompanhamento_90_dias", "gestor", False),
]


def _login(email, password):
    chamadas.append("login")
    if estado["login"] == "bloqueado":
        raise ApiError("Muitas tentativas. Tente novamente em 15 minutos.", 429)
    conta = CONTAS.get(email)
    if not conta or conta["senha"] != password:
        raise ApiError("E-mail ou senha inválidos.", 403)
    return {"aguardando_otp": True, "email": email}


def _validar_otp(email, codigo, dispositivo=None, endereco_ip=None):
    chamadas.append("otp")
    if codigo != CODIGO_OK:
        raise ApiError("Código inválido ou expirado. Restam 4 tentativas.", 403)
    c = CONTAS[email]
    return {
        "token": "tok-" + email, "expira_em_segundos": 3600, "senha_primeiro_acesso": c["primeiro"],
        "usuario": {"id": 1, "nome": c["nome"], "email": email, "perfil": c["perfil"], "colaborador_id": c["colab"]},
    }


def _trocar_senha(token, atual, nova, confirmar):
    chamadas.append("trocar_senha")
    if atual != "Temp1234!":
        raise ApiError("A senha atual está incorreta.", 403)
    return {"sucesso": True}


def _onboarding(token, colaborador_id):
    chamadas.append("onboarding")
    if estado["onboarding"] == "sem":
        raise ApiError("Este colaborador ainda nao tem onboarding iniciado.", 404)
    if estado["onboarding"] == "erro":
        raise ApiError("Erro inesperado. Tente novamente.", 500)
    itens = [
        {"id": i + 1, "categoria": c, "descricao": c, "responsavel": r, "concluido": ok or (i + 1) in concluidos}
        for i, (c, r, ok) in enumerate(ITENS)
    ]
    feitos = sum(1 for i in itens if i["concluido"])
    return {
        "onboarding": {"data_inicio": "2026-10-01", "status": "em_andamento"},
        "itens": itens, "total_itens": len(itens), "itens_concluidos": feitos, "percentual_concluido": 0,
    }


def _concluir(token, item_id):
    chamadas.append("concluir_item")
    concluidos.add(item_id)
    return {"sucesso": True}


def _instalar_api_simulada():
    api_client.login = _login
    api_client.validar_otp = _validar_otp
    api_client.reenviar_otp = lambda email: chamadas.append("reenviar") or {"mensagem": "Enviamos um novo código."}
    api_client.trocar_senha = _trocar_senha
    api_client.logout = lambda token: chamadas.append("logout") or {}
    api_client.auth_me = lambda token: chamadas.append("auth_me") or {"autenticado": True}
    api_client.esqueci_senha = lambda email: {"mensagem": "ok"}
    api_client.onboarding = _onboarding
    api_client.concluir_item_onboarding = _concluir
    api_client.meu_perfil_colaborador = lambda token: {
        "colaborador": {"tipo_contrato": "CLT", "carga_horaria_semanal": 44},
        "departamento": {"nome": "Tecnologia", "gestor_colaborador_id": 3},
    }
    api_client.organograma = lambda token: {"colaboradores": [{"id": 3, "nome": "Ana Ribeiro"}]}
    api_client.minhas_pendencias_documento = lambda token: {"pendencias": [
        {"tipo_documento": "rg", "status": "atendida", "prazo": "2026-10-10"},
        {"tipo_documento": "ctps", "status": "pendente", "prazo": "2026-10-10"},
    ]}
    api_client.central_de_tarefas = lambda token: {}
    api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
    api_client.meus_documentos = lambda token: {"documentos": []}


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


def novo_app() -> AppTest:
    chamadas.clear()
    concluidos.clear()
    estado.update(onboarding="ok", login="normal")
    return AppTest.from_file(str(APP), default_timeout=30).run()


def html_visivel(at: AppTest) -> str:
    """Todo o HTML dos st.html da página (os alertas do protótipo são HTML)."""
    return " ".join(str(e.value) for e in at.get("html"))


def entrar(at: AppTest, email: str, senha: str) -> AppTest:
    at.text_input(key="campo_email").set_value(email)
    at.text_input(key="campo_senha").set_value(senha)
    at.button(key="btn_entrar").click()
    return at.run()


def validar_codigo(at: AppTest, codigo: str) -> AppTest:
    at.text_input(key="campo_codigo").set_value(codigo)
    at.button(key="btn_validar").click()
    return at.run()


def trocar_senha(at: AppTest, atual: str, nova: str, confirmar: str) -> AppTest:
    at.text_input(key="campo_senha_temporaria").set_value(atual)
    at.text_input(key="campo_nova_senha").set_value(nova)
    at.text_input(key="campo_confirmar_senha").set_value(confirmar)
    at.button[0].click()  # "Salvar nova senha" é o único botão de envio do formulário
    return at.run()


def passo(at: AppTest) -> str:
    return at.session_state["auth_step"] if "auth_step" in at.session_state else "?"


def caso(nome: str) -> None:
    print(f"\n{nome}")


def main() -> int:
    _instalar_api_simulada()

    caso("Login do dia a dia: e-mail e senha, código de acesso, Início")
    at = novo_app()
    conferir(not len(at.exception) and {"E-mail", "Senha"} <= {t.label for t in at.text_input}, "tela Entrar mostra E-mail e Senha")
    at = entrar(at, "ana@teste.com", "Senha1234")
    conferir(passo(at) == "otp", "senha certa leva ao código de acesso")
    conferir("Enviamos 6 dígitos para ana@teste.com" in html_visivel(at), "subtítulo do código mostra o e-mail")
    conferir("Expira em" in html_visivel(at), "legenda 'Expira em MM:SS' aparece")
    at = validar_codigo(at, CODIGO_OK)
    conferir(bool(at.session_state["token"]) and not len(at.exception), "código certo abre a área logada")
    conferir(not at.session_state["onboarding_pendente"] if "onboarding_pendente" in at.session_state else True, "sem primeiro acesso não passa pelo Onboarding")
    conferir("Olá, Ana" in html_visivel(at), "Início saúda a pessoa")

    caso("Erro: credencial inválida (a mensagem não revela se a conta existe)")
    at = novo_app()
    at = entrar(at, "ana@teste.com", "errada1234")
    conferir("E-mail ou senha inválidos." in html_visivel(at) and 'class="crh-alerta erro"' in html_visivel(at), "alerta de erro dentro do cartão")
    conferir(passo(at) == "login" and not at.session_state["token"] if "token" in at.session_state else passo(at) == "login", "continua na tela de login, sem token")

    caso("Erro: validação local barra o envio sem chamar a API")
    at = novo_app()
    at = entrar(at, "isso-nao-e-email", "Senha1234")
    conferir("login" not in chamadas and "e-mail válido" in html_visivel(at), "e-mail inválido não chega à API")
    at = entrar(at, "ana@teste.com", "curta")
    conferir("login" not in chamadas and "senha" in html_visivel(at).lower(), "senha curta não chega à API")

    caso("Bloqueado: muitas tentativas")
    at = novo_app()
    estado["login"] = "bloqueado"
    at = entrar(at, "ana@teste.com", "Senha1234")
    conferir("Muitas tentativas" in html_visivel(at), "mostra a mensagem do backend dentro do cartão")

    caso("Código de acesso: formato, erro e reenvio")
    at = novo_app()
    at = entrar(at, "ana@teste.com", "Senha1234")
    chamadas.clear()
    at = validar_codigo(at, "12ab")
    conferir("otp" not in chamadas and "6 números" in html_visivel(at), "código fora do formato não gasta tentativa")
    at = validar_codigo(at, "999999")
    conferir("Restam 4 tentativas" in html_visivel(at) and passo(at) == "otp", "código errado mostra o erro e fica no passo")
    at.button(key="btn_reenviar_otp").click()
    at = at.run()
    conferir("Aguarde" in html_visivel(at) and "reenviar" not in chamadas, "reenviar antes de 60 s pede para aguardar")
    at.session_state["otp_enviado_em"] = time.time() - 61
    at.button(key="btn_reenviar_otp").click()
    at = at.run()
    conferir("reenviar" in chamadas and "novo código" in html_visivel(at), "reenviar depois de 60 s chama a API")
    at.button(key="btn_voltar_login").click()
    at = at.run()
    conferir(passo(at) == "login" and at.text_input(key="campo_email").value == "ana@teste.com", "voltar ao login mantém o e-mail")

    caso("Primeiro acesso: código, trocar senha temporária, Onboarding, Início")
    at = novo_app()
    at = entrar(at, "novo@teste.com", "Temp1234!")
    at = validar_codigo(at, CODIGO_OK)
    conferir(passo(at) == "trocar_senha", "senha temporária leva ao Passo 3")
    conferir(not at.session_state["token"] if "token" in at.session_state else True, "sem token ativo antes da troca")
    conferir("Use de 8 a 64 caracteres" in html_visivel(at), "regra da senha visível")

    caso("Erro: senha nova inválida e senha temporária errada (Figma 224:583)")
    at = trocar_senha(at, "Temp1234!", "curta", "curta")
    conferir("trocar_senha" not in chamadas and "entre 8 e 64" in html_visivel(at), "senha nova curta mostra o que falta e não chama a API")
    at = trocar_senha(at, "Temp1234!", "NovaSenha123", "Outra123456")
    conferir("confirmação" in html_visivel(at) and "trocar_senha" not in chamadas, "confirmação diferente é recusada")
    at = trocar_senha(at, "Temp1234!", "Temp1234!", "Temp1234!")
    conferir("diferente da senha temporária" in html_visivel(at), "nova senha igual à temporária é recusada")
    at = trocar_senha(at, "ErradaTemp1", "NovaSenha123", "NovaSenha123")
    conferir("A senha temporária está incorreta." in html_visivel(at), "mensagem do backend vira 'senha temporária' (texto do Figma)")
    conferir("campo_senha_temporaria" in html_visivel(at) or any("campo_senha_temporaria" in str(e.value) for e in at.get("html")), "campo da senha temporária recebe a borda de erro")
    conferir(not at.session_state["token"] if "token" in at.session_state else True, "erro não libera a área logada")

    caso("Sucesso: troca de senha leva ao Onboarding e depois ao Início")
    at = trocar_senha(at, "Temp1234!", "NovaSenha123", "NovaSenha123")
    conferir(bool(at.session_state["token"]) and bool(at.session_state["onboarding_pendente"]), "troca libera a sessão e marca o Onboarding")
    conferir("Bem-vindo(a), Leonardo!" in html_visivel(at), "Onboarding saúda pela primeira palavra do nome")
    conferir("3 de 13" in html_visivel(at), "mostra o progresso das 13 etapas")
    conferir("concluir_item" in chamadas and "Concluída — você" in html_visivel(at), "marca 'Trocar a senha temporária' como concluída")
    conferir("São 13 etapas: 2 suas, 7 do RH e 4 do seu gestor." in html_visivel(at), "nota com as etapas por responsável (Figma 310:2477)")
    conferir(any(b.label == "Enviar documentos" for b in at.button), "com documentos pendentes, o botão é 'Enviar documentos'")
    conferir("Gestor: Ana Ribeiro · Departamento: Tecnologia · CLT · 44h/semana" in html_visivel(at), "resumo com gestor, departamento e contrato")
    at.button(key="btn_onb_continuar").click()
    at = at.run()
    conferir(not at.session_state["onboarding_pendente"] if "onboarding_pendente" in at.session_state else True, "'Enviar documentos' sai do Onboarding")
    conferir("Documentos obrigatórios da sua admissão" in html_visivel(at) and "CTPS" in html_visivel(at), "'Enviar documentos' abre a tela Documentos com o que falta")
    at.button(key="nav_Início").click()
    at = at.run()
    conferir("Olá, Leonardo" in html_visivel(at), "Início aparece depois do Onboarding")
    conferir("Seu onboarding: 3 de 13 etapas" in html_visivel(at), "Início mostra o card do onboarding em andamento")

    caso("Vazio: conta sem colaborador vinculado vai direto ao Início")
    at = novo_app()
    at = entrar(at, "admin@teste.com", "Temp1234!")
    at = validar_codigo(at, CODIGO_OK)
    at = trocar_senha(at, "Temp1234!", "NovaSenha123", "NovaSenha123")
    conferir("onboarding" not in chamadas and "Olá, Admin" in html_visivel(at), "sem colaborador não há Onboarding")

    caso("Vazio: colaborador sem checklist iniciado (404) vai ao Início")
    at = novo_app()
    estado["onboarding"] = "sem"
    at = entrar(at, "novo@teste.com", "Temp1234!")
    at = validar_codigo(at, CODIGO_OK)
    at = trocar_senha(at, "Temp1234!", "NovaSenha123", "NovaSenha123")
    conferir("Olá, Leonardo" in html_visivel(at), "404 do onboarding segue para o Início")

    caso("Erro: o onboarding não carrega e a pessoa não fica presa")
    at = novo_app()
    estado["onboarding"] = "erro"
    at = entrar(at, "novo@teste.com", "Temp1234!")
    at = validar_codigo(at, CODIGO_OK)
    at = trocar_senha(at, "Temp1234!", "NovaSenha123", "NovaSenha123")
    conferir("Não foi possível carregar suas etapas" in html_visivel(at) and 'class="crh-alerta erro"' in html_visivel(at), "mostra o erro dentro do cartão")
    at.button(key="btn_onb_inicio").click()
    at = at.run()
    conferir("Olá, Leonardo" in html_visivel(at), "'Continuar para o início' sai da tela de erro")

    caso("Sair no Passo 3 volta ao login e limpa o token pendente")
    at = novo_app()
    at = entrar(at, "novo@teste.com", "Temp1234!")
    at = validar_codigo(at, CODIGO_OK)
    at.button(key="btn_sair_troca").click()
    at = at.run()
    conferir(passo(at) == "login" and "logout" in chamadas, "Sair encerra a sessão e volta ao login")
    conferir("token_pendente" not in at.session_state, "token pendente descartado")

    caso("Sessão terminou: 401 numa chamada autenticada (Figma 224:619)")
    at = novo_app()
    at = entrar(at, "ana@teste.com", "Senha1234")
    at = validar_codigo(at, CODIGO_OK)
    import pagina_inicio

    pagina_inicio.central_de_tarefas = lambda token: (_ for _ in ()).throw(_marcar_401())
    at.run()
    conferir("Sua sessão terminou" in html_visivel(at), "volta ao login com o aviso 'Sua sessão terminou'")
    conferir(at.text_input(key="campo_email").value == "ana@teste.com", "e-mail já preenchido")
    conferir("token" not in at.session_state or not at.session_state["token"], "token descartado")
    pagina_inicio.central_de_tarefas = lambda token: {}

    caso("Sessão terminou: auth/me responde 401 logo depois do login (revogada em outro lugar)")
    at = novo_app()
    at = entrar(at, "ana@teste.com", "Senha1234")
    revogada = {"on": True}
    _original_me = api_client.auth_me

    def _me_revogado(token):
        if revogada["on"]:
            raise _marcar_401()
        return {"autenticado": True}

    api_client.auth_me = _me_revogado  # app.py é executado de novo a cada rodada e lê este nome
    at = validar_codigo(at, CODIGO_OK)
    conferir("Sua sessão terminou" in html_visivel(at) and passo(at) == "login", "auth/me 401 leva ao login com aviso")
    api_client.auth_me = _original_me

    caso("Sessão terminou: prazo do token vencido pelo relógio")
    at = novo_app()
    at = entrar(at, "ana@teste.com", "Senha1234")
    at = validar_codigo(at, CODIGO_OK)
    at.session_state["token_expira_em"] = time.time() - 5
    at.run()
    conferir("Sua sessão terminou" in html_visivel(at), "token vencido leva ao login com aviso")

    caso("Cliente de API: 401 com token é sessão terminada; 401 sem token não é")
    resposta = mock.Mock(ok=False, status_code=401)
    resposta.json.return_value = {"message": "Invalid token."}
    with mock.patch.object(api_client.requests, "request", return_value=resposta), mock.patch.object(
        api_client, "_base_url", return_value="https://exemplo.invalid/api:x"
    ):
        sessao = {}
        with mock.patch.object(api_client.st, "session_state", sessao):
            try:
                api_client._request("GET", "auth/me", "tok", "x")
            except ApiError as erro:
                conferir(erro.status_code == 401 and "sessão terminou" in erro.message.lower(), "401 com token vira ApiError em português")
            conferir(sessao.get("sessao_expirada") is True, "marca a sessão como expirada")
        sessao = {}
        with mock.patch.object(api_client.st, "session_state", sessao):
            try:
                api_client._request("POST", "auth/login", None, "x", {})
            except ApiError:
                pass
            conferir("sessao_expirada" not in sessao, "401 sem token não marca sessão expirada")

    caso("Permissão negada: 403 vira mensagem e não derruba a tela")
    at = novo_app()
    import pagina_entrar

    pagina_entrar.login = lambda e, p: (_ for _ in ()).throw(ApiError("Você não tem permissão para esta ação.", 403))
    at = entrar(at, "ana@teste.com", "Senha1234")
    conferir("não tem permissão" in html_visivel(at) and not len(at.exception), "403 aparece no cartão, sem exceção")
    pagina_entrar.login = _login

    print(f"\n{total - len(falhas)}/{total} verificações ok.")
    if falhas:
        print("Falharam:")
        for f in falhas:
            print(" -", f)
        return 1
    return 0


def _marcar_401() -> ApiError:
    import streamlit as st

    st.session_state["sessao_expirada"] = True
    return ApiError("Sua sessão terminou. Entre de novo para continuar.", 401)


if __name__ == "__main__":
    sys.exit(main())
