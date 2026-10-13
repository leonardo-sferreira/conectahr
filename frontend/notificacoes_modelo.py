"""
Regras de apresentação do sino de notificações (Figma 197:77, "Dropdown/Notificações"; pedido do usuário em 12/10/2026).
Funções puras, sem Streamlit.

Dados: `minhas_notificacoes` -> {total_nao_lidas, notificacoes: [{id, tipo, titulo, mensagem, recurso, registro_id, lida,
lida_em, criada_em}]}, das mais recentes. Cada notificação leva à tela do assunto (`destino`): o app.py troca de página
pela marca `ir_*` em `st.session_state`.
"""

from datetime import datetime, timedelta

from ponto_modelo import BRASILIA, para_brasilia

# A tela de cada assunto, pelo tipo e, quando o tipo não diz, pelo recurso. A marca é a que o app.py entende (`_ATALHOS`).
_DESTINO_TIPO = {
    "ferias_aprovada": "ir_ferias",
    "ponto_ajustado": "ir_ponto",
    "descanso_interjornada": "ir_folha",
    "solicitacao_respondida": "ir_central",
    "beneficio_atualizado": "ir_beneficios",
    "documento_vencendo": "ir_documentos",
    "avaliacao_disponivel": "ir_central",
}
_DESTINO_RECURSO = {
    "ferias": "ir_ferias",
    "registro_ponto": "ir_ponto",
    "correcao_ponto": "ir_ponto",
    "ausencia": "ir_ponto",
    "solicitacao_rh": "ir_central",
    "beneficio": "ir_beneficios",
    "documento": "ir_documentos",
    "pendencia_documento": "ir_documentos",
    "avaliacao": "ir_central",
}


def destino(n: dict) -> str:
    """A marca da tela do assunto (`ir_ferias`, `ir_ponto`...); sem correspondência, o Início."""
    return _DESTINO_TIPO.get(n.get("tipo")) or _DESTINO_RECURSO.get(n.get("recurso")) or "ir_inicio"


def quando(valor, agora: datetime | None = None) -> str:
    """"agora", "há 5 min", "há 2 horas", "ontem" ou "03/10" (horário de Brasília)."""
    momento = para_brasilia(valor)
    if momento is None:
        return ""
    agora = agora or datetime.now(BRASILIA)
    segundos = (agora - momento).total_seconds()
    if segundos < 60:
        return "agora"
    if segundos < 3600:
        return f"há {int(segundos // 60)} min"
    if momento.date() == agora.date():
        horas = int(segundos // 3600)
        return f"há {horas} hora{'s' if horas != 1 else ''}"
    if momento.date() == agora.date() - timedelta(days=1):
        return "ontem"
    return f"{momento:%d/%m}" if momento.year == agora.year else f"{momento:%d/%m/%Y}"


def rotulo_nao_lidas(total: int) -> str:
    """O selo do topo do painel: "2 não lidas", "1 não lida" ou "Tudo lido"."""
    if not total:
        return "Tudo lido"
    return f"{total} não lida{'s' if total != 1 else ''}"


def resumo(resposta: dict) -> tuple[int, list[dict]]:
    """(não lidas, notificações em ordem: as mais recentes primeiro)."""
    lista = list(resposta.get("notificacoes") or [])
    lista.sort(key=lambda n: (para_brasilia(n.get("criada_em")) or datetime.min.replace(tzinfo=BRASILIA)), reverse=True)
    total = resposta.get("total_nao_lidas")
    if total is None:
        total = sum(1 for n in lista if not n.get("lida"))
    return int(total), lista
