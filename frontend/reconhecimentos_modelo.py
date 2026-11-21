"""
Regras das telas de reconhecimento (tarefa 66 da change concluir-frontend-streamlit): "Mural de reconhecimentos"
(Figma 291:908, 291:1075 e 291:1239), "Moderar reconhecimentos" (291:1374) e os modais 291:1631, 291:1667 e 291:1703.
Funções puras, sem Streamlit.

A visibilidade não é escolhida por quem envia: o backend grava privado quando quem envia é o gestor do departamento
de quem recebe, e público nos outros casos. O mural só lista públicos ativos, respeitando "Aparecer no mural". Nenhuma
tela oferece promoção nem punição a partir de um reconhecimento.
"""

from datetime import datetime, timedelta, timezone

from integracoes_modelo import quando as _quando

BRASILIA = timezone(timedelta(hours=-3))
ABAS = {"mural": "Mural", "recebidos": "Recebidos", "enviados": "Enviados"}
PERIODOS = {30: "últimos 30 dias", 90: "últimos 90 dias", 365: "últimos 12 meses", 0: "todo o período"}
FILTROS_MODERACAO = {"todos": "Todos", "mural": "No mural", "moderados": "Moderados"}
MAX_TITULO, MAX_MENSAGEM = 100, 1500


def iniciais(nome: str | None) -> str:
    partes = [p for p in str(nome or "").split() if p[:1].isalpha()]
    return ((partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")) if partes else "?").upper()


def _momento(valor) -> datetime | None:
    if valor in (None, ""):
        return None
    try:
        if isinstance(valor, (int, float)) or str(valor).isdigit():
            return datetime.fromtimestamp(int(valor) / 1000, tz=timezone.utc)
        m = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
        return m if m.tzinfo else m.replace(tzinfo=timezone.utc)
    except (ValueError, OSError):
        return None


def quando(valor, agora: datetime | None = None) -> str:
    """"Hoje, 09:12", "Ontem, 16:40" e, antes disso, a data completa ("06/10/2026"), como no Figma."""
    texto = _quando(valor, agora)
    if texto.startswith(("Hoje", "Ontem")) or texto == "—":
        return texto
    m = _momento(valor)
    return m.astimezone(BRASILIA).strftime("%d/%m/%Y") if m else "—"


def _base(r: dict, agora) -> dict:
    return {"id": r.get("id"), "titulo": r.get("titulo") or "", "mensagem": r.get("mensagem") or "", "competencia": r.get("competencia_nome") or "",
            "quando": quando(r.get("created_at"), agora), "privado": r.get("visibilidade") == "privado", "moderado": r.get("status") == "moderado",
            "remetente": r.get("remetente_nome") or "Alguém", "destinatario": r.get("destinatario_nome") or "Colaborador", "nota": ""}


def cartoes_mural(itens: list[dict], competencia_id=None, dias: int = 30, agora: datetime | None = None) -> list[dict]:
    agora = agora or datetime.now(timezone.utc)
    saida = []
    for r in itens:
        if competencia_id and r.get("competencia_avaliacao_id") != competencia_id:
            continue
        m = _momento(r.get("created_at"))
        if dias and m and m < agora - timedelta(days=dias):
            continue
        c = _base(r, agora)
        c.update(autor=c["remetente"], frase=f"reconheceu {c['destinatario']}", selos=[(c["competencia"], "amb")] if c["competencia"] else [])
        saida.append(c)
    return saida


def cartoes_recebidos(itens: list[dict], agora: datetime | None = None) -> list[dict]:
    saida = []
    for r in itens:
        if r.get("status") == "moderado":
            continue
        c = _base(r, agora)
        frase = "(seu gestor) deu um feedback a você" if c["privado"] else "reconheceu você"
        selos = ([(c["competencia"], "amb")] if c["competencia"] else []) + ([("Privado: só você vê", "neu")] if c["privado"] else [])
        c.update(autor=c["remetente"], frase=frase, selos=selos)
        saida.append(c)
    return saida


def cartoes_enviados(itens: list[dict], agora: datetime | None = None) -> list[dict]:
    saida = []
    for r in itens:
        c = _base(r, agora)
        selos = [(c["competencia"], "amb")] if c["competencia"] else []
        if c["privado"]:
            selos.append(("Privado", "neu"))
        if c["moderado"]:
            selos.append(("Moderado", "err"))
            motivo = r.get("motivo_moderacao") or "sem motivo informado"
            c["nota"] = f"Moderado pelo RH em {quando(r.get('updated_at'), agora)}: {motivo}"
        verbo = "deu um feedback a" if c["privado"] else "reconheceu"
        c.update(autor="Você", frase=f"{verbo} {c['destinatario']}", selos=selos)
        saida.append(c)
    return saida


def cartoes_moderacao(itens: list[dict], filtro: str = "todos", agora: datetime | None = None) -> list[dict]:
    saida = []
    for r in itens:
        c = _base(r, agora)
        if (filtro == "mural" and c["moderado"]) or (filtro == "moderados" and not c["moderado"]):
            continue
        selos = [(c["competencia"], "amb")] if c["competencia"] else []
        if c["moderado"]:
            selos.append(("Moderado", "err"))
            c["mensagem"] = "(conteúdo ocultado do mural)"
            data = _momento(r.get("updated_at"))
            quem = r.get("moderador_nome") or "RH"
            inicio = f"Moderado por {quem} em {data.astimezone(BRASILIA):%d/%m/%Y}: " if data else f"Moderado por {quem}: "
            c["nota"] = inicio + (r.get("motivo_moderacao") or "")
        c.update(autor=c["remetente"], frase=f"reconheceu {c['destinatario']}", selos=selos, pode_moderar=not c["moderado"])
        saida.append(c)
    return saida


def opcoes_colegas(organograma: dict) -> list[tuple[int, str]]:
    """[(colaborador_id, "Nome — Departamento")] em ordem de nome, para o campo "Colega"."""
    deps = {d["id"]: d.get("nome") for d in organograma.get("departamentos") or []}
    pessoas = [(c["id"], c.get("nome") or "—", deps.get(c.get("departamento_id"))) for c in organograma.get("colaboradores") or []]
    return [(i, f"{n} — {d}" if d else n) for i, n, d in sorted(pessoas, key=lambda p: p[1].lower())]


def erro_destinatario(destinatario_id, meu_colaborador_id) -> str | None:
    if destinatario_id is not None and destinatario_id == meu_colaborador_id:
        return "Não dá para reconhecer a si mesmo. Escolha outra pessoa."
    return None


def validar_envio(destinatario_id, meu_colaborador_id, competencia_id, titulo: str | None, mensagem: str | None) -> str | None:
    if destinatario_id is None:
        return "Escolha o colega."
    if erro := erro_destinatario(destinatario_id, meu_colaborador_id):
        return erro
    if competencia_id is None:
        return "Escolha a competência."
    if not (titulo or "").strip():
        return "Escreva o título."
    if len(titulo.strip()) > MAX_TITULO:
        return f"O título tem no máximo {MAX_TITULO} caracteres."
    if not (mensagem or "").strip():
        return "Escreva a mensagem."
    if len(mensagem.strip()) > MAX_MENSAGEM:
        return f"A mensagem tem no máximo {MAX_MENSAGEM} caracteres."
    return None


def validar_motivo(motivo: str | None) -> str | None:
    return "Escreva o motivo (pelo menos 5 caracteres)." if len((motivo or "").strip()) < 5 else None
