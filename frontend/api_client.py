"""
Cliente HTTP para a API do ConectaRH (Xano).

Centraliza a base URL e o tratamento de erro para nao duplicar isso em cada tela —
mesmo principio ja seguido no backend: reutilizar um padrao estabelecido em vez de
criar um novo para o mesmo problema (AGENTS.md).

A base URL fica em .streamlit/secrets.toml (nunca versionado - ver .gitignore).
"""

import logging
import re
import time
from urllib.parse import quote

import requests
import streamlit as st

_log = logging.getLogger(__name__)

_MENSAGEM_SEM_CONEXAO = "Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente em instantes."
_MENSAGEM_GENERICA = "Erro inesperado. Tente novamente."
_MENSAGEM_SESSAO_TERMINOU = "Sua sessão terminou. Entre de novo para continuar."
_MENSAGEM_LIMITE = "O servidor recebeu muitas consultas seguidas. Espere alguns segundos e tente de novo."

# Mensagens de validação que o próprio Xano gera em inglês (tipos e filtros de
# input), traduzidas para o usuário. As mensagens escritas nos endpoints já
# estão em português e passam direto.
_TRADUCOES = [
    (re.compile(r"^Invalid email format\.?$", re.I), lambda m: "Informe um e-mail válido, no formato nome@empresa.com."),
    (re.compile(r"^Missing param: .*", re.I), lambda m: "Preencha todos os campos obrigatórios."),
    # Token inválido (adulterado, de outro ambiente ou já invalidado): a resposta é 401,
    # tratada como sessão encerrada em _request.
    (re.compile(r"^Invalid token\.?$", re.I), lambda m: _MENSAGEM_SESSAO_TERMINOU),
    (
        re.compile(r"minimum length requirement of (\d+)", re.I),
        lambda m: f"O valor informado precisa ter pelo menos {m.group(1)} caracteres.",
    ),
    (
        re.compile(r"maximum length requirement of (\d+)", re.I),
        lambda m: f"O valor informado pode ter no máximo {m.group(1)} caracteres.",
    ),
]


def _traduzir(message: str) -> str:
    for padrao, traducao in _TRADUCOES:
        achado = padrao.search(message)
        if achado:
            return traducao(achado)
    return message


class ApiError(Exception):
    """Erro retornado pela API do Xano, com a mensagem pronta para exibir ao usuario."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# Canonical de cada api_group do Xano (xano-workspace/api/*/conecta_rh_*.xs).
# Todos os grupos vivem na mesma instancia; so o sufixo "api:<canonical>" muda.
GRUPO_AUTENTICACAO = "kFmShhlY"
GRUPO_COLABORADORES = "ySciQ2YN"
GRUPO_DEPARTAMENTOS = "wcbcMmlw"
GRUPO_DOCUMENTOS = "DzPbmWVZ"
GRUPO_PONTO = "4PXzu46t"
GRUPO_AUSENCIAS = "x-LkEdmU"
GRUPO_FERIAS = "AI-dSGch"
GRUPO_USUARIOS = "GjsM93yp"
GRUPO_CARGOS = "iy_CTE1P"
GRUPO_DESLIGAMENTOS = "yECNVuXQ"


# Pausas antes de cada nova tentativa depois de um 429 (o limite do plano gratuito é por janela de 20 s).
_PAUSAS_429_S = (3, 5)


def _base_url(canonical: str = GRUPO_AUTENTICACAO) -> str:
    # Uma base URL que não começa com http (ex.: texto de exemplo esquecido nos
    # secrets) gera uma mensagem de configuração clara, em vez do erro do requests.
    try:
        auth_base_url = st.secrets["xano"]["auth_base_url"].rstrip("/")
    except (KeyError, FileNotFoundError) as exc:
        raise ApiError(
            "Configuração ausente: crie .streamlit/secrets.toml com a base URL da API "
            "(ver frontend/api_client.py).",
            0,
        ) from exc
    if not auth_base_url.startswith(("https://", "http://")):
        raise ApiError(
            "Configuração inválida: xano.auth_base_url em .streamlit/secrets.toml precisa ser a URL "
            "completa da API, começando com https://.",
            0,
        )
    return auth_base_url.rsplit("api:", 1)[0] + f"api:{canonical}"


def _post(path: str, payload: dict, token: str | None = None, canonical: str = GRUPO_AUTENTICACAO) -> dict:
    return _request("POST", path, token, canonical, payload)


def _get(path: str, token: str, canonical: str) -> dict:
    return _request("GET", path, token, canonical)


def _request(method: str, path: str, token: str | None, canonical: str, payload: dict | None = None) -> dict:
    url = f"{_base_url(canonical)}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        resp = requests.request(method, url, json=payload, headers=headers, timeout=10)
        for pausa in _PAUSAS_429_S:
            if resp.status_code != 429:
                break
            # Plano gratuito do Xano: 10 requisições a cada 20 s. Novas tentativas depois de pausas curtas
            # evitam que uma tela com várias consultas mostre erro (ou fique sem dados) só por ter chegado ao limite.
            time.sleep(pausa)
            resp = requests.request(method, url, json=payload, headers=headers, timeout=10)
    except requests.RequestException as exc:
        # O detalhe técnico (host, SSL, retries) vai só para o log do servidor,
        # nunca para a tela (spec: erro do backend sem detalhes internos).
        _log.warning("Falha de conexão em %s %s: %s", method, path, exc)
        raise ApiError(_MENSAGEM_SEM_CONEXAO, 0) from exc

    try:
        data = resp.json()
    except ValueError:
        data = {}
    if not isinstance(data, dict):
        data = {}

    if not resp.ok:
        if resp.status_code == 401 and token:
            # 401 numa chamada autenticada: sessão encerrada, revogada ou vencida.
            # O app.py (e a tela Entrar) veem a marca e levam a pessoa ao login com
            # aviso. Um 401 sem token (credencial errada no login) não conta.
            st.session_state["sessao_expirada"] = True
            raise ApiError(_MENSAGEM_SESSAO_TERMINOU, 401)
        if resp.status_code == 429:
            raise ApiError(_MENSAGEM_LIMITE, 429)
        message = data.get("message") or data.get("error") or _MENSAGEM_GENERICA
        raise ApiError(_traduzir(str(message)), resp.status_code)

    return data


def login(email: str, password: str) -> dict:
    """POST auth/login -> {aguardando_otp, mensagem, email}."""
    return _post("auth/login", {"email": email, "password": password})


def validar_otp(email: str, codigo: str, dispositivo: str | None = None, endereco_ip: str | None = None) -> dict:
    """POST auth/otp/validar -> {token, tipo, expira_em_segundos, senha_primeiro_acesso, usuario}.

    `dispositivo` ("Chrome no Windows") e `endereco_ip` vão para a sessão criada: o backend só vê o
    servidor do Streamlit, então quem informa o navegador da pessoa é o frontend (sessao.py)."""
    corpo = {"email": email, "codigo": codigo}
    if dispositivo:
        corpo["dispositivo"] = dispositivo[:120]
    if endereco_ip:
        corpo["endereco_ip"] = endereco_ip[:64]
    return _post("auth/otp/validar", corpo)


def reenviar_otp(email: str) -> dict:
    """POST auth/otp/reenviar -> {aguardando_otp, mensagem}."""
    return _post("auth/otp/reenviar", {"email": email})


def esqueci_senha(email: str) -> dict:
    """POST auth/senha/esqueci -> {mensagem} (sempre a mesma, não revela se a conta existe)."""
    return _post("auth/senha/esqueci", {"email": email})


def redefinir_senha(email: str, codigo: str, nova_senha: str, confirmar_senha: str) -> dict:
    """POST auth/senha/redefinir -> {sucesso, mensagem}."""
    return _post(
        "auth/senha/redefinir",
        {
            "email": email,
            "codigo": codigo,
            "nova_senha": nova_senha,
            "confirmar_senha": confirmar_senha,
        },
    )


def trocar_senha(token: str, senha_atual: str, nova_senha: str, confirmar_senha: str) -> dict:
    """PATCH auth/senha -> {sucesso, mensagem, usuario_id, senha_primeiro_acesso}. Conclui o primeiro acesso."""
    return _request(
        "PATCH",
        "auth/senha",
        token,
        GRUPO_AUTENTICACAO,
        {"senha_atual": senha_atual, "nova_senha": nova_senha, "confirmar_senha": confirmar_senha},
    )


def auth_me(token: str) -> dict:
    """GET auth/me -> usuário da sessão (id, nome, perfil, colaborador_id…). 401 se a sessão terminou."""
    return _get("auth/me", token, GRUPO_AUTENTICACAO)


def logout(token: str) -> dict:
    """POST auth/logout -> encerra a sessão do usuário autenticado."""
    return _post("auth/logout", {}, token)


def central_de_tarefas(token: str) -> dict:
    """GET central_de_tarefas -> pendencias pessoais + filas de decisao por perfil."""
    return _get("central_de_tarefas", token, GRUPO_COLABORADORES)


def meu_banco_horas(token: str) -> dict:
    """GET meu_banco_horas -> {saldo_horas, lancamentos}."""
    return _get("meu_banco_horas", token, GRUPO_PONTO)


def aniversariantes(token: str) -> dict:
    """GET colaboradores/aniversariantes -> {mes, aniversariantes: [{id, nome, aniversario}]}."""
    return _get("colaboradores/aniversariantes", token, GRUPO_COLABORADORES)


def meus_comunicados(token: str) -> dict:
    """GET meus_comunicados -> {comunicados} (vigentes e visiveis ao usuario)."""
    return _get("meus_comunicados", token, GRUPO_COLABORADORES)


def minhas_notificacoes(token: str) -> dict:
    """GET minhas_notificacoes -> {total_nao_lidas, notificacoes}: as 50 mais recentes do próprio usuário, com `criada_em`."""
    return _get("minhas_notificacoes", token, GRUPO_COLABORADORES)


def marcar_notificacao_lida(token: str, notificacao_id: int) -> dict:
    """POST notificacoes/{id}/marcar_lida: só o destinatário marca."""
    return _post(f"notificacoes/{int(notificacao_id)}/marcar_lida", {}, token, GRUPO_COLABORADORES)


def marcar_todas_notificacoes_lidas(token: str) -> dict:
    """POST notificacoes/marcar_todas_lidas -> {marcadas}: as não lidas do próprio usuário."""
    return _post("notificacoes/marcar_todas_lidas", {}, token, GRUPO_COLABORADORES)


def artigos_faq(token: str) -> dict:
    """GET artigos_faq -> {artigos}: os artigos ativos da FAQ, para qualquer perfil."""
    return _get("artigos_faq", token, GRUPO_COLABORADORES)


def criar_artigo_faq(token: str, categoria: str, titulo: str, conteudo: str) -> dict:
    """POST artigos_faq (RH e Admin): publica uma pergunta e a resposta na FAQ."""
    return _post("artigos_faq", {"categoria": categoria, "titulo": titulo, "conteudo": conteudo}, token, GRUPO_COLABORADORES)


def meu_perfil_colaborador(token: str) -> dict:
    """GET meu_perfil_colaborador -> {colaborador, cargo, departamento, ...} do próprio usuário."""
    return _get("meu_perfil_colaborador", token, GRUPO_COLABORADORES)


def organograma(token: str) -> dict:
    """GET organograma -> {departamentos, cargos (com nivel_hierarquico_id), colaboradores (com superior_colaborador_id),
    niveis} (campos não sensíveis, qualquer perfil)."""
    return _get("organograma", token, GRUPO_DEPARTAMENTOS)


def niveis_hierarquicos(token: str) -> dict:
    """GET niveis_hierarquicos -> {niveis: [{id, nome, ordem, ativo}]}; o RH e o Admin veem também os inativos."""
    return _get("niveis_hierarquicos", token, GRUPO_CARGOS)


def criar_nivel_hierarquico(token: str, nome: str, ordem: int) -> dict:
    """POST niveis_hierarquicos (RH e Admin): um nível da hierarquia da empresa; ordem 1 é o topo."""
    return _post("niveis_hierarquicos", {"nome": nome, "ordem": int(ordem)}, token, GRUPO_CARGOS)


def editar_nivel_hierarquico(token: str, nivel_id: int, nome: str, ordem: int, ativo: bool) -> dict:
    """PATCH niveis_hierarquicos/{id} (RH e Admin): nome, ordem e situação."""
    return _request("PATCH", f"niveis_hierarquicos/{int(nivel_id)}", token, GRUPO_CARGOS, {"nome": nome, "ordem": int(ordem), "ativo": bool(ativo)})


def listar_cargos(token: str) -> dict:
    """GET listar_cargos (RH e Admin) -> {cargos}: todos os campos, inclusive o salário base e os inativos."""
    return _get("listar_cargos", token, GRUPO_CARGOS)


def criar_cargo(token: str, nome: str, descricao: str, salario_base: float, senioridade: str | None, departamento_id: int | None,
                nivel_id: int | None) -> dict:
    """POST cargos (RH e Admin): o nome é o título completo, com a senioridade, como vai para a carteira."""
    return _post("cargos", {"nome": nome, "descricao": descricao or "", "salario_base": float(salario_base), "ativo": True,
                            "senioridade": senioridade, "departamento_id": departamento_id, "nivel_hierarquico_id": nivel_id}, token, GRUPO_CARGOS)


def editar_cargo(token: str, cargo_id: int, nome: str, descricao: str, salario_base: float, senioridade: str | None,
                 departamento_id: int | None) -> dict:
    """PATCH cargos/{id} (RH e Admin): nome, descrição, salário, senioridade e departamento (o nível é em cargos/{id}/nivel)."""
    return _request("PATCH", f"cargos/{int(cargo_id)}", token, GRUPO_CARGOS, {"nome": nome, "descricao": descricao or "", "salario_base": float(salario_base),
                                                                               "senioridade": senioridade, "departamento_id": departamento_id})


def definir_nivel_cargo(token: str, cargo_id: int, nivel_id: int | None) -> dict:
    """PATCH cargos/{id}/nivel (RH e Admin): só o nível do cargo; None tira o nível."""
    return _request("PATCH", f"cargos/{int(cargo_id)}/nivel", token, GRUPO_CARGOS, {"nivel_hierarquico_id": nivel_id})


def onboarding(token: str, colaborador_id: int) -> dict:
    """GET colaboradores/{id}/onboarding -> {onboarding, itens, total_itens, itens_concluidos, percentual_concluido}."""
    return _get(f"colaboradores/{int(colaborador_id)}/onboarding", token, GRUPO_COLABORADORES)


def concluir_item_onboarding(token: str, item_id: int) -> dict:
    """POST onboarding_item/{id}/concluir -> {sucesso, mensagem, item, onboarding_concluido}."""
    return _post(f"onboarding_item/{int(item_id)}/concluir", {}, token, GRUPO_COLABORADORES)


def minhas_pendencias_documento(token: str) -> dict:
    """GET minhas_pendencias_documento -> {pendencias: [{tipo_documento, prazo, status, ...}]} do próprio colaborador."""
    return _get("minhas_pendencias_documento", token, GRUPO_DOCUMENTOS)



# ---------------------------------------------------------------------------
# Privacidade (tarefas 5 e 67): exportação, preferências e pedidos LGPD
# ---------------------------------------------------------------------------
def meus_dados(token: str, formato: str = "json") -> dict:
    """GET meus_dados?formato=json|csv -> dados do próprio usuário (o CSV vem no campo `csv`).

    Cada chamada grava `exportar_meus_dados` na auditoria."""
    return _get(f"meus_dados?formato={'csv' if formato == 'csv' else 'json'}", token, GRUPO_COLABORADORES)


def minhas_preferencias_privacidade(token: str) -> dict:
    """GET minhas_preferencias_privacidade -> {ocultar_aniversario, ocultar_mural, padrao, menor_de_idade}."""
    return _get("minhas_preferencias_privacidade", token, GRUPO_COLABORADORES)


def salvar_preferencias_privacidade(token: str, ocultar_aniversario: bool, ocultar_mural: bool) -> dict:
    """PATCH minhas_preferencias_privacidade (os dois campos são obrigatórios)."""
    return _request(
        "PATCH",
        "minhas_preferencias_privacidade",
        token,
        GRUPO_COLABORADORES,
        {"ocultar_aniversario": bool(ocultar_aniversario), "ocultar_mural": bool(ocultar_mural)},
    )


def minhas_solicitacoes(token: str) -> dict:
    """GET minhas_solicitacoes -> {solicitacoes, ferias, ausencias} do próprio colaborador."""
    return _get("minhas_solicitacoes", token, GRUPO_COLABORADORES)


def criar_pedido_privacidade(token: str, subtipo: str, descricao: str) -> dict:
    """POST solicitacoes com tipo privacidade_lgpd: o backend dá prazo de resposta de 15 dias."""
    return _post(
        "solicitacoes",
        {"tipo": "privacidade_lgpd", "subtipo_lgpd": subtipo, "descricao": descricao},
        token,
        GRUPO_COLABORADORES,
    )


# ---------------------------------------------------------------------------
# Documentos (tarefas 26 a 28). Não existe função de exclusão: o backend recusa o DELETE e o
# documento só é arquivado pelo RH (documentos/{id}/arquivar).
# ---------------------------------------------------------------------------
def meus_documentos(token: str) -> dict:
    """GET meus_documentos -> {quantidade, documentos} do próprio colaborador, sem o link do arquivo."""
    return _get("meus_documentos", token, GRUPO_DOCUMENTOS)


def enviar_documento(token: str, dados: dict) -> dict:
    """POST documentos -> {documento}. `dados`: colaborador_id, tipo, nome_documento, arquivo_url e,
    opcionais, numero_documento e data_emissao (aaaa-mm-dd). Encerra a pendência aberta do mesmo tipo."""
    return _post("documentos", {k: v for k, v in dados.items() if v not in (None, "")}, token, GRUPO_DOCUMENTOS)


def preparar_envio_arquivo(token: str, colaborador_id: int, extensao: str) -> dict:
    """POST documentos/envio_arquivo -> {upload_url, arquivo_url} (change anexo-de-arquivos). O Xano gera um endereço
    de envio de uso único no armazenamento privado; a chave do armazenamento não passa pelo Streamlit."""
    return _post("documentos/envio_arquivo", {"colaborador_id": colaborador_id, "extensao": extensao}, token, GRUPO_DOCUMENTOS)


def subir_arquivo(upload_url: str, conteudo: bytes, tipo_conteudo: str) -> None:
    """PUT do arquivo no endereço de envio devolvido por `preparar_envio_arquivo`. Não leva o token do ConectaRH."""
    try:
        resp = requests.put(upload_url, data=conteudo, headers={"Content-Type": tipo_conteudo}, timeout=60)
    except requests.RequestException as exc:
        _log.warning("Falha de conexão no envio do arquivo: %s", exc)
        raise ApiError(_MENSAGEM_SEM_CONEXAO, 0) from exc
    if not resp.ok:
        _log.warning("Envio do arquivo recusado pelo armazenamento: HTTP %s", resp.status_code)
        raise ApiError("Não foi possível enviar o arquivo. Confira se é PDF, JPG ou PNG de até 10 MB e tente de novo.", resp.status_code)


def abrir_arquivo_documento(token: str, documento_id: int) -> dict:
    """GET documentos/{id}/arquivo -> {arquivo_url, expira_em_segundos}. Só o dono, o RH e o Admin; cada
    abertura grava `acessar_arquivo_documento` na auditoria."""
    return _get(f"documentos/{int(documento_id)}/arquivo", token, GRUPO_DOCUMENTOS)


# ---------------------------------------------------------------------------
# Conferência de documentos pelo RH (tarefa 27). Só RH e Admin: o backend recusa os demais perfis.
# Nenhuma exclusão: o documento sai das listas por arquivamento.
# ---------------------------------------------------------------------------
def documentos_rh(token: str) -> dict:
    """GET documentos -> {quantidade, documentos} de todos os colaboradores, sem o link do arquivo."""
    return _get("documentos", token, GRUPO_DOCUMENTOS)


def pendencias_documento(token: str) -> dict:
    """GET pendencias_documento -> {pendencias} de todos os colaboradores."""
    return _get("pendencias_documento", token, GRUPO_DOCUMENTOS)


def pedir_documento(token: str, colaborador_id: int, tipo_documento: str, prazo: str, observacao: str | None) -> dict:
    """POST pendencias_documento: o colaborador recebe a pendência por e-mail e na tela Documentos."""
    corpo = {"colaborador_id": int(colaborador_id), "tipo_documento": tipo_documento, "prazo": prazo}
    if observacao:
        corpo["observacao"] = observacao
    return _post("pendencias_documento", corpo, token, GRUPO_DOCUMENTOS)


def documentos_obrigatorios(token: str) -> dict:
    """GET documentos_obrigatorios -> {regras} ativas da matriz de documentos obrigatórios."""
    return _get("documentos_obrigatorios", token, GRUPO_DOCUMENTOS)


def criar_regra_documento(token: str, regra: dict) -> dict:
    """POST documentos_obrigatorios -> {regra}. Campos vazios não são enviados."""
    return _post("documentos_obrigatorios", {k: v for k, v in regra.items() if v not in (None, "")}, token, GRUPO_DOCUMENTOS)


def _decidir(acao: str, token: str, documento_id: int, observacao: str | None) -> dict:
    corpo = {"observacao": observacao} if observacao else {}
    return _post(f"documentos/{int(documento_id)}/{acao}", corpo, token, GRUPO_DOCUMENTOS)


def aprovar_documento(token: str, documento_id: int, observacao: str | None = None) -> dict:
    """POST documentos/{id}/aprovar. Recusa o próprio documento e arquivo bloqueado."""
    return _decidir("aprovar", token, documento_id, observacao)


def rejeitar_documento(token: str, documento_id: int, motivo: str) -> dict:
    """POST documentos/{id}/rejeitar. O motivo (5 a 1000 caracteres) é obrigatório e o colaborador vê."""
    return _decidir("rejeitar", token, documento_id, motivo)


def arquivar_documento(token: str, documento_id: int, observacao: str | None = None) -> dict:
    """POST documentos/{id}/arquivar. Só recusado, vencido ou substituído; o documento não é apagado."""
    return _decidir("arquivar", token, documento_id, observacao)


def processar_vencimentos(token: str) -> dict:
    """POST documentos/processar_vencimentos -> {total_vencidos, total_alertas}. Idempotente no mesmo dia."""
    return _post("documentos/processar_vencimentos", {}, token, GRUPO_DOCUMENTOS)


# ---------------------------------------------------------------------------
# Perfil (tarefas 14 a 16). Nada aqui recebe id: tudo é do próprio usuário do token.
# ---------------------------------------------------------------------------
def salvar_dados_bancarios(token: str, banco: str, agencia: str, conta: str, digito: str, tipo_conta: str) -> dict:
    """PATCH meus_dados_bancarios: só o próprio colaborador edita; a alteração vai para a auditoria com a
    conta mascarada. `tipo_conta`: "corrente" ou "poupanca"."""
    return _request(
        "PATCH",
        "meus_dados_bancarios",
        token,
        GRUPO_COLABORADORES,
        {"banco": banco, "agencia": agencia, "conta": conta, "digito": digito, "tipo_conta": tipo_conta},
    )


def salvar_contato_endereco(token: str, dados: dict) -> dict:
    """PATCH meu_perfil_colaborador: telefone, e-mail pessoal e endereço do próprio colaborador, sem pedido ao
    RH (tarefa 72). `dados`: email_pessoal, telefone, cep, logradouro, numero, complemento, bairro, cidade e
    estado. A alteração vai para a auditoria mascarada."""
    return _request("PATCH", "meu_perfil_colaborador", token, GRUPO_COLABORADORES, dados)


def solicitar_alteracao_cadastral(token: str, descricao: str) -> dict:
    """POST solicitacoes com tipo alteracao_cadastral: o RH confere e aplica no cadastro."""
    return _post("solicitacoes", {"tipo": "alteracao_cadastral", "descricao": descricao}, token, GRUPO_COLABORADORES)


# ---------------------------------------------------------------------------
# Ponto e ausências (tarefas 19 a 21). Nada aqui recebe id de colaborador: o backend usa o token.
# ---------------------------------------------------------------------------
def meu_ponto(token: str) -> dict:
    """GET meu_ponto -> {registros, marcacoes, tratamentos} do próprio colaborador: o resumo de cada dia, as marcações
    da ARP (com NSR) e os tratamentos."""
    return _get("meu_ponto", token, GRUPO_PONTO)


def marcar_ponto(token: str) -> dict:
    """POST ponto/marcar: grava a marcação na ARP do REP-P, sem ordem nem limite (art. 74). Responde `marcacao` (NSR,
    data e hora, hash) e `comprovante` (empregador e trabalhador) para o PDF do comprovante."""
    return _post("ponto/marcar", {}, token, GRUPO_PONTO)


def comprovantes_ponto(token: str) -> dict:
    """GET ponto/comprovantes -> {marcacoes, empregador, trabalhador, jornada}: as marcações dos últimos 7 dias do
    próprio colaborador com os dados do comprovante (arts. 79 e 80) e do cabeçalho do espelho (art. 84)."""
    return _get("ponto/comprovantes", token, GRUPO_PONTO)


def minhas_correcoes_ponto(token: str) -> dict:
    """GET minhas_correcoes_ponto -> {correcoes} do próprio colaborador."""
    return _get("minhas_correcoes_ponto", token, GRUPO_PONTO)


def pedir_correcao_ponto(token: str, data: str, tipo: str, justificativa: str, marcacao_id: int | None = None,
                         data_hora_ms: int | None = None, tratamento_id: int | None = None) -> dict:
    """POST ponto/correcao: pede a inclusão (`data_hora_ms`) ou a desconsideração (`marcacao_id`) de uma marcação de um
    dia passado. A marcação original nunca muda; aprovado, o pedido vira um tratamento. Quem decide é a hierarquia."""
    corpo = {"data": data, "tipo": tipo, "justificativa": justificativa}
    if marcacao_id:
        corpo["marcacao_id"] = int(marcacao_id)
    if tratamento_id:  # marcação incluída por correção (12/10/2026)
        corpo["tratamento_id"] = int(tratamento_id)
    if data_hora_ms is not None:
        corpo["data_hora"] = int(data_hora_ms)
    return _post("ponto/correcao", corpo, token, GRUPO_PONTO)


def minhas_ausencias(token: str) -> dict:
    """GET minhas_ausencias -> {quantidade, ausencias} do próprio colaborador."""
    return _get("minhas_ausencias", token, GRUPO_AUSENCIAS)


def registrar_ausencia(token: str, tipo: str, data_inicio: str, data_fim: str, motivo_tipo: str, observacao: str | None) -> dict:
    """POST ausencias -> {ausencia}. `tipo`: Falta, Atestado, Afastamento, Licenca ou Outro; `motivo_tipo`:
    consulta, doenca, acompanhamento_familiar ou outro. Sem comprovante: o sistema não recebe arquivo."""
    corpo = {"tipo": tipo, "data_inicio": data_inicio, "data_fim": data_fim, "motivo_tipo": motivo_tipo}
    if observacao:
        corpo["observacao"] = observacao
    return _post("ausencias", corpo, token, GRUPO_AUSENCIAS)


# ---------------------------------------------------------------------------
# Férias (tarefas 22 a 25). Tudo do próprio colaborador, pelo token.
# ---------------------------------------------------------------------------
def minhas_ferias(token: str) -> dict:
    """GET minhas_ferias -> {quantidade, ferias} do próprio colaborador, do início mais recente ao mais antigo."""
    return _get("minhas_ferias", token, GRUPO_FERIAS)


def minha_situacao_ferias(token: str) -> dict:
    """GET minha_situacao_ferias -> os números que o pedido de férias confere: limite de dias por pedido,
    períodos usados e máximo, mínimo do próximo período, antecedência mínima e se há pedido pendente.
    Não é saldo: o backend ainda não desconta os dias já tirados (tarefa 74)."""
    return _get("minha_situacao_ferias", token, GRUPO_FERIAS)


def solicitar_ferias(token: str, data_inicio: str, data_fim: str, quantidade_dias: int, observacao: str | None, dias_abono: int = 0) -> dict:
    """POST ferias/solicitacoes -> {solicitacao, saldo_restante}. `dias_abono`: dias vendidos junto (até 10 na CLT, uma vez
    por período aquisitivo). Quem decide é o gestor ou o RH."""
    corpo = {"data_inicio": data_inicio, "data_fim": data_fim, "quantidade_dias": int(quantidade_dias), "dias_abono": int(dias_abono or 0)}
    if observacao:
        corpo["observacao"] = observacao
    return _post("ferias/solicitacoes", corpo, token, GRUPO_FERIAS)


def ferias_equipe(token: str, desde: str, ate: str) -> dict:
    """GET ferias_equipe -> {ve_todos, pessoas, ferias}: férias aprovadas, concluídas e em análise que tocam o período
    (aaaa-mm-dd), com o nome de cada pessoa. RH e Admin veem todos; os demais, a si mesmos e quem está abaixo deles."""
    return _get(f"ferias_equipe?desde={desde}&ate={ate}", token, GRUPO_FERIAS)


def cancelar_ferias(token: str, ferias_id: int) -> dict:
    """POST ferias/{id}/cancelar: só a própria pessoa e só pedido pendente (o backend confere)."""
    return _post(f"ferias/{int(ferias_id)}/cancelar", {}, token, GRUPO_FERIAS)


# ---------------------------------------------------------------------------
# Decisões do gestor, do RH e do Admin (Central de Pendências e Ausências; tarefas 11 a 13, 20, 21 e 24).
# O backend confere o escopo (Gestor só a própria equipe, RH e Admin todos) e bloqueia quem tenta
# decidir o próprio pedido; a tela só deixa de oferecer o que ele recusaria.
# ---------------------------------------------------------------------------
def correcoes_ponto(token: str) -> dict:
    """GET correcoes_ponto -> {correcoes} pendentes no escopo de quem pede (Gestor, RH ou Admin)."""
    return _get("correcoes_ponto", token, GRUPO_PONTO)


def aprovar_correcao_ponto(token: str, correcao_id: int) -> dict:
    """POST correcoes_ponto/{id}/aprovar: troca o horário no registro do dia e recalcula o banco de horas."""
    return _post(f"correcoes_ponto/{int(correcao_id)}/aprovar", {}, token, GRUPO_PONTO)


def rejeitar_correcao_ponto(token: str, correcao_id: int, motivo: str) -> dict:
    """POST correcoes_ponto/{id}/rejeitar com `motivo_decisao` (5 a 1000 caracteres)."""
    return _post(f"correcoes_ponto/{int(correcao_id)}/rejeitar", {"motivo_decisao": motivo}, token, GRUPO_PONTO)


def verificar_conflito_ferias(token: str, ferias_id: int) -> dict:
    """GET ferias/{id}/verificar_conflito -> antecedência, período aquisitivo, sobreposições e colegas de
    férias no período. Só informa: não bloqueia a decisão."""
    return _get(f"ferias/{int(ferias_id)}/verificar_conflito", token, GRUPO_FERIAS)


def aprovar_ferias(token: str, ferias_id: int) -> dict:
    """POST ferias/{id}/aprovar."""
    return _post(f"ferias/{int(ferias_id)}/aprovar", {}, token, GRUPO_FERIAS)


def rejeitar_ferias(token: str, ferias_id: int) -> dict:
    """POST ferias/{id}/rejeitar."""
    return _post(f"ferias/{int(ferias_id)}/rejeitar", {}, token, GRUPO_FERIAS)


def ausencias_rh(token: str, status: str) -> dict:
    """GET ausencias?status=... -> {ausencias} (só RH e Admin). `status`: Pendente, Aprovada, Registrado ou Rejeitada."""
    return _get(f"ausencias?status={status}", token, GRUPO_AUSENCIAS)


def _decidir_ausencia(acao: str, token: str, ausencia_id: int, observacao: str | None) -> dict:
    corpo = {"observacao": observacao} if observacao else {}
    return _post(f"ausencias/{int(ausencia_id)}/{acao}", corpo, token, GRUPO_AUSENCIAS)


def aprovar_ausencia(token: str, ausencia_id: int, observacao: str | None = None) -> dict:
    """POST ausencias/{id}/aprovar (só RH e Admin)."""
    return _decidir_ausencia("aprovar", token, ausencia_id, observacao)


def rejeitar_ausencia(token: str, ausencia_id: int, justificativa: str) -> dict:
    """POST ausencias/{id}/rejeitar com a justificativa obrigatória (5 a 1000 caracteres, sem CID)."""
    return _decidir_ausencia("rejeitar", token, ausencia_id, justificativa)


def registrar_ausencia_aprovada(token: str, ausencia_id: int, observacao: str | None = None) -> dict:
    """POST ausencias/{id}/registrar: só ausência aprovada; o dia fica justificado no espelho de ponto."""
    return _decidir_ausencia("registrar", token, ausencia_id, observacao)


def abrir_comprovante_ausencia(token: str, ausencia_id: int) -> dict:
    """GET ausencias/{id}/comprovante -> {comprovante_url} temporário. RH, Admin ou o próprio; o Gestor não."""
    return _get(f"ausencias/{int(ausencia_id)}/comprovante", token, GRUPO_AUSENCIAS)


# ---------------------------------------------------------------------------
# Colaboradores (RH) e Usuários e perfis (Admin) — tarefas 50 e 53. O backend decide quem pode:
# admitir é só do RH; criar conta, RH ou Admin; trocar perfil, só Admin; vincular, Admin (qualquer
# conta) ou RH (contas de colaborador), nunca a própria.
# ---------------------------------------------------------------------------
def colaboradores(token: str) -> dict:
    """GET colaboradores -> {colaboradores} (RH e Admin), com `user_id` quando a ficha tem conta."""
    return _get("colaboradores", token, GRUPO_COLABORADORES)


def admitir_colaborador(token: str, dados: dict) -> dict:
    """POST colaboradores: pré-cadastro (só RH). Não cria conta de acesso; o próximo passo é `criar_usuario`."""
    return _post("colaboradores", dados, token, GRUPO_COLABORADORES)


def usuarios(token: str) -> dict:
    """GET usuarios -> {usuarios} com perfil, situação, último acesso e se ainda usa a senha temporária."""
    return _get("usuarios", token, GRUPO_USUARIOS)


def criar_usuario(token: str, colaborador_id: int, email: str, senha_temporaria: str) -> dict:
    """POST usuarios: cria a conta de um colaborador; o backend manda a senha temporária por e-mail e
    responde `email_enviado`. A conta nasce com o perfil Colaborador."""
    return _post("usuarios", {"colaborador_id": int(colaborador_id), "email": email, "senha_temporaria": senha_temporaria}, token, GRUPO_USUARIOS)


def trocar_perfil(token: str, usuario_id: int, perfil: str) -> dict:
    """PATCH usuarios/{id}/perfil (só Admin; ninguém troca o próprio). `perfil`: COLABORADOR, GESTOR, RH ou ADMIN."""
    return _request("PATCH", f"usuarios/{int(usuario_id)}/perfil", token, GRUPO_USUARIOS, {"perfil": perfil})


def solicitacoes_acesso(token: str) -> dict:
    """GET solicitacoes_acesso -> {solicitacoes}: pedidos de alteração de acesso (RH e Admin), mais recentes primeiro,
    com o nome da conta, quem pediu, o perfil pedido, a justificativa e a decisão (change pedido-de-acesso)."""
    return _get("solicitacoes_acesso", token, GRUPO_USUARIOS)


def pedir_acesso(token: str, usuario_id: int, perfil: str, justificativa: str) -> dict:
    """POST solicitacoes_acesso: o RH pede ao Admin outro perfil para uma conta (um pedido pendente por conta)."""
    return _post("solicitacoes_acesso", {"usuario_id": int(usuario_id), "perfil": perfil, "justificativa": justificativa}, token, GRUPO_USUARIOS)


def aprovar_pedido_acesso(token: str, pedido_id: int) -> dict:
    """POST solicitacoes_acesso/{id}/aprovar (só Admin): troca o perfil da conta na hora."""
    return _post(f"solicitacoes_acesso/{int(pedido_id)}/aprovar", {}, token, GRUPO_USUARIOS)


def recusar_pedido_acesso(token: str, pedido_id: int, motivo: str) -> dict:
    """POST solicitacoes_acesso/{id}/recusar (só Admin), com o motivo (5 a 1000 caracteres) que vai para o RH."""
    return _post(f"solicitacoes_acesso/{int(pedido_id)}/recusar", {"motivo": motivo}, token, GRUPO_USUARIOS)


def alterar_status_usuario(token: str, usuario_id: int, ativo: bool) -> dict:
    """PATCH usuarios/{id}/status: ativa ou desativa sem apagar o histórico."""
    return _request("PATCH", f"usuarios/{int(usuario_id)}/status", token, GRUPO_USUARIOS, {"ativo": bool(ativo)})


def vincular_colaborador(token: str, usuario_id: int, colaborador_id: int) -> dict:
    """POST usuarios/{id}/vincular_colaborador: liga uma conta sem ficha a uma ficha sem conta."""
    return _post(f"usuarios/{int(usuario_id)}/vincular_colaborador", {"colaborador_id": int(colaborador_id)}, token, GRUPO_USUARIOS)


# ---------------------------------------------------------------------------
# Solicitações ao RH (tarefa 47). RH e Admin listam e decidem; aplicar uma alteração cadastral
# no cadastro é `colaboradores/{id}` PATCH, que só o RH pode.
# ---------------------------------------------------------------------------
def solicitacoes_rh(token: str) -> dict:
    """GET solicitacoes -> {solicitacoes} de todos os colaboradores (RH e Admin), mais recentes primeiro."""
    return _get("solicitacoes", token, GRUPO_COLABORADORES)


def atender_solicitacao(token: str, solicitacao_id: int, justificativa: str | None = None, parcial: bool = False) -> dict:
    """POST solicitacoes/{id}/atender. Para alteração cadastral, não muda o cadastro sozinho. No pedido LGPD, a
    justificativa é a resposta ao titular (obrigatória) e `parcial` registra "atendido em parte" (change pedidos-lgpd)."""
    corpo = {"justificativa_decisao": justificativa} if justificativa else {}
    if parcial:
        corpo["resultado"] = "parcial"
    return _post(f"solicitacoes/{int(solicitacao_id)}/atender", corpo, token, GRUPO_COLABORADORES)


def indeferir_solicitacao(token: str, solicitacao_id: int, justificativa: str) -> dict:
    """POST solicitacoes/{id}/indeferir com a justificativa obrigatória (5 a 1000 caracteres)."""
    return _post(f"solicitacoes/{int(solicitacao_id)}/indeferir", {"justificativa_decisao": justificativa}, token, GRUPO_COLABORADORES)


def atualizar_dados_pessoais(token: str, colaborador_id: int, dados: dict) -> dict:
    """PATCH colaboradores/{id}: dados pessoais completos (nome, CPF, e-mail, nascimento, telefone e endereço). Só o RH."""
    return _request("PATCH", f"colaboradores/{int(colaborador_id)}", token, GRUPO_COLABORADORES, dados)


# ---------------------------------------------------------------------------
# Espelho mensal do ponto (tarefa 78).
# ---------------------------------------------------------------------------
def calendario(token: str) -> dict:
    """GET calendario -> {feriados, ferias, ausencias}. Os feriados valem para todos."""
    return _get("calendario", token, GRUPO_COLABORADORES)


def importar_feriados(token: str, ano: int) -> dict:
    """POST feriados/importar (RH e Admin) -> {ano, importados, ja_existiam}: os feriados nacionais do ano, da BrasilAPI.
    Só grava as datas que ainda não têm feriado nacional."""
    return _post("feriados/importar", {"ano": int(ano)}, token, GRUPO_COLABORADORES)




# ---------------------------------------------------------------------------
# Folha de ponto da equipe e do RH, e hierarquia (tarefa 81). O escopo é do backend: RH e Admin veem todos;
# os demais, a si mesmos, quem os tem como superior direto e, de quem não tem superior, o departamento que gerenciam.
# ---------------------------------------------------------------------------
def folha_pessoas(token: str) -> dict:
    """GET folha_ponto/pessoas -> {ve_todos, pessoas} com a data do primeiro ponto de cada uma."""
    return _get("folha_ponto/pessoas", token, GRUPO_PONTO)


def folha_mes(token: str, ano: int, mes: int, colaborador_id: int | None = None) -> dict:
    """GET folha_ponto/mes -> {registros, marcacoes, tratamentos, ausencias, ferias, correcoes} do mês (correções só
    com colaborador_id). As marcações vêm sem CPF nem hash."""
    caminho = f"folha_ponto/mes?ano={int(ano)}&mes={int(mes)}" + (f"&colaborador_id={int(colaborador_id)}" if colaborador_id else "")
    return _get(caminho, token, GRUPO_PONTO)


def tratar_ponto(token: str, colaborador_id: int, data: str, tipo: str, motivo: str, marcacao_id: int | None = None,
                 data_hora_ms: int | None = None, tratamento_id: int | None = None) -> dict:
    """POST folha_ponto/tratar: ajuste direto, auditado, no ponto de outra pessoa (nunca no próprio): inclui
    (`data_hora_ms`) ou desconsidera (`marcacao_id`) uma marcação, com motivo. Vale na hora, como tratamento."""
    corpo = {"colaborador_id": int(colaborador_id), "data": data, "tipo": tipo, "motivo": motivo}
    if marcacao_id:
        corpo["marcacao_id"] = int(marcacao_id)
    if tratamento_id:  # marcação incluída por correção (12/10/2026)
        corpo["tratamento_id"] = int(tratamento_id)
    if data_hora_ms is not None:
        corpo["data_hora"] = int(data_hora_ms)
    return _post("folha_ponto/tratar", corpo, token, GRUPO_PONTO)


def definir_superior(token: str, colaborador_id: int, superior_colaborador_id: int | None) -> dict:
    """PATCH colaboradores/{id}/superior (RH e Admin). None limpa o superior direto."""
    return _request("PATCH", f"colaboradores/{int(colaborador_id)}/superior", token, GRUPO_COLABORADORES, {"superior_colaborador_id": superior_colaborador_id})


# ---------------------------------------------------------------------------
# Benefícios (tarefa 82). O RH e o Admin cuidam do catálogo e dos vínculos; o colaborador vê os seus.
# ---------------------------------------------------------------------------
def meus_beneficios(token: str) -> dict:
    """GET meus_beneficios -> {beneficios} do próprio colaborador (ativos e encerrados)."""
    return _get("meus_beneficios", token, GRUPO_COLABORADORES)


def beneficios_catalogo(token: str) -> dict:
    """GET beneficios -> {beneficios} do catálogo (RH e Admin)."""
    return _get("beneficios", token, GRUPO_COLABORADORES)


def cadastrar_beneficio(token: str, nome: str, tipo: str, operadora: str | None, descricao: str | None) -> dict:
    """POST beneficios: novo benefício no catálogo (RH e Admin; nome não pode repetir)."""
    return _post("beneficios", {"nome": nome, "tipo": tipo, "operadora": operadora, "descricao": descricao}, token, GRUPO_COLABORADORES)


def status_beneficio(token: str, beneficio_id: int, ativo: bool) -> dict:
    """PATCH beneficios/{id}/status: desativado não aceita novos vínculos."""
    return _request("PATCH", f"beneficios/{int(beneficio_id)}/status", token, GRUPO_COLABORADORES, {"ativo": bool(ativo)})


def editar_beneficio(token: str, beneficio_id: int, nome: str, tipo: str, operadora: str | None, descricao: str | None, links: list[dict]) -> dict:
    """PATCH beneficios/{id} (RH e Admin): dados e links da apresentação; avisa quem tem o benefício."""
    corpo = {"nome": nome, "tipo": tipo, "operadora": operadora, "descricao": descricao, "links": links}
    return _request("PATCH", f"beneficios/{int(beneficio_id)}", token, GRUPO_COLABORADORES, corpo)


def preparar_material_beneficio(token: str, beneficio_id: int, extensao: str) -> dict:
    """POST beneficios/{id}/arquivos/envio -> {upload_url, caminho}: endereço de envio de uso único (RH e Admin)."""
    return _post(f"beneficios/{int(beneficio_id)}/arquivos/envio", {"extensao": extensao}, token, GRUPO_COLABORADORES)


def registrar_material_beneficio(token: str, beneficio_id: int, nome: str, caminho: str) -> dict:
    """POST beneficios/{id}/arquivos: registra o material já enviado (RH e Admin)."""
    return _post(f"beneficios/{int(beneficio_id)}/arquivos", {"nome": nome, "caminho": caminho}, token, GRUPO_COLABORADORES)


def remover_material_beneficio(token: str, material_id: int) -> dict:
    """POST beneficio_arquivos/{id}/remover: desativa o material, sem apagar (RH e Admin)."""
    return _post(f"beneficio_arquivos/{int(material_id)}/remover", {}, token, GRUPO_COLABORADORES)


def abrir_material_beneficio(token: str, material_id: int) -> dict:
    """GET beneficio_arquivos/{id}/abrir -> {arquivo_url} que vale 5 minutos; auditado. Quem tem o benefício, RH e Admin."""
    return _get(f"beneficio_arquivos/{int(material_id)}/abrir", token, GRUPO_COLABORADORES)


def beneficios_da_pessoa(token: str, colaborador_id: int) -> dict:
    """GET colaboradores/{id}/beneficios -> {beneficios} (RH e Admin)."""
    return _get(f"colaboradores/{int(colaborador_id)}/beneficios", token, GRUPO_COLABORADORES)


def vincular_beneficio(token: str, colaborador_id: int, dados: dict) -> dict:
    """POST colaboradores/{id}/beneficios: beneficio_id, valor_empresa, desconto_colaborador, data_inicio, data_fim e observação."""
    return _post(f"colaboradores/{int(colaborador_id)}/beneficios", dados, token, GRUPO_COLABORADORES)


def encerrar_beneficio(token: str, vinculo_id: int, data_fim: str, observacao: str | None = None) -> dict:
    """POST colaborador_beneficios/{id}/encerrar: preenche a data de fim e desativa, sem apagar."""
    return _post(f"colaborador_beneficios/{int(vinculo_id)}/encerrar", {"data_fim": data_fim, "observacao": observacao}, token, GRUPO_COLABORADORES)


# ---------------------------------------------------------------------------
# Prazo para pedir correção de ponto (tarefa 83), definido pelo RH. None = sem limite.
# ---------------------------------------------------------------------------
def prazo_correcao(token: str) -> dict:
    """GET ponto/prazo_correcao -> {prazo_dias} (qualquer perfil)."""
    return _get("ponto/prazo_correcao", token, GRUPO_PONTO)


def definir_prazo_correcao(token: str, prazo_dias: int | None) -> dict:
    """PATCH ponto/prazo_correcao (RH e Admin). None tira o limite. O ajuste do gestor e do RH não tem prazo."""
    return _request("PATCH", "ponto/prazo_correcao", token, GRUPO_PONTO, {"prazo_dias": prazo_dias})


# ---------------------------------------------------------------------------
# Trajetória (change trajetoria-do-colaborador): avaliação, metas, PDI e reconhecimentos da própria pessoa.
# ---------------------------------------------------------------------------
def minha_trajetoria(token: str) -> dict:
    """GET minha_trajetoria -> plano de carreira, 360 do ciclo, a_preencher, recebidas, metas, pdi e reconhecimentos."""
    return _get("minha_trajetoria", token, GRUPO_COLABORADORES)


def competencias_avaliacao(token: str, avaliacao_id: int) -> dict:
    """GET avaliacoes/{id}/competencias -> {competencias, respostas, avaliado_nome} (só o avaliador designado)."""
    return _get(f"avaliacoes/{int(avaliacao_id)}/competencias", token, GRUPO_COLABORADORES)


def responder_avaliacao(token: str, avaliacao_id: int, competencia_id: int, nota: int, comentario: str | None) -> dict:
    """POST avaliacoes/{id}/respostas: nota de 1 a 5 de uma competência; chamar de novo atualiza a resposta."""
    return _post(f"avaliacoes/{int(avaliacao_id)}/respostas", {"competencia_avaliacao_id": int(competencia_id), "nota": int(nota), "comentario": comentario or None},
                 token, GRUPO_COLABORADORES)


def enviar_avaliacao(token: str, avaliacao_id: int, comentario: str | None) -> dict:
    """POST avaliacoes/{id}/enviar: fecha a avaliação (definitivo) com a nota geral pela média."""
    return _post(f"avaliacoes/{int(avaliacao_id)}/enviar", {"comentario": comentario or None}, token, GRUPO_COLABORADORES)


def contestar_avaliacao(token: str, avaliacao_id: int, motivo: str) -> dict:
    """POST avaliacoes/{id}/contestar: só o avaliado, só avaliação enviada; o RH revisa."""
    return _post(f"avaliacoes/{int(avaliacao_id)}/contestar", {"motivo": motivo}, token, GRUPO_COLABORADORES)


def checkin_meta(token: str, meta_id: int, progresso: float, comentario: str | None, dificuldades: str | None, evidencia: str | None) -> dict:
    """POST metas/{id}/checkin: progresso de 0 a 100, com comentário, dificuldades e evidência opcionais."""
    return _post(f"metas/{int(meta_id)}/checkin", {"progresso_percentual": float(progresso), "comentario_checkin": comentario or None,
                                                    "dificuldades": dificuldades or None, "evidencia": evidencia or None}, token, GRUPO_COLABORADORES)


def progresso_pdi(token: str, pdi_id: int, progresso: float, evidencia: str | None) -> dict:
    """POST pdi/{id}/progresso: progresso de 0 a 100 e evidência opcional."""
    return _post(f"pdi/{int(pdi_id)}/progresso", {"progresso_percentual": float(progresso), "evidencia": evidencia or None}, token, GRUPO_COLABORADORES)


# ---------------------------------------------------------------------------
# Ciclo anual de metas (change ciclo-de-metas): a pessoa preenche; o RH configura; o superior dá feedback.
# ---------------------------------------------------------------------------
def meu_ciclo_metas(token: str) -> dict:
    """GET meu_ciclo_metas -> {hoje, perguntas_ativas, ciclos: [{datas, etapa_aberta, formulario_id, etapaN_enviada_em, respostas, feedbacks}]}."""
    return _get("meu_ciclo_metas", token, GRUPO_COLABORADORES)


def responder_meta(token: str, ciclo_id: int, pergunta_id: int, texto: str | None, autoavaliacao: str | None = None) -> dict:
    """POST meu_ciclo_metas/{ciclo_id}/respostas: uma pergunta da etapa aberta (meta, ou alcançado e autoavaliação)."""
    return _post(f"meu_ciclo_metas/{int(ciclo_id)}/respostas", {"pergunta_meta_id": int(pergunta_id), "texto": texto or None, "autoavaliacao": autoavaliacao or None},
                 token, GRUPO_COLABORADORES)


def enviar_etapa_meta(token: str, ciclo_id: int) -> dict:
    """POST meu_ciclo_metas/{ciclo_id}/enviar: fecha a etapa aberta (definitivo)."""
    return _post(f"meu_ciclo_metas/{int(ciclo_id)}/enviar", {}, token, GRUPO_COLABORADORES)


def ciclos_metas(token: str) -> dict:
    """GET ciclos_metas -> {hoje, ciclos} (RH e Admin)."""
    return _get("ciclos_metas", token, GRUPO_COLABORADORES)


def criar_ciclo_metas(token: str, ano: int, datas: dict) -> dict:
    """POST ciclos_metas: ano e as seis datas (etapaN_inicio/etapaN_fim, 'AAAA-MM-DD')."""
    return _post("ciclos_metas", {"ano": int(ano), **datas}, token, GRUPO_COLABORADORES)


def alterar_ciclo_metas(token: str, ciclo_id: int, datas: dict) -> dict:
    """PATCH ciclos_metas/{id}: as seis datas; só antes de a etapa 1 abrir."""
    return _request("PATCH", f"ciclos_metas/{int(ciclo_id)}", token, GRUPO_COLABORADORES, datas)


def perguntas_meta(token: str) -> dict:
    """GET perguntas_meta -> {perguntas} (ativas e inativas; RH e Admin)."""
    return _get("perguntas_meta", token, GRUPO_COLABORADORES)


def criar_pergunta_meta(token: str, texto: str, orientacao: str | None, ordem: int) -> dict:
    return _post("perguntas_meta", {"texto": texto, "orientacao": orientacao or None, "ordem": int(ordem)}, token, GRUPO_COLABORADORES)


def alterar_pergunta_meta(token: str, pergunta_id: int, texto: str, orientacao: str | None, ordem: int, ativa: bool) -> dict:
    return _request("PATCH", f"perguntas_meta/{int(pergunta_id)}", token, GRUPO_COLABORADORES,
                    {"texto": texto, "orientacao": orientacao or None, "ordem": int(ordem), "ativa": bool(ativa)})


def formularios_meta(token: str, ciclo_id: int) -> dict:
    """GET formularios_meta?ciclo_id= -> {ciclo, etapa_aberta, pessoas} (RH: todos; superior e gestor: a equipe)."""
    return _get(f"formularios_meta?ciclo_id={int(ciclo_id)}", token, GRUPO_COLABORADORES)


def formulario_meta(token: str, formulario_id: int) -> dict:
    """GET formularios_meta/{id} -> {formulario, colaborador_nome, ciclo, respostas, feedbacks, pode_dar_feedback}."""
    return _get(f"formularios_meta/{int(formulario_id)}", token, GRUPO_COLABORADORES)


def feedback_meta(token: str, formulario_id: int, etapa: int, texto: str) -> dict:
    """POST formularios_meta/{id}/feedback: superior direto ou gestor do departamento, em etapa enviada."""
    return _post(f"formularios_meta/{int(formulario_id)}/feedback", {"etapa": int(etapa), "texto": texto}, token, GRUPO_COLABORADORES)


# ---------------------------------------------------------------------------
# Configurações: Segurança e Notificações (change configuracoes-seguranca-notificacoes).
# ---------------------------------------------------------------------------
def minhas_sessoes(token: str) -> dict:
    """GET auth/minhas_sessoes -> {sessoes, sessao_atual_id}."""
    return _get("auth/minhas_sessoes", token, GRUPO_AUTENTICACAO)


def encerrar_sessao(token: str, sessao_id: int) -> dict:
    """POST auth/sessoes/{id}/encerrar: uma sessão da própria pessoa."""
    return _post(f"auth/sessoes/{int(sessao_id)}/encerrar", {}, token, GRUPO_AUTENTICACAO)


def encerrar_outras_sessoes(token: str) -> dict:
    """POST auth/sessoes/encerrar_outras -> {total_encerradas}; a sessão deste token continua."""
    return _post("auth/sessoes/encerrar_outras", {}, token, GRUPO_AUTENTICACAO)


def minhas_preferencias_aviso(token: str) -> dict:
    """GET minhas_preferencias_aviso -> {preferencias: [{assunto, plataforma, email}]}."""
    return _get("minhas_preferencias_aviso", token, GRUPO_COLABORADORES)


def salvar_preferencia_aviso(token: str, assunto: str, plataforma: bool, email: bool) -> dict:
    """PATCH minhas_preferencias_aviso: os dois canais de um assunto."""
    return _request("PATCH", "minhas_preferencias_aviso", token, GRUPO_COLABORADORES,
                    {"assunto": assunto, "plataforma": bool(plataforma), "email": bool(email)})


# ---------------------------------------------------------------------------
# Auditoria (Figma 225:6784; tarefas 34 e 35 de concluir-frontend-streamlit). Só RH e Admin.
# ---------------------------------------------------------------------------
def auditoria(token: str, dias: int = 30, recurso: str | None = None, acao: str | None = None, resultado: str | None = None,
              user_id: int | None = None) -> dict:
    """GET auditoria -> {eventos (até 300, mais recentes primeiro), recursos, acoes, usuarios_na_janela, usuarios, dias}."""
    filtros = {"dias": int(dias), "recurso": recurso, "acao": acao, "resultado": resultado, "user_id": user_id}
    consulta = "&".join(f"{k}={quote(str(v))}" for k, v in filtros.items() if v not in (None, ""))
    return _get(f"auditoria?{consulta}", token, GRUPO_COLABORADORES)


# ---------------------------------------------------------------------------
# Regras e Conformidade (Figma 287:884 e 288:886; change tela-de-regras). Só RH e Admin.
# ---------------------------------------------------------------------------
def instrumentos_normativos(token: str) -> dict:
    """GET instrumentos_normativos -> {instrumentos}."""
    return _get("instrumentos_normativos", token, GRUPO_COLABORADORES)


def criar_instrumento(token: str, dados: dict) -> dict:
    """POST instrumentos_normativos (rascunho)."""
    return _post("instrumentos_normativos", dados, token, GRUPO_COLABORADORES)


def enviar_instrumento(token: str, instrumento_id: int) -> dict:
    return _post(f"instrumentos_normativos/{int(instrumento_id)}/enviar_aprovacao", {}, token, GRUPO_COLABORADORES)


def aprovar_instrumento(token: str, instrumento_id: int) -> dict:
    return _post(f"instrumentos_normativos/{int(instrumento_id)}/aprovar", {}, token, GRUPO_COLABORADORES)


def rejeitar_instrumento(token: str, instrumento_id: int, motivo: str) -> dict:
    return _post(f"instrumentos_normativos/{int(instrumento_id)}/rejeitar", {"motivo": motivo}, token, GRUPO_COLABORADORES)


def regras_override(token: str) -> dict:
    """GET regras_override -> {overrides (com `conflitos` nas em rascunho ou pendentes)}."""
    return _get("regras_override", token, GRUPO_COLABORADORES)


def criar_override(token: str, dados: dict) -> dict:
    """POST regras_override (rascunho)."""
    return _post("regras_override", dados, token, GRUPO_COLABORADORES)


def enviar_override(token: str, override_id: int) -> dict:
    return _post(f"regras_override/{int(override_id)}/enviar_aprovacao", {}, token, GRUPO_COLABORADORES)


def aprovar_override(token: str, override_id: int, justificativa: str | None = None) -> dict:
    return _post(f"regras_override/{int(override_id)}/aprovar", {"justificativa": justificativa or None}, token, GRUPO_COLABORADORES)


def rejeitar_override(token: str, override_id: int, motivo: str) -> dict:
    return _post(f"regras_override/{int(override_id)}/rejeitar", {"motivo": motivo}, token, GRUPO_COLABORADORES)


def prioridade_override(token: str, override_id: int, prioridade: int) -> dict:
    return _request("PATCH", f"regras_override/{int(override_id)}/prioridade", token, GRUPO_COLABORADORES, {"prioridade": int(prioridade)})


def simular_override(token: str, override_id: int) -> dict:
    """GET regras_override/{id}/simular -> {override_simulado, total_afetados, departamentos, detalhes, conflitos}."""
    return _get(f"regras_override/{int(override_id)}/simular", token, GRUPO_COLABORADORES)


# ---------------------------------------------------------------------------
# Desligamento (Figma 224:4056 e 249:3075; change fluxo-de-desligamento).
# ---------------------------------------------------------------------------
def pedir_desligamento(token: str, colaborador_id: int, tipo: str, data_prevista: str, dias_aviso: int, motivo: str) -> dict:
    """POST solicitacoes_desligamento: o próprio (qualquer perfil com ficha) ou, para o gestor, alguém da equipe."""
    return _post("solicitacoes_desligamento", {"colaborador_id": int(colaborador_id), "tipo_desligamento": tipo, "data_prevista": data_prevista,
                                               "dias_aviso": int(dias_aviso), "motivo_solicitacao": motivo}, token, GRUPO_DESLIGAMENTOS)


def meus_desligamentos(token: str) -> dict:
    """GET minhas_solicitacoes_desligamento -> os pedidos criados pela conta."""
    return _get("minhas_solicitacoes_desligamento", token, GRUPO_DESLIGAMENTOS)


def cancelar_desligamento(token: str, solicitacao_id: int, motivo: str) -> dict:
    return _post(f"solicitacoes_desligamento/{int(solicitacao_id)}/cancelar", {"motivo_cancelamento": motivo}, token, GRUPO_DESLIGAMENTOS)


def desligamentos_rh(token: str) -> dict:
    """GET solicitacoes_desligamento (todos) -> {solicitacoes (com nomes), contagens} (só RH)."""
    return _get("solicitacoes_desligamento", token, GRUPO_DESLIGAMENTOS)


def desligamento(token: str, solicitacao_id: int) -> dict:
    """GET solicitacoes_desligamento/{id} -> {solicitacao, colaborador, departamento, checklist}."""
    return _get(f"solicitacoes_desligamento/{int(solicitacao_id)}", token, GRUPO_DESLIGAMENTOS)


def assumir_desligamento(token: str, solicitacao_id: int) -> dict:
    return _post(f"solicitacoes_desligamento/{int(solicitacao_id)}/iniciar_analise", {}, token, GRUPO_DESLIGAMENTOS)


def aprovar_desligamento(token: str, solicitacao_id: int, data_efetiva: str, motivo: str) -> dict:
    return _post(f"solicitacoes_desligamento/{int(solicitacao_id)}/aprovar", {"data_efetiva": data_efetiva, "motivo_decisao": motivo}, token, GRUPO_DESLIGAMENTOS)


def rejeitar_desligamento(token: str, solicitacao_id: int, motivo: str) -> dict:
    return _post(f"solicitacoes_desligamento/{int(solicitacao_id)}/rejeitar", {"motivo_decisao": motivo}, token, GRUPO_DESLIGAMENTOS)


def concluir_desligamento(token: str, solicitacao_id: int) -> dict:
    return _post(f"solicitacoes_desligamento/{int(solicitacao_id)}/concluir", {}, token, GRUPO_DESLIGAMENTOS)


def marcar_checklist_desligamento(token: str, solicitacao_id: int, item_id: int, feito: bool) -> dict:
    return _post(f"solicitacoes_desligamento/{int(solicitacao_id)}/checklist/{int(item_id)}", {"feito": bool(feito)}, token, GRUPO_DESLIGAMENTOS)


# ---------------------------------------------------------------------------
# Pesquisa de clima (change pesquisa-clima-e-avaliacao-360)
# ---------------------------------------------------------------------------
def minhas_pesquisas_clima(token: str) -> dict:
    """GET minhas_pesquisas_clima -> {hoje, pesquisas: [{aberta, respondida, perguntas (as que faltam, com a escala)}]}."""
    return _get("minhas_pesquisas_clima", token, GRUPO_COLABORADORES)


def responder_pesquisa_clima(token: str, pesquisa_id: int, respostas: list[dict], comentario: str | None) -> dict:
    """POST pesquisas_clima/{id}/responder: todas as notas de uma vez ([{pergunta_id, nota}]) e o comentário anônimo."""
    return _post(f"pesquisas_clima/{int(pesquisa_id)}/responder", {"respostas": respostas, "comentario": comentario or None}, token, GRUPO_COLABORADORES)


def pesquisas_clima_rh(token: str) -> dict:
    """GET pesquisas_clima_rh -> {hoje, elegiveis, pesquisas: [{situacao, participantes, perguntas}]} (RH e Admin)."""
    return _get("pesquisas_clima_rh", token, GRUPO_COLABORADORES)


def criar_pesquisa_clima(token: str, titulo: str, descricao: str | None, data_inicio: str, data_fim: str, minimo: int, perguntas: list[dict],
                         tipo: str = "clima") -> dict:
    """POST pesquisas_clima: a pesquisa e as perguntas ([{texto, escala, dimensao?, sentido?}]) numa chamada. tipo: clima ou psicossocial."""
    return _post("pesquisas_clima", {"titulo": titulo, "descricao": descricao or None, "data_inicio": data_inicio, "data_fim": data_fim,
                                     "minimo_respostas": int(minimo), "perguntas": perguntas, "tipo": tipo}, token, GRUPO_COLABORADORES)


def adicionar_pergunta_clima(token: str, pesquisa_id: int, texto: str, escala: str, ordem: int) -> dict:
    """POST pesquisas_clima/{id}/perguntas: só antes de a pesquisa abrir."""
    return _post(f"pesquisas_clima/{int(pesquisa_id)}/perguntas", {"texto": texto, "escala": escala, "ordem": int(ordem)}, token, GRUPO_COLABORADORES)


def encerrar_pesquisa_clima(token: str, pesquisa_id: int) -> dict:
    """POST pesquisas_clima/{id}/encerrar: para de aceitar respostas e libera os resultados."""
    return _post(f"pesquisas_clima/{int(pesquisa_id)}/encerrar", {}, token, GRUPO_COLABORADORES)


def resultados_pesquisa_clima(token: str, pesquisa_id: int) -> dict:
    """GET pesquisas_clima/{id}/resultados -> {participantes, departamentos, resultados (média, favoráveis), comentarios}."""
    return _get(f"pesquisas_clima/{int(pesquisa_id)}/resultados", token, GRUPO_COLABORADORES)


# ---------------------------------------------------------------------------
# Ciclos de avaliação de desempenho (change pesquisa-clima-e-avaliacao-360)
# ---------------------------------------------------------------------------
def ciclos_avaliacao_rh(token: str) -> dict:
    """GET ciclos_avaliacao_rh -> {hoje, ciclos (com contagens), contestacoes (com nomes), departamentos, pessoas} (RH e Admin)."""
    return _get("ciclos_avaliacao_rh", token, GRUPO_COLABORADORES)


def criar_ciclo_avaliacao(token: str, nome: str, descricao: str, data_inicio: str, data_fim: str) -> dict:
    """POST ciclos_avaliacao: nasce em planejamento."""
    return _post("ciclos_avaliacao", {"nome": nome, "descricao": descricao, "data_inicio": data_inicio, "data_fim": data_fim}, token, GRUPO_COLABORADORES)


def mudar_status_ciclo_avaliacao(token: str, ciclo_id: int, status: str) -> dict:
    """PATCH ciclos_avaliacao/{id}/status: planejamento → em_andamento → fechamento → concluido (ou cancelado)."""
    return _request("PATCH", f"ciclos_avaliacao/{int(ciclo_id)}/status", token, GRUPO_COLABORADORES, {"status": status})


def avaliacoes_do_ciclo(token: str, ciclo_id: int) -> dict:
    """GET ciclos_avaliacao/{id}/avaliacoes -> {ciclo, avaliacoes (com nomes, relação, situação e nota)}."""
    return _get(f"ciclos_avaliacao/{int(ciclo_id)}/avaliacoes", token, GRUPO_COLABORADORES)


def atribuir_avaliacoes_lote(token: str, ciclo_id: int, departamento_id: int | None, autoavaliacao: bool, gestor: bool) -> dict:
    """POST ciclos_avaliacao/{id}/atribuir -> {criadas, puladas, sem_gestor}."""
    return _post(f"ciclos_avaliacao/{int(ciclo_id)}/atribuir", {"departamento_id": departamento_id or 0, "autoavaliacao": bool(autoavaliacao), "gestor": bool(gestor)},
                 token, GRUPO_COLABORADORES)


def atribuir_avaliacao(token: str, ciclo_id: int, colaborador_id: int, avaliador_user_id: int, relacao: str, inicio: str | None, fim: str | None) -> dict:
    """POST avaliacoes: uma avaliação avulsa (par, subordinado, rh...)."""
    return _post("avaliacoes", {"ciclo_avaliacao_id": int(ciclo_id), "colaborador_id": int(colaborador_id), "user_id": int(avaliador_user_id),
                                "relacao_avaliador": relacao, "periodo_incio": inicio, "periodo_fim": fim}, token, GRUPO_COLABORADORES)


def revisar_contestacao(token: str, contestacao_id: int, resposta: str) -> dict:
    """POST contestacoes_avaliacao/{id}/revisar: a resposta do RH à contestação."""
    return _post(f"contestacoes_avaliacao/{int(contestacao_id)}/revisar", {"resposta_revisao": resposta}, token, GRUPO_COLABORADORES)


# ---------------------------------------------------------------------------
# Integrações e e-mails (change integracoes-e-emails)
# ---------------------------------------------------------------------------
def fila_emails(token: str, status: str | None = None) -> dict:
    """GET email_outbox -> {contagens: {na_fila, enviados_24h, falharam_24h}, emails (destinatário mascarado)} (RH e Admin)."""
    caminho = f"email_outbox?status={quote(status)}" if status else "email_outbox"
    return _get(caminho, token, GRUPO_COLABORADORES)


def processar_fila_emails(token: str) -> dict:
    """POST email_outbox/processar -> {total_pendentes_no_lote, total_enviados, total_falhados, total_ja_no_limite}."""
    return _post("email_outbox/processar", {}, token, GRUPO_COLABORADORES)


def status_operacional(token: str) -> dict:
    """GET status_operacional -> {fila_email, tarefas_manuais_pendentes, rotina_diaria_pendente, acesso_bloqueado} (RH e Admin)."""
    return _get("status_operacional", token, GRUPO_AUTENTICACAO)


def processar_rotina_diaria(token: str) -> dict:
    """POST rotinas/processar_diarias -> {aplicadas: contagens do que mudou}. Idempotente."""
    return _post("rotinas/processar_diarias", {}, token, GRUPO_COLABORADORES)


# ---------------------------------------------------------------------------
# Canal de denúncias (change canal-de-denuncias). As três primeiras são públicas: vão sem token, e nada liga a
# denúncia a uma conta.
# ---------------------------------------------------------------------------
def enviar_denuncia(tipo: str, relato: str, quando: str | None, envolvidos: str | None, identificacao: str | None) -> dict:
    """POST denuncias (público) -> {protocolo, codigo}. O código só existe nesta resposta."""
    return _post("denuncias", {"tipo": tipo, "relato": relato, "quando": quando or None, "envolvidos": envolvidos or None,
                               "identificacao": identificacao or None}, None, GRUPO_COLABORADORES)


def acompanhar_denuncia(codigo: str) -> dict:
    """POST denuncias/acompanhar (público) -> {protocolo, tipo, status, recebida_em, resultado, parecer, mensagens}."""
    return _post("denuncias/acompanhar", {"codigo": codigo}, None, GRUPO_COLABORADORES)


def responder_denuncia(codigo: str, texto: str) -> dict:
    """POST denuncias/responder (público): quem denunciou escreve para a comissão."""
    return _post("denuncias/responder", {"codigo": codigo, "texto": texto}, None, GRUPO_COLABORADORES)


def denuncias(token: str) -> dict:
    """GET denuncias -> {contagens, denuncias} (só a comissão de ética)."""
    return _get("denuncias", token, GRUPO_COLABORADORES)


def denuncia(token: str, denuncia_id: int) -> dict:
    """GET denuncias/{id} -> {denuncia (com a identificação), mensagens}. Cada abertura fica na auditoria."""
    return _get(f"denuncias/{int(denuncia_id)}", token, GRUPO_COLABORADORES)


def mensagem_denuncia(token: str, denuncia_id: int, texto: str) -> dict:
    """POST denuncias/{id}/mensagem: a comissão escreve para quem denunciou; a primeira passa a em apuração."""
    return _post(f"denuncias/{int(denuncia_id)}/mensagem", {"texto": texto}, token, GRUPO_COLABORADORES)


def concluir_denuncia(token: str, denuncia_id: int, resultado: str, parecer: str) -> dict:
    """POST denuncias/{id}/concluir: procedente, improcedente ou inconclusiva, com o parecer final."""
    return _post(f"denuncias/{int(denuncia_id)}/concluir", {"resultado": resultado, "parecer": parecer}, token, GRUPO_COLABORADORES)


def comissao_etica(token: str) -> dict:
    """GET comissao_etica -> {membros: [{id, user_id, nome, perfil}]} (só o Admin)."""
    return _get("comissao_etica", token, GRUPO_COLABORADORES)


def incluir_comissao_etica(token: str, user_id: int) -> dict:
    return _post("comissao_etica", {"user_id": int(user_id)}, token, GRUPO_COLABORADORES)


def remover_comissao_etica(token: str, membro_id: int) -> dict:
    return _post(f"comissao_etica/{int(membro_id)}/remover", {}, token, GRUPO_COLABORADORES)


# ---------------------------------------------------------------------------
# Riscos psicossociais (NR-1; change riscos-psicossociais). A avaliação usa as rotas da pesquisa de clima com
# tipo "psicossocial"; o plano de ação tem rotas próprias.
# ---------------------------------------------------------------------------
def acoes_psicossociais(token: str, pesquisa_id: int | None = None) -> dict:
    """GET acoes_psicossociais -> {hoje, acoes} (RH e Admin)."""
    caminho = f"acoes_psicossociais?pesquisa_id={int(pesquisa_id)}" if pesquisa_id else "acoes_psicossociais"
    return _get(caminho, token, GRUPO_COLABORADORES)


def criar_acao_psicossocial(token: str, pesquisa_id: int, departamento_id: int | None, dimensao: str, nivel: str | None, medida: str,
                            responsavel: str, prazo: str) -> dict:
    return _post("acoes_psicossociais", {"pesquisa_id": int(pesquisa_id), "departamento_id": departamento_id or 0, "dimensao": dimensao,
                                         "nivel_risco": nivel or None, "medida": medida, "responsavel": responsavel, "prazo": prazo}, token, GRUPO_COLABORADORES)


def atualizar_acao_psicossocial(token: str, acao_id: int, status: str, medida: str | None = None, responsavel: str | None = None,
                                prazo: str | None = None) -> dict:
    return _request("PATCH", f"acoes_psicossociais/{int(acao_id)}", token, GRUPO_COLABORADORES,
                    {"status": status, "medida": medida or None, "responsavel": responsavel or None, "prazo": prazo or None})
