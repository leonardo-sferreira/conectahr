"""
Regras de apresentação das decisões do gestor, do RH e do Admin (tarefas 11 a 13, 20, 21 e 24 da change
concluir-frontend-streamlit). Funções puras, sem Streamlit.

- Central de Pendências (Figma seção 19, 436:1145 e 436:1308; modais 436:1473 e 436:1506): filas de
  férias (`central_de_tarefas.fila_ferias_pendentes`) e de correções de ponto (`correcoes_ponto`), já
  no escopo de quem pede; e a aba "Minhas pendências" (F13, 31:37).
- Ausências do RH (Figma 243:846; modais 243:1127 e 243:1153): `ausencias?status=...`.

Quem decide é o backend: o Gestor só a própria equipe (ou por delegação), RH e Admin todos, e ninguém o
próprio pedido. A tela só deixa de oferecer o botão que o backend recusaria (o próprio pedido).
"""

from datetime import date, timedelta

from documentos_modelo import rotulo_tipo
from onboarding_modelo import data_br
from ponto_modelo import _DIAS_LONGOS, MOTIVOS_AUSENCIA, ROTULO_CAMPO, TIPOS_AUSENCIA, hora, para_brasilia

RECENTE_DIAS = 30  # decisões dos últimos 30 dias continuam em "Minhas pendências"

_TIPOS_SOLICITACAO = {
    "alteracao_cadastral": "Alteração cadastral",
    "declaracao": "Declaração",
    "documento_avulso": "Documento avulso",
    "outra": "Solicitação ao RH",
    "privacidade_lgpd": "Pedido de privacidade",
}
_SOLICITACAO = {"recebida": ("Recebida", "amb"), "em_analise": ("Em análise", "amb"), "atendida": ("Atendida", "ok"), "indeferida": ("Indeferida", "err")}
_FERIAS = {"Pendente": ("Pendente", "amb"), "Aprovada": ("Aprovada", "ok"), "Rejeitada": ("Rejeitada", "err")}
_AUSENCIA = {"Pendente": ("Em análise", "amb"), "Aprovada": ("Aprovada", "ok"), "Registrado": ("Registrada", "ok"), "Rejeitada": ("Recusada", "err")}
_CORRECAO = {"pendente": ("Em análise", "amb"), "aprovada": ("Aprovada", "ok"), "rejeitada": ("Recusada", "err")}


def _dia(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _decidida_ha_pouco(valor, hoje: date) -> bool:
    texto = data_br(valor)
    if not texto:
        return False
    d, m, a = texto.split("/")
    return hoje - date(int(a), int(m), int(d)) <= timedelta(days=RECENTE_DIAS)


def periodo(inicio, fim) -> str:
    """"10 a 20/01/2027", "14/09/2026" ou "28/12/2026 a 03/01/2027"."""
    a, b = _dia(inicio), _dia(fim)
    if not a:
        return "—"
    if not b or a == b:
        return a.strftime("%d/%m/%Y")
    if (a.year, a.month) == (b.year, b.month):
        return f"{a.day:02d} a {b.strftime('%d/%m/%Y')}"
    return f"{a.strftime('%d/%m/%Y')} a {b.strftime('%d/%m/%Y')}"


def dias(inicio, fim) -> int:
    a, b = _dia(inicio), _dia(fim)
    return (b - a).days + 1 if a and b and b >= a else 0


def pessoas(organograma: dict) -> dict:
    """{colaborador_id: {'nome', 'detalhe', 'departamento_id'}} com o departamento como detalhe."""
    deps = {d.get("id"): d.get("nome") for d in organograma.get("departamentos") or []}
    return {
        c.get("id"): {"nome": c.get("nome") or "Colaborador", "detalhe": deps.get(c.get("departamento_id")) or "—", "departamento_id": c.get("departamento_id")}
        for c in organograma.get("colaboradores") or []
    }


def _pessoa(mapa: dict, colaborador_id) -> dict:
    return mapa.get(colaborador_id) or {"nome": f"Colaborador nº {colaborador_id}", "detalhe": "—", "departamento_id": None}


def _no_filtro(p: dict, departamento_id) -> bool:
    return not departamento_id or p["departamento_id"] == departamento_id


# ---------------------------------------------------------------------------
# Central de Pendências: filas de decisão
# ---------------------------------------------------------------------------
def linhas_ferias(fila: list[dict], mapa: dict, meu_colaborador_id, departamento_id=None) -> list[dict]:
    """Aba Férias (436:1145): {'id', 'pessoa', 'detalhe', 'dias', 'periodo', 'observacao', 'pedido_em',
    'proprio'}, do pedido mais antigo para o mais novo."""
    linhas = []
    for f in fila:
        if f.get("status") not in (None, "Pendente"):
            continue
        p = _pessoa(mapa, f.get("colaborador_id"))
        if not _no_filtro(p, departamento_id):
            continue
        qtd = f.get("quantidade_dias") or dias(f.get("data_inicio"), f.get("data_fim"))
        linhas.append({
            "id": f.get("id"),
            "pessoa": p["nome"],
            "detalhe": p["detalhe"],
            "dias": f"{qtd} dia{'s' if qtd != 1 else ''}",
            "periodo": periodo(f.get("data_inicio"), f.get("data_fim")),
            "observacao": (f.get("observacao_colaborador") or "").strip() or "—",
            "pedido_em": data_br(f.get("data_solicitacao") or f.get("created_at")) or "—",
            "proprio": meu_colaborador_id is not None and f.get("colaborador_id") == meu_colaborador_id,
            "_ordem": str(f.get("data_solicitacao") or f.get("created_at") or ""),
        })
    linhas.sort(key=lambda l: l.pop("_ordem"))
    return linhas


_TIPO_CORRECAO = {"inclusao": "Incluir marcação", "alteracao": "Corrigir horário", "desconsideracao": "Desconsiderar marcação"}


def _momento_correcao(c: dict):
    """O horário do pedido: o incluído (`valor_solicitado`) ou o da marcação a desconsiderar (`valor_original`)."""
    return c.get("valor_original") if c.get("tipo") == "desconsideracao" else c.get("valor_solicitado")


def _rotulo_correcao(c: dict) -> str:
    return _TIPO_CORRECAO.get(c.get("tipo")) or ROTULO_CAMPO.get(c.get("campo"), c.get("campo") or "—")


def linhas_correcoes(correcoes: list[dict], mapa: dict, meu_colaborador_id, departamento_id=None) -> list[dict]:
    """Aba Correções de ponto (436:1308): {'id', 'pessoa', 'detalhe', 'campo', 'dia', 'justificativa',
    'horario', 'proprio'}. No REP-P, `campo` é "Incluir marcação" ou "Desconsiderar marcação"; o dia e o horário vêm
    do horário incluído ou do da marcação a desconsiderar (Brasília)."""
    linhas = []
    for c in correcoes:
        if c.get("status") not in (None, "pendente"):
            continue
        p = _pessoa(mapa, c.get("colaborador_id"))
        if not _no_filtro(p, departamento_id):
            continue
        momento = para_brasilia(_momento_correcao(c))
        linhas.append({
            "id": c.get("id"),
            "pessoa": p["nome"],
            "detalhe": p["detalhe"],
            "campo": _rotulo_correcao(c),
            "dia": momento.strftime("%d/%m/%Y") if momento else "—",
            "justificativa": (c.get("justificativa") or "").strip() or "—",
            "horario": hora(_momento_correcao(c)) or "—",
            "original": hora(c.get("valor_original")) if c.get("tipo") != "desconsideracao" else None,
            "proprio": meu_colaborador_id is not None and c.get("colaborador_id") == meu_colaborador_id,
        })
    return linhas


def linhas_ausencias_fila(fila: list[dict], mapa: dict, meu_colaborador_id, departamento_id=None) -> list[dict]:
    """Aba Ausências da Central (tarefa 83): só tipo, período e situação — nunca o comprovante nem o motivo.
    {'id', 'pessoa', 'detalhe', 'tipo', 'periodo', 'proprio'}."""
    linhas = []
    for a in fila:
        if a.get("status") not in (None, "Pendente"):
            continue
        p = _pessoa(mapa, a.get("colaborador_id"))
        if not _no_filtro(p, departamento_id):
            continue
        linhas.append({
            "id": a.get("id"), "pessoa": p["nome"], "detalhe": p["detalhe"],
            "tipo": TIPOS_AUSENCIA.get(a.get("tipo"), a.get("tipo") or "—"),
            "periodo": periodo(a.get("data_inicio"), a.get("data_fim")),
            "proprio": meu_colaborador_id is not None and a.get("colaborador_id") == meu_colaborador_id,
        })
    return linhas


def conferencia_ferias(resposta: dict) -> list[str]:
    """O resultado de `verificar_conflito` em frases curtas (só informa, não bloqueia)."""
    partes = []
    antecedencia = resposta.get("antecedencia_dias")
    if antecedencia is not None:
        partes.append(f"Antecedência de {antecedencia} dia{'s' if antecedencia != 1 else ''}")
    cumprido = resposta.get("periodo_aquisitivo_cumprido")
    if cumprido is not None:
        partes.append("período aquisitivo cumprido" if cumprido else "período aquisitivo ainda não cumprido")
    sobrepostas = len(resposta.get("ferias_sobrepostas") or []) + len(resposta.get("ausencias_sobrepostas") or [])
    partes.append("sem sobreposição com férias ou ausências" if not sobrepostas else f"{sobrepostas} sobreposição(ões) com férias ou ausências aprovadas")
    colegas = len(resposta.get("colegas_de_ferias_no_periodo") or [])
    equipe = resposta.get("tamanho_equipe")
    if equipe:
        partes.append(f"{colegas} de {equipe} colegas do departamento de férias no período")
    return partes


def tem_alerta(resposta: dict) -> bool:
    return bool(
        resposta.get("periodo_aquisitivo_cumprido") is False
        or resposta.get("ferias_sobrepostas")
        or resposta.get("ausencias_sobrepostas")
    )


def validar_motivo(motivo: str) -> str | None:
    if len((motivo or "").strip()) < 5:
        return "Explique o motivo em pelo menos 5 caracteres."
    return None


# ---------------------------------------------------------------------------
# Central de Pendências: "Minhas pendências" (F13, 31:37)
# ---------------------------------------------------------------------------
def _item(titulo: str, detalhe: str | None, selo: tuple[str, str]) -> dict:
    return {"titulo": titulo, "detalhe": detalhe, "badge": selo[0], "tom": selo[1]}


def minhas_pendencias(central: dict, solicitacoes: list[dict], ferias: list[dict], ausencias: list[dict],
                      pendencias_doc: list[dict], correcoes: list[dict], hoje: date) -> list[dict]:
    """Seções da Central do colaborador, na ordem do Figma: [{'titulo', 'itens'}], só as que têm itens.
    Fica o que está em aberto e o que foi decidido nos últimos 30 dias."""
    secoes = []

    itens = []
    for s in solicitacoes:
        status = s.get("status") or "recebida"
        if status in ("atendida", "indeferida") and not _decidida_ha_pouco(s.get("data_decisao") or s.get("updated_at"), hoje):
            continue
        enviada = data_br(s.get("created_at") or s.get("updated_at"))
        itens.append(_item(_TIPOS_SOLICITACAO.get(s.get("tipo"), "Solicitação ao RH"), f"Enviada em {enviada}" if enviada else None, _SOLICITACAO.get(status, ("Recebida", "amb"))))
    secoes.append({"titulo": "Solicitações ao RH", "itens": itens})

    itens = []
    for f in ferias:
        status = f.get("status")
        if status not in _FERIAS or (status != "Pendente" and not _decidida_ha_pouco(f.get("data_decisao"), hoje)):
            continue
        quando = data_br(f.get("data_solicitacao")) if status == "Pendente" else data_br(f.get("data_decisao"))
        rotulo = "Solicitada em" if status == "Pendente" else "Decidida em"
        itens.append(_item(f"Férias — {periodo(f.get('data_inicio'), f.get('data_fim'))}", f"{rotulo} {quando}" if quando else None, _FERIAS[status]))
    secoes.append({"titulo": "Férias", "itens": itens})

    itens = []
    for a in ausencias:
        status = a.get("status")
        if status not in _AUSENCIA:
            continue
        fim = _dia(a.get("data_fim")) or _dia(a.get("data_inicio"))
        if status != "Pendente" and (not fim or hoje - fim > timedelta(days=RECENTE_DIAS)):
            continue
        n = dias(a.get("data_inicio"), a.get("data_fim")) or 1
        itens.append(_item(
            f"{TIPOS_AUSENCIA.get(a.get('tipo'), 'Ausência')} — {n} dia{'s' if n != 1 else ''}",
            periodo(a.get("data_inicio"), a.get("data_fim")), _AUSENCIA[status],
        ))
    secoes.append({"titulo": "Ausências", "itens": itens})

    itens = []
    for p in pendencias_doc:
        if p.get("status") != "pendente":
            continue
        prazo = _dia(p.get("prazo"))
        atrasada = prazo is not None and prazo < hoje
        itens.append(_item(f"Envio de {rotulo_tipo(p.get('tipo_documento'))}", f"Prazo: {prazo.strftime('%d/%m/%Y')}" if prazo else None, ("Atrasada", "err") if atrasada else ("Pendente", "amb")))
    secoes.append({"titulo": "Documentos pendentes", "itens": itens})

    itens = []
    if (central or {}).get("meu_ponto_status_hoje") == "Incompleto":
        itens.append(_item("Jornada de hoje incompleta", "Confira as marcações na tela Ponto", ("Pendente", "amb")))
    for c in correcoes:
        status = c.get("status") or "pendente"
        if status not in _CORRECAO or (status != "pendente" and not _decidida_ha_pouco(c.get("data_decisao"), hoje)):
            continue
        momento = para_brasilia(_momento_correcao(c))
        titulo = f"Correção de ponto — {_DIAS_LONGOS[momento.weekday()]}, {momento.strftime('%d/%m')}" if momento else "Correção de ponto"
        rotulo, pedido = _rotulo_correcao(c), hora(_momento_correcao(c))
        ligacao = {"inclusao": "às", "desconsideracao": "das"}.get(c.get("tipo"), "para")
        if c.get("tipo") == "alteracao" and hora(c.get("valor_original")):
            ligacao = f"de {hora(c.get('valor_original'))} para"
        itens.append(_item(titulo, f"{rotulo} {ligacao} {pedido}" if pedido else rotulo, _CORRECAO[status]))
    secoes.append({"titulo": "Ponto", "itens": itens})

    return [s for s in secoes if s["itens"]]


# ---------------------------------------------------------------------------
# Ausências do RH (243:846)
# ---------------------------------------------------------------------------
ABAS_AUSENCIAS = {"Pendentes": "Pendente", "Aprovadas": "Aprovada", "Registradas": "Registrado", "Rejeitadas": "Rejeitada"}
_SELO_TIPO = {"Atestado": "azul", "Licenca": "azul", "Afastamento": "azul"}


def _no_mes(valor, hoje: date) -> bool:
    texto = data_br(valor)
    return bool(texto) and texto[3:] == hoje.strftime("%m/%Y")


def resumo_ausencias(por_status: dict, hoje: date) -> dict:
    """Os quatro números do topo: pendentes, aprovadas sem registro, registradas e rejeitadas no mês."""
    return {
        "pendentes": len(por_status.get("Pendente") or []),
        "aprovadas": len(por_status.get("Aprovada") or []),
        "registradas_mes": sum(1 for a in por_status.get("Registrado") or [] if _no_mes(a.get("updated_at") or a.get("data_inicio"), hoje)),
        "rejeitadas_mes": sum(1 for a in por_status.get("Rejeitada") or [] if _no_mes(a.get("updated_at") or a.get("data_inicio"), hoje)),
    }


def linhas_ausencias(ausencias: list[dict], mapa: dict, meu_colaborador_id, tipo=None, departamento_id=None) -> list[dict]:
    """{'id', 'pessoa', 'detalhe', 'tipo', 'selo_tipo', 'periodo', 'motivo', 'comprovante', 'proprio',
    'status', 'aprovada_em'}. O motivo é a categoria e a observação; o texto livre antigo é privado."""
    linhas = []
    for a in ausencias:
        if tipo and a.get("tipo") != tipo:
            continue
        p = _pessoa(mapa, a.get("colaborador_id"))
        if not _no_filtro(p, departamento_id):
            continue
        motivo = MOTIVOS_AUSENCIA.get(a.get("motivo_tipo"))
        obs = (a.get("observacao") or "").strip()
        linhas.append({
            "id": a.get("id"),
            "pessoa": p["nome"],
            "detalhe": p["detalhe"],
            "tipo": TIPOS_AUSENCIA.get(a.get("tipo"), a.get("tipo") or "—"),
            "selo_tipo": _SELO_TIPO.get(a.get("tipo"), "neu"),
            "periodo": periodo(a.get("data_inicio"), a.get("data_fim")),
            "motivo": " · ".join(x for x in (motivo, obs) if x) or "—",
            "comprovante": bool(a.get("comprovante")),
            "proprio": meu_colaborador_id is not None and a.get("colaborador_id") == meu_colaborador_id,
            "status": a.get("status"),
            "aprovada_em": data_br(a.get("updated_at")) or "—",
        })
    return linhas


def tipos_ausencia_presentes(ausencias: list[dict]) -> list[str]:
    return sorted({a.get("tipo") for a in ausencias if a.get("tipo")}, key=lambda t: TIPOS_AUSENCIA.get(t, t))
