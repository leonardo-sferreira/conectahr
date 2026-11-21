"""
SLA de solicitações (change sla-de-solicitacoes, D5 e D6): a situação do prazo, o selo "Responder até" e a ordem
das filas, mais as linhas da aba "SLA de solicitações" de Configurações. Funções puras, sem Streamlit.

O prazo (`prazo_sla`) e o ponto de "perto de vencer" (`alerta_sla`, 80% das horas úteis) são gravados pelo backend na
abertura do pedido; aqui só se comparam com a hora atual. Pedido aberto antes da change não tem prazo: "Sem prazo".
Figma: "Selo/Responder até (SLA)" e "Configurações — SLA de solicitações" (Admin e RH), seção 5, claro e escuro.
"""

from datetime import datetime, timedelta, timezone

# O Brasil não tem horário de verão desde 2019: São Paulo é UTC-3 o ano todo.
FUSO = timezone(timedelta(hours=-3))
PADRAO_HORAS = 72
MAXIMO_HORAS = 720
MAXIMO_LGPD = 240

# Os 10 tipos, na ordem do Figma, com o setor responsável (D1) e o texto da linha quando vale o padrão.
TIPOS = [
    ("alteracao_cadastral", "Alteração cadastral", "Padrão do sistema"),
    ("declaracao", "Declaração", "Padrão do sistema"),
    ("documento_avulso", "Documento avulso", "Padrão do sistema"),
    ("outra", "Outra solicitação", "Padrão do sistema"),
    ("privacidade_lgpd", "Privacidade (LGPD)", "Nunca passa do prazo legal de 15 dias"),
    ("desligamento", "Desligamento", "Padrão do sistema"),
    ("ferias", "Férias", "Padrão do sistema"),
    ("ausencia", "Ausência", "O superior acompanha"),
    ("correcao_ponto", "Correção de ponto", "Padrão do sistema"),
    ("acesso", "Pedido de acesso", "Padrão do sistema"),
]
NOMES = {t: n for t, n, _ in TIPOS}
SETORES = {"rh": "RH", "gestor": "Gestor", "admin": "Admin"}
TEXTO_ABA = ("Prazo de resposta de cada tipo de pedido, em horas úteis: só contam os dias de segunda a sexta, sem os "
             "feriados nacionais. Mudar o prazo vale para os pedidos abertos depois.")
TEXTO_SO_ADMIN = " Só o Admin altera o prazo."
COMO_CONTA = "De 1 a 720 horas úteis. 24 horas úteis = 1 dia útil."


def instante(valor) -> datetime | None:
    """O timestamp do Xano (milissegundos, ou texto ISO) como data e hora com fuso; None se vazio."""
    if valor in (None, "", 0):
        return None
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(valor / 1000, tz=timezone.utc)
    try:
        d = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _local(d: datetime) -> str:
    return d.astimezone(FUSO).strftime("%d/%m %H:%M")


def situacao(item: dict, agora: datetime | None = None) -> str:
    """'sem_prazo', 'no_prazo', 'perto' (a partir de `alerta_sla`) ou 'vencido' (depois de `prazo_sla`)."""
    prazo = instante(item.get("prazo_sla"))
    if prazo is None:
        return "sem_prazo"
    agora = agora or datetime.now(timezone.utc)
    if agora > prazo:
        return "vencido"
    alerta = instante(item.get("alerta_sla"))
    if alerta is not None and agora >= alerta:
        return "perto"
    return "no_prazo"


def selo(item: dict, agora: datetime | None = None) -> tuple[str, str]:
    """(texto, tom de `crh-selo`), como no Figma: verde no prazo, âmbar perto de vencer, vermelho vencido, cinza sem prazo."""
    s = situacao(item, agora)
    if s == "sem_prazo":
        return "Sem prazo", "neu"
    prazo = _local(instante(item["prazo_sla"]))
    if s == "vencido":
        return f"Venceu em {prazo}", "err"
    return f"Responder até {prazo}", "amb" if s == "perto" else "ok"


def ordenar(itens: list[dict]) -> list[dict]:
    """Pelo prazo mais próximo (os vencidos, que têm o prazo mais antigo, vêm primeiro); sem prazo no fim."""
    return sorted(itens, key=lambda i: (instante(i.get("prazo_sla")) is None, instante(i.get("prazo_sla")) or datetime.max.replace(tzinfo=timezone.utc)))


def linhas_config(slas: list[dict]) -> list[dict]:
    """As 10 linhas da aba, na ordem do Figma: {tipo, nome, descricao, setor, horas, prazo, padrao, id}."""
    por_tipo = {s.get("tipo_solicitacao"): s for s in slas or []}
    linhas = []
    for tipo, nome, texto_padrao in TIPOS:
        s = por_tipo.get(tipo) or {}
        padrao = bool(s.get("padrao", True))
        horas = int(s.get("horas_uteis") or PADRAO_HORAS)
        descricao = texto_padrao
        if not padrao:
            quando = instante(s.get("atualizado_em"))
            quem = s.get("atualizado_por") or "Admin"
            descricao = f"Alterado por {quem} em {quando.astimezone(FUSO).strftime('%d/%m/%Y')}" if quando else f"Alterado por {quem}"
        linhas.append({"tipo": tipo, "nome": nome, "descricao": descricao, "setor": SETORES.get(s.get("setor"), "—"), "horas": horas,
                       "prazo": f"{horas} h úteis", "padrao": padrao, "id": s.get("id")})
    return linhas


def validar_horas(tipo: str, horas) -> str | None:
    try:
        horas = int(horas)
    except (TypeError, ValueError):
        return "Informe o prazo em horas úteis."
    if not 1 <= horas <= MAXIMO_HORAS:
        return "O prazo vai de 1 a 720 horas úteis."
    if tipo == "privacidade_lgpd" and horas > MAXIMO_LGPD:
        return "O pedido LGPD tem prazo legal de 15 dias: o SLA vai até 240 horas úteis."
    return None


_ABERTOS = {"recebida", "em_analise", "pendente", "Pendente"}


def aberto(item: dict) -> bool:
    """Pedido ainda sem decisão (os nomes dos status variam por tabela)."""
    return item.get("status") in _ABERTOS or item.get("status") is None


def selo_html(item: dict, agora: datetime | None = None) -> str:
    """O selo pronto para `st.html`, só para pedido em aberto (o decidido não tem prazo a cumprir)."""
    if not aberto(item):
        return ""
    texto, tom = selo(item, agora)
    return f'<span class="crh-selo {tom}">{texto}</span>'


def selo_texto(item: dict, agora: datetime | None = None) -> str:
    """O texto do selo para "Meus pedidos" (a linha já tem o selo da situação), só com o pedido em aberto."""
    return selo(item, agora)[0] if aberto(item) else ""
