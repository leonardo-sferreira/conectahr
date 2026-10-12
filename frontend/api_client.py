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

import requests
import streamlit as st

_log = logging.getLogger(__name__)

_MENSAGEM_SEM_CONEXAO = "Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente em instantes."
_MENSAGEM_GENERICA = "Erro inesperado. Tente novamente."
_MENSAGEM_SESSAO_TERMINOU = "Sua sessão terminou. Entre de novo para continuar."

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


_PAUSA_429_S = 3


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
        if resp.status_code == 429:
            # Plano gratuito do Xano: 10 requisições a cada 20 s. Uma nova tentativa depois de uma pausa curta
            # evita que uma tela com várias consultas mostre erro só por ter chegado ao limite.
            time.sleep(_PAUSA_429_S)
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


def meu_perfil_colaborador(token: str) -> dict:
    """GET meu_perfil_colaborador -> {colaborador, cargo, departamento, ...} do próprio usuário."""
    return _get("meu_perfil_colaborador", token, GRUPO_COLABORADORES)


def organograma(token: str) -> dict:
    """GET organograma -> {departamentos, cargos, colaboradores} (campos não sensíveis, qualquer perfil)."""
    return _get("organograma", token, GRUPO_DEPARTAMENTOS)


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


def solicitar_ferias(token: str, data_inicio: str, data_fim: str, quantidade_dias: int, observacao: str | None) -> dict:
    """POST ferias/solicitacoes -> {solicitacao}. Quem decide é o gestor ou o RH."""
    corpo = {"data_inicio": data_inicio, "data_fim": data_fim, "quantidade_dias": int(quantidade_dias)}
    if observacao:
        corpo["observacao"] = observacao
    return _post("ferias/solicitacoes", corpo, token, GRUPO_FERIAS)


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


def atender_solicitacao(token: str, solicitacao_id: int, justificativa: str | None = None) -> dict:
    """POST solicitacoes/{id}/atender. Para alteração cadastral, não muda o cadastro sozinho."""
    corpo = {"justificativa_decisao": justificativa} if justificativa else {}
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
