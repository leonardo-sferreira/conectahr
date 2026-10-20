"""
Regras da tela Trajetória (Figma 64:42; change trajetoria-do-colaborador). Funções puras, sem Streamlit.

Dados: `minha_trajetoria` (plano de carreira, 360 do ciclo, avaliações a preencher e recebidas, metas, PDI e
reconhecimentos) e `avaliacoes/{id}/competencias` (formulário do avaliador). Cada linha das trilhas é
{titulo, detalhe, badge, tom}, com tom "ok" (verde), "amb" (âmbar), "err" (vermelho) ou "azul".
A tela só informa o próximo nível: promoção é decisão humana, fora do sistema.
"""

from datetime import date

from onboarding_modelo import data_br

NOTAS = {1: "1 — Muito abaixo", 2: "2 — Abaixo", 3: "3 — Atende", 4: "4 — Acima", 5: "5 — Muito acima"}
_RELACOES = {"gestor": "Avaliação do gestor", "par": "Avaliação de par", "subordinado": "Avaliação de liderado", "rh": "Avaliação do RH",
             "autoavaliacao": "Autoavaliação"}
_A_PREENCHER = {"autoavaliacao": "Sua autoavaliação", "gestor": "Avaliar como gestor", "par": "Avaliar como par",
                "subordinado": "Avaliar seu gestor", "rh": "Avaliar como RH"}


def nivel(valor) -> str:
    """"l2" -> "L2"; vazio -> "—"."""
    return str(valor).upper() if valor else "—"


def _status_avaliacao(status) -> tuple[str, str]:
    if status == "enviada":
        return "Enviada", "ok"
    if status == "em_andamento":
        return "Em andamento", "amb"
    return "Pendente", "amb"


def _data(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _pct(valor) -> int:
    try:
        return max(0, min(100, round(float(valor or 0))))
    except (TypeError, ValueError):
        return 0


def titulo_360(dados: dict) -> str | None:
    ciclo = dados.get("ciclo")
    return f"Avaliação 360 — {ciclo.get('nome')}" if ciclo else None


def linhas_360(dados: dict) -> list[dict]:
    """Autoavaliação, gestor (com o nome) e pares (só a contagem) do ciclo em andamento."""
    if not dados.get("ciclo"):
        return []
    linhas = []
    if dados.get("autoavaliacao_status"):
        badge, tom = _status_avaliacao(dados["autoavaliacao_status"])
        detalhe = "Preenchida por você" if dados["autoavaliacao_status"] == "enviada" else "Para você preencher"
        linhas.append({"titulo": "Autoavaliação", "detalhe": detalhe, "badge": badge, "tom": tom})
    if dados.get("gestor_status"):
        badge, tom = _status_avaliacao(dados["gestor_status"])
        linhas.append({"titulo": "Avaliação do gestor", "detalhe": dados.get("gestor_nome") or "Gestor", "badge": badge, "tom": tom})
    total, enviadas = dados.get("pares_total") or 0, dados.get("pares_enviadas") or 0
    if total:
        linhas.append({"titulo": "Avaliação de pares", "detalhe": f"{enviadas} de {total} respondida{'s' if enviadas != 1 else ''}",
                       "badge": "Enviada" if enviadas >= total else "Pendente", "tom": "ok" if enviadas >= total else "amb"})
    return linhas


def linhas_a_preencher(dados: dict) -> list[dict]:
    """Avaliações que a pessoa tem a responder, com o avaliado e o ciclo."""
    linhas = []
    for a in dados.get("a_preencher") or []:
        titulo = _A_PREENCHER.get(a.get("relacao"), "Avaliação")
        if a.get("relacao") != "autoavaliacao" and a.get("avaliado_nome"):
            titulo = f"{titulo}: {a['avaliado_nome']}"
        badge, tom = _status_avaliacao(a.get("status"))
        linhas.append({"id": a.get("id"), "titulo": titulo, "detalhe": a.get("ciclo_nome") or "Sem ciclo", "badge": badge, "tom": tom})
    return linhas


def nota_br(valor) -> str | None:
    try:
        return f"{float(valor):.1f}".replace(".", ",")
    except (TypeError, ValueError):
        return None


def linhas_recebidas(dados: dict) -> list[dict]:
    """Avaliações enviadas sobre a pessoa. O nome do avaliador só vem do backend para gestor e RH."""
    linhas = []
    for r in dados.get("recebidas") or []:
        partes = [p for p in (r.get("avaliador_nome"), r.get("ciclo_nome"), f"Nota {nota_br(r.get('nota'))}" if nota_br(r.get("nota")) else None,
                              data_br(r.get("data_avaliacao"))) if p]
        situacao = r.get("contestacao_status")
        if situacao == "aberta":
            badge, tom = "Contestação em análise", "amb"
        elif situacao == "revisada":
            badge, tom = "Contestação revisada", "azul"
        else:
            badge, tom = "Enviada", "ok"
        linhas.append({"id": r.get("id"), "titulo": _RELACOES.get(r.get("relacao"), "Avaliação"), "detalhe": " · ".join(partes) or None,
                       "badge": badge, "tom": tom, "pode_contestar": situacao != "aberta", "resposta_rh": r.get("contestacao_resposta")})
    return linhas


def linhas_metas(metas: list[dict], hoje: date) -> list[dict]:
    """Figma 64:42: "Prazo era 15/08/2026 · 40% concluído" (Atrasada) ou "Prazo 30/11/2026 · 65% concluído"."""
    linhas = []
    for m in metas or []:
        prazo = _data(m.get("data_prazo"))
        atrasada = prazo is not None and prazo < hoje
        texto_prazo = f"Prazo era {prazo:%d/%m/%Y}" if atrasada else f"Prazo {prazo:%d/%m/%Y}" if prazo else "Sem prazo"
        linhas.append({"id": m.get("id"), "titulo": m.get("titulo") or "Meta", "detalhe": f"{texto_prazo} · {_pct(m.get('progresso_percentual'))}% concluído",
                       "badge": "Atrasada" if atrasada else "Pendente", "tom": "err" if atrasada else "amb", "progresso": _pct(m.get("progresso_percentual"))})
    return linhas


def linhas_pdi(pdi: list[dict], hoje: date) -> list[dict]:
    """Ações de PDI: "Previsto para DD/MM/AAAA · X% concluído", Atrasado depois do prazo."""
    linhas = []
    for p in pdi or []:
        prazo = _data(p.get("data_prazo"))
        atrasado = prazo is not None and prazo < hoje
        texto_prazo = f"Prazo era {prazo:%d/%m/%Y}" if atrasado else f"Previsto para {prazo:%d/%m/%Y}" if prazo else "Sem prazo"
        linhas.append({"id": p.get("id"), "titulo": p.get("titulo") or "Ação de desenvolvimento", "detalhe": f"{texto_prazo} · {_pct(p.get('progresso_percentual'))}% concluído",
                       "badge": "Atrasado" if atrasado else "Pendente", "tom": "err" if atrasado else "amb", "progresso": _pct(p.get("progresso_percentual"))})
    return linhas


def reconhecimentos(dados: dict) -> list[dict]:
    """{nome, data, mensagem}: "Ana Ribeiro (RH)" quando quem enviou é do RH, como no Figma."""
    itens = []
    for r in dados.get("reconhecimentos") or []:
        nome = r.get("remetente_nome") or "Colega"
        if str(r.get("remetente_perfil") or "").strip().upper() == "RH":
            nome = f"{nome} (RH)"
        itens.append({"nome": nome, "data": data_br(r.get("created_at")) or "", "mensagem": r.get("mensagem") or r.get("titulo") or ""})
    return itens


def respostas_alteradas(competencias: list[dict], salvas: list[dict], notas: dict, comentarios: dict) -> list[tuple[int, int, str]]:
    """(competência, nota, comentário) que mudaram em relação ao que já está salvo; sem nota não vai."""
    antes = {r.get("competencia_avaliacao_id"): (r.get("nota"), (r.get("comentario") or "").strip()) for r in salvas or []}
    mudou = []
    for c in competencias or []:
        nota = notas.get(c["id"])
        if nota is None:
            continue
        comentario = (comentarios.get(c["id"]) or "").strip()
        if antes.get(c["id"]) != (nota, comentario):
            mudou.append((c["id"], nota, comentario))
    return mudou


def validar_envio(competencias: list[dict], notas: dict) -> str | None:
    if not competencias:
        return "Esta avaliação não tem competências para responder. Fale com o RH."
    faltam = [c["nome"] for c in competencias if notas.get(c["id"]) is None]
    if faltam:
        return f"Dê uma nota a todas as competências antes de enviar (faltam {len(faltam)})."
    return None


def validar_contestacao(motivo: str) -> str | None:
    texto = (motivo or "").strip()
    if len(texto) < 5:
        return "Explique o motivo da contestação (pelo menos 5 caracteres)."
    if len(texto) > 2000:
        return "O motivo pode ter no máximo 2000 caracteres."
    return None
