"""
Regras de "Metas e PDI da equipe" (F16; change concluir-metas-pdi-equipe, decisões D1 a D5), sem Streamlit.

Dados de `minha_equipe/metas_pdi` GET: só os liderados diretos, com título, prazo, progresso e situação de cada meta e
ação de PDI (D1); as reuniões 1:1 que o gestor registrou (D4); os ciclos em andamento; e as pessoas para quem ele pode
criar meta (liderados diretos e o departamento de que é gestor, D2).
"""

from datetime import date, datetime, timedelta, timezone

DIAS_SEM_CHECKIN = 30
BRASILIA = timezone(timedelta(hours=-3))
DIAS_SEMANA = ("Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo")
SITUACOES_REUNIAO = {"agendada": ("Agendada", "azul"), "realizada": ("Realizada", "ok"), "cancelada": ("Cancelada", "neu")}
PROGRESSOS = list(range(0, 101, 5))


def _data(valor) -> date | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, (int, float)):  # timestamp do Xano, em milissegundos
        return datetime.fromtimestamp(valor / 1000).date()
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def hoje_brasilia() -> date:
    """A data de hoje no horário de Brasília (o servidor pode estar em UTC)."""
    return datetime.now(BRASILIA).date()


def fora_da_tela(dados: dict, pessoa_id) -> str | None:
    """Nome da pessoa do departamento que não é liderada direta: a meta ou o PDI dela não aparece no F16 (D1)."""
    if pessoa_id is None or any(p.get("id") == pessoa_id for p in dados.get("liderados") or []):
        return None
    return nomes(dados).get(pessoa_id)


def br(valor) -> str:
    d = _data(valor)
    return d.strftime("%d/%m/%Y") if d else "—"


def pct(valor) -> int:
    try:
        return max(0, min(100, round(float(valor or 0))))
    except (TypeError, ValueError):
        return 0


def nomes(dados: dict) -> dict:
    """{colaborador_id: nome} dos liderados diretos e das pessoas do departamento."""
    saida = {p.get("id"): p.get("nome") or "—" for p in dados.get("pessoas_meta") or []}
    saida.update({p.get("id"): p.get("nome") or "—" for p in dados.get("liderados") or []})
    return saida


def pessoas_para_meta(dados: dict) -> list[dict]:
    """Liderados diretos e pessoas do departamento do gestor, sem repetir, em ordem alfabética (D2)."""
    vistos, saida = set(), []
    for p in list(dados.get("liderados") or []) + list(dados.get("pessoas_meta") or []):
        if p.get("id") is not None and p["id"] not in vistos:
            vistos.add(p["id"])
            saida.append({"id": p["id"], "nome": p.get("nome") or "—"})
    return sorted(saida, key=lambda p: p["nome"].lower())


def situacao_meta(meta: dict, hoje: date) -> tuple[str, str]:
    """(rótulo, tom do selo)."""
    status = meta.get("status") or "planejada"
    if status == "concluida":
        return "Concluída", "ok"
    if status == "cancelada":
        return "Cancelada", "neu"
    prazo = _data(meta.get("data_prazo"))
    if prazo and prazo < hoje:
        return "Atrasada", "err"
    if status == "planejada":
        return "Planejada", "neu"
    return "Em dia", "ok"


def ultimo_checkin(meta: dict, hoje: date) -> str:
    feito = _data(meta.get("data_checkin_realizado"))
    if feito is None:
        return "Sem check-in"
    dias = (hoje - feito).days
    if dias > DIAS_SEM_CHECKIN:
        return f"Sem check-in há {dias} dias"
    return f"Último check-in: {feito:%d/%m/%Y}"


def linhas_metas(dados: dict, hoje: date, pessoa_id=None) -> list[dict]:
    """As metas dos liderados diretos: atrasadas primeiro, depois as abertas pelo prazo e, no fim, as concluídas."""
    quem = nomes(dados)
    saida = []
    for m in dados.get("metas") or []:
        if pessoa_id is not None and m.get("colaborador_id") != pessoa_id:
            continue
        rotulo, tom = situacao_meta(m, hoje)
        saida.append({"id": m.get("id"), "titulo": m.get("titulo") or "—", "pessoa": quem.get(m.get("colaborador_id"), "—"),
                      "colaborador_id": m.get("colaborador_id"), "prazo": br(m.get("data_prazo")), "progresso": pct(m.get("progresso_percentual")),
                      "situacao": rotulo, "tom": tom, "detalhe": ultimo_checkin(m, hoje),
                      "aberta": (m.get("status") or "planejada") not in ("concluida", "cancelada"),
                      "_ordem": (0 if rotulo == "Atrasada" else 2 if rotulo == "Concluída" else 1, _data(m.get("data_prazo")) or date.max)})
    return [{k: v for k, v in l.items() if k != "_ordem"} for l in sorted(saida, key=lambda l: l["_ordem"])]


def linhas_pdi(dados: dict, pessoa_id=None) -> list[dict]:
    quem = nomes(dados)
    saida = []
    for p in dados.get("pdis") or []:
        if pessoa_id is not None and p.get("colaborador_id") != pessoa_id:
            continue
        primeiro_nome = (quem.get(p.get("colaborador_id")) or "—").split(" ")[0]
        saida.append({"id": p.get("id"), "rotulo": f"{primeiro_nome} — {p.get('titulo') or '—'}", "progresso": pct(p.get("progresso_percentual")),
                      "prazo": br(p.get("data_prazo")), "concluido": p.get("status") == "concluido"})
    return saida


def quando_reuniao(r: dict) -> str:
    d = _data(r.get("data_reuniao"))
    if d is None:
        return "—"
    texto = f"{DIAS_SEMANA[d.weekday()]}, {d:%d/%m/%Y}"
    return texto + (f" às {r['hora']}" if r.get("hora") else "")


def reunioes(dados: dict, hoje: date, pessoa_id=None) -> dict:
    """{"proximas": agendadas de hoje em diante (as mais próximas primeiro), "historico": o resto (as mais recentes primeiro)}.
    Sem situação: registro antigo, já realizado."""
    quem = nomes(dados)
    proximas, historico = [], []
    for r in dados.get("reunioes") or []:
        if pessoa_id is not None and r.get("colaborador_id") != pessoa_id:
            continue
        situacao = r.get("situacao") or "realizada"
        rotulo, tom = SITUACOES_REUNIAO.get(situacao, ("Realizada", "ok"))
        d = _data(r.get("data_reuniao"))
        pauta = " ".join(str(r.get("assuntos") or "").split())
        detalhe = quando_reuniao(r) + (f" · pauta: {pauta[:80]}{'…' if len(pauta) > 80 else ''}" if pauta else "")
        linha = {"id": r.get("id"), "pessoa": quem.get(r.get("colaborador_id"), "—"), "detalhe": detalhe, "situacao": rotulo, "tom": tom,
                 "agendada": situacao == "agendada", "atrasada": situacao == "agendada" and d is not None and d < hoje,
                 "_data": d or date.min, "_hora": r.get("hora") or ""}
        (proximas if situacao == "agendada" else historico).append(linha)
    proximas.sort(key=lambda l: (l["_data"], l["_hora"]))
    historico.sort(key=lambda l: (l["_data"], l["_hora"]), reverse=True)
    limpar = lambda ls: [{k: v for k, v in l.items() if not k.startswith("_")} for l in ls]  # noqa: E731
    return {"proximas": limpar(proximas), "historico": limpar(historico)}


def hora_valida(texto: str | None) -> bool:
    t = (texto or "").strip()
    if len(t) != 5 or t[2] != ":" or not (t[:2].isdigit() and t[3:].isdigit()):
        return False
    return int(t[:2]) <= 23 and int(t[3:]) <= 59


def validar_meta(pessoa_id, ciclo_id, titulo: str | None, como_medir: str | None, prazo: date | None, hoje: date) -> str | None:
    if not pessoa_id:
        return "Escolha a pessoa."
    if not ciclo_id:
        return "Não há ciclo de avaliação em andamento. Peça ao RH para abrir um."
    titulo = (titulo or "").strip()
    if len(titulo) < 5:
        return "Descreva a meta (pelo menos 5 caracteres)."
    if len(titulo) > 500:
        return "A meta pode ter até 500 caracteres."
    como = (como_medir or "").strip()
    if len(como) < 3:
        return "Diga como medir a meta."
    if len(como) > 300:
        return "\"Como medir\" pode ter até 300 caracteres."
    if prazo is None:
        return "Informe o prazo."
    if prazo < hoje:
        return "O prazo não pode estar no passado."
    return None


def validar_checkin(progresso, comentario: str | None) -> str | None:
    if progresso is None or not 0 <= int(progresso) <= 100:
        return "Escolha o novo progresso, de 0% a 100%."
    if len((comentario or "").strip()) > 2000:
        return "O texto pode ter até 2000 caracteres."
    return None


def validar_pdi(pessoa_id, ciclo_id, titulo: str | None, acao: str | None, prazo: date | None, hoje: date) -> str | None:
    if not pessoa_id:
        return "Escolha a pessoa."
    if not ciclo_id:
        return "Não há ciclo de avaliação em andamento. Peça ao RH para abrir um."
    titulo = (titulo or "").strip()
    if len(titulo) < 3:
        return "Dê um título à ação (pelo menos 3 caracteres)."
    if len(titulo) > 150:
        return "O título pode ter até 150 caracteres."
    acao = (acao or "").strip()
    if len(acao) < 5:
        return "Descreva a ação de desenvolvimento."
    if len(acao) > 2000:
        return "A ação pode ter até 2000 caracteres."
    if prazo is not None and prazo < hoje:
        return "O prazo não pode estar no passado."
    return None


def validar_reuniao(pessoa_id, data_reuniao: date | None, hora: str | None, pauta: str | None, hoje: date) -> str | None:
    if not pessoa_id:
        return "Escolha a pessoa."
    if data_reuniao is None:
        return "Informe a data."
    if data_reuniao < hoje:
        return "Para agendar, a data precisa ser hoje ou depois."
    if hora and not hora_valida(hora):
        return "Hora inválida. Use HH:MM."
    pauta = (pauta or "").strip()
    if len(pauta) < 3:
        return "Escreva a pauta da reunião."
    if len(pauta) > 2000:
        return "A pauta pode ter até 2000 caracteres."
    return None


def validar_situacao(situacao: str | None, texto: str | None) -> str | None:
    if situacao not in ("realizada", "cancelada"):
        return "Escolha se a reunião foi realizada ou cancelada."
    limite = 2000 if situacao == "realizada" else 500
    if len((texto or "").strip()) > limite:
        return f"O texto pode ter até {limite} caracteres."
    return None
