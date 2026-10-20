"""
Regras da tela "Integrações e e-mails" do Admin (Figma 249:7847; change integracoes-e-emails). Funções puras, sem
Streamlit.

O plano do Xano não tem tarefas agendadas: os e-mails de aviso ficam na fila (`email_outbox`) até alguém processá-la,
e a rotina diária (férias encerradas, ponto em aberto, status de afastamento, desligamentos com data efetiva) e os
documentos vencidos também rodam por botão. O código de acesso do login e o "esqueci minha senha" saem na hora e não
passam pela fila.
"""

import re
from datetime import datetime, timedelta, timezone

ABAS = ["Fila de e-mails", "Tarefas manuais", "Modelos"]
SITUACOES = {"pendente": ("Pendente", "amb"), "enviado": ("Enviado", "ok"), "falhou": ("Falhou", "err")}
# Nome legível do tipo (a chave de idempotência sem os números).
TIPOS = {
    "solicitacao_respondida": "Solicitação respondida",
    "avaliacao_disponivel": "Avaliação disponível",
    "avaliacoes_lote": "Avaliações para fazer",
    "documento_vencendo": "Documento vencendo",
    "ferias_aprovada": "Férias aprovadas",
    "alerta_acesso_suspeito": "Alerta de segurança",
    "alerta_troca_email": "Troca de e-mail",
}
_ROTINA = {
    "desligamentos_concluidos": "desligamentos com data efetiva concluídos",
    "ferias_concluidas": "férias encerradas",
    "ponto_para_incompleto": "dias de ponto em aberto marcados como incompletos",
    "instrumentos_expirados": "instrumentos normativos expirados",
    "colaboradores_para_ferias": "pessoas que entraram em férias",
    "colaboradores_para_afastado": "pessoas afastadas",
    "colaboradores_para_ativo": "pessoas que voltaram a ativo",
    "sessoes_ip_dispositivo_limpos": "sessões antigas com IP e dispositivo apagados",
    "emails_enviados_limpos": "e-mails enviados antigos apagados",
    "desligados_prazo_cumprido": "desligados com prazo de guarda cumprido",
}
BREVO_PAINEL = "https://app.brevo.com/templates/listing"


def tipo(chave: str | None) -> str:
    """"solicitacao_respondida_12" → "solicitacao_respondida" (sem os pedaços que são números ou data)."""
    partes = [p for p in str(chave or "").split("_") if p and not re.fullmatch(r"\d+", p)]
    return "_".join(partes) or "—"


def tipo_legivel(chave: str | None) -> str:
    t = tipo(chave)
    return TIPOS.get(t, t.replace("_", " ").capitalize() if t != "—" else "—")


def situacao(status) -> tuple[str, str]:
    return SITUACOES.get(status, (str(status or "—"), "neu"))


def quando(valor, agora: datetime | None = None) -> str:
    """"Hoje, 09:40", "Ontem, 18:02" ou "15/10, 08:00", no horário de Brasília (UTC-3). Aceita ISO ou milissegundos."""
    if valor in (None, ""):
        return "—"
    try:
        if isinstance(valor, (int, float)) or str(valor).isdigit():
            momento = datetime.fromtimestamp(int(valor) / 1000, tz=timezone.utc)
        else:
            momento = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
            if momento.tzinfo is None:
                momento = momento.replace(tzinfo=timezone.utc)
    except (ValueError, OSError):
        return "—"
    brasilia = timezone(timedelta(hours=-3))
    local = momento.astimezone(brasilia)
    hoje = (agora or datetime.now(timezone.utc)).astimezone(brasilia).date()
    hora = local.strftime("%H:%M")
    if local.date() == hoje:
        return f"Hoje, {hora}"
    if (hoje - local.date()).days == 1:
        return f"Ontem, {hora}"
    return f"{local.strftime('%d/%m')}, {hora}"


def indicadores(contagens: dict, status_op: dict) -> list[tuple[str, str, str]]:
    bloqueadas = ((status_op or {}).get("acesso_bloqueado") or {}).get("contas_bloqueadas_por_senha")
    falharam = contagens.get("falharam_24h") or 0
    return [("E-mails na fila", str(contagens.get("na_fila") or 0), "ambar"),
            ("Falharam (24h)", str(falharam), "negativo" if falharam else ""),
            ("Enviados (24h)", str(contagens.get("enviados_24h") or 0), "verde"),
            ("Contas bloqueadas por senha", "—" if bloqueadas is None else str(bloqueadas), "negativo" if bloqueadas else "")]


def linhas_fila(emails: list[dict], agora: datetime | None = None) -> list[dict]:
    return [{"id": e.get("id"), "assunto": e.get("assunto") or "—", "tipo": tipo_legivel(e.get("chave")), "chave": tipo(e.get("chave")),
             "destinatario": e.get("destinatario") or "—", "criado": quando(e.get("criado_em"), agora),
             "tentativas": f"{e.get('tentativas') or 0} de {e.get('max_tentativas') or 3}", "situacao": situacao(e.get("status")),
             "erro": e.get("ultimo_erro") if e.get("status") != "enviado" else None, "destaque": e.get("status") == "falhou"} for e in emails]


def resumo_processamento(r: dict) -> str:
    enviados, falhados, limite = r.get("total_enviados") or 0, r.get("total_falhados") or 0, r.get("total_ja_no_limite") or 0
    if not (r.get("total_pendentes_no_lote") or 0):
        return "Nenhum e-mail na fila."
    partes = [f"{enviados} enviado{'s' if enviados != 1 else ''}"]
    if falhados:
        partes.append(f"{falhados} com erro (tenta de novo na próxima vez)")
    if limite:
        partes.append(f"{limite} desistido{'s' if limite != 1 else ''} depois de 3 tentativas")
    return "Fila processada: " + "; ".join(partes) + "."


def tarefas(status_op: dict) -> list[dict]:
    """Tarefas manuais (Figma: cartão "Tarefas manuais pendentes"): rótulo, detalhe, quantidade e a ação."""
    pend = (status_op or {}).get("tarefas_manuais_pendentes") or {}
    rotina = (status_op or {}).get("rotina_diaria_pendente") or {}
    n_rotina = sum(v for v in rotina.values() if isinstance(v, (int, float)))
    return [
        {"chave": "rotina", "titulo": "Rotina diária", "acao": "Rodar rotina",
         "detalhe": "Férias encerradas, ponto em aberto, entrada e volta de afastamento, desligamentos com data efetiva e limpezas de prazo.",
         "quantidade": int(n_rotina)},
        {"chave": "desligamentos", "titulo": "Desligamento com data efetiva vencida", "acao": None,
         "detalhe": "A rotina diária conclui; se o checklist de saída estiver incompleto, conclua em Desligamentos.",
         "quantidade": int(pend.get("desligamentos_vencidos_nao_concluidos") or 0)},
        {"chave": "documentos", "titulo": "Documentos vencidos para processar", "acao": "Processar documentos",
         "detalhe": "Marca os vencidos e cria os alertas de renovação.", "quantidade": int(pend.get("documentos_vencidos_nao_processados") or 0)},
    ]


def resumo_rotina(r: dict) -> str:
    aplicadas = {k: v for k, v in (r.get("aplicadas") or {}).items() if isinstance(v, (int, float)) and v}
    if not aplicadas:
        return "Rotina diária rodada: nada para mudar hoje."
    return "Rotina diária rodada: " + "; ".join(f"{v} {_ROTINA.get(k, k.replace('_', ' '))}" for k, v in aplicadas.items()) + "."
