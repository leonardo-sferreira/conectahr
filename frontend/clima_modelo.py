"""
Regras das telas de pesquisa de clima (Figma "Pesquisa de clima" 225:4668; change pesquisa-clima-e-avaliacao-360).
Funções puras, sem Streamlit.

A resposta é anônima: o backend só soma a nota num contador por pergunta, departamento e nota, e o comentário fica
sem pessoa, departamento nem data. O RH só vê os resultados depois do encerramento e só dos grupos com o mínimo de
respostas da pesquisa.
"""

from datetime import date

from onboarding_modelo import data_br

ESCALAS = {
    "concordancia": {"notas": list(range(1, 6)), "min": "Discordo totalmente", "max": "Concordo totalmente", "nome": "Concordância (1 a 5)"},
    "nps": {"notas": list(range(0, 11)), "min": "Nada provável", "max": "Muito provável", "nome": "Recomendação (0 a 10)"},
}
PERGUNTA_NPS = "De 0 a 10, quanto você recomendaria a empresa como lugar para trabalhar?"
PERGUNTAS_SUGERIDAS = [
    "Eu me sinto reconhecido pelo meu trabalho.",
    "Tenho as ferramentas e os recursos de que preciso para fazer bem o meu trabalho.",
    "Meu gestor me dá retorno claro sobre o meu desempenho.",
    "Consigo equilibrar o trabalho e a vida pessoal.",
    "Vejo oportunidades de crescer na empresa.",
]
_SITUACAO_RH = {"agendada": ("Agendada", "neu"), "aberta": ("Aberta", "azul"), "encerrada": ("Encerrada", "ok")}


def _data(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def escala(pergunta: dict) -> dict:
    return ESCALAS.get(pergunta.get("escala") or "concordancia", ESCALAS["concordancia"])


# ---------------------------------------------------------------------------
# A pessoa
# ---------------------------------------------------------------------------
def situacao_minha(p: dict) -> tuple[str, str]:
    """(selo, tom) no cartão "Pesquisas" do Figma."""
    if p.get("respondida"):
        return "Respondida", "ok"
    if p.get("aberta"):
        return "Em andamento", "amb"
    return "Encerrada", "neu"


def prazo_minha(p: dict) -> str:
    fim = data_br(p.get("data_fim"))
    return f"Aberta até {fim}" if p.get("aberta") else f"Encerrada em {fim}"


def a_responder(pesquisas: list[dict]) -> list[dict]:
    """Abertas, ainda não respondidas e com perguntas a responder."""
    return [p for p in pesquisas if p.get("aberta") and not p.get("respondida") and p.get("perguntas")]


def validar_respostas(perguntas: list[dict], notas: dict, comentario: str = "") -> str | None:
    faltam = [i for i, p in enumerate(perguntas, start=1) if notas.get(p["id"]) is None]
    if faltam:
        return f"Responda a pergunta {faltam[0]} antes de enviar." if len(faltam) == 1 else f"Faltam {len(faltam)} perguntas (a primeira é a {faltam[0]})."
    for p in perguntas:
        if notas[p["id"]] not in escala(p)["notas"]:
            return "Há uma nota fora da escala da pergunta."
    if len((comentario or "").strip()) > 1000:
        return "O comentário pode ter no máximo 1000 caracteres."
    return None


def montar_respostas(perguntas: list[dict], notas: dict) -> list[dict]:
    return [{"pergunta_id": p["id"], "nota": int(notas[p["id"]])} for p in perguntas]


def progresso(indice: int, total: int) -> tuple[str, int]:
    """("Pergunta 3 de 10", porcentagem da barra)."""
    total = max(total, 1)
    return f"Pergunta {indice + 1} de {total}", round((indice + 1) / total * 100)


# ---------------------------------------------------------------------------
# RH
# ---------------------------------------------------------------------------
def situacao_rh(p: dict) -> tuple[str, str]:
    return _SITUACAO_RH.get(p.get("situacao"), ("—", "neu"))


def adesao(participantes: int, elegiveis: int) -> str:
    if not elegiveis:
        return "—"
    return f"{round((participantes or 0) / elegiveis * 100)}%"


ABAS_RH = {"Em andamento": ("agendada", "aberta"), "Encerradas": ("encerrada",)}


def da_aba(pesquisas: list[dict], aba: str) -> list[dict]:
    return [p for p in pesquisas if p.get("situacao") in ABAS_RH.get(aba, ())]


def subtitulo_card(p: dict) -> str:
    """"Aberta até 15/10/2026 · 10 perguntas" (Figma 249:4645)."""
    n = len(p.get("perguntas") or [])
    quando = {"agendada": f"Abre em {data_br(p.get('data_inicio'))}", "aberta": f"Aberta até {data_br(p.get('data_fim'))}"}.get(
        p.get("situacao"), f"Encerrada em {data_br(p.get('data_fim'))}")
    return f"{quando} · {n} {'pergunta' if n == 1 else 'perguntas'}"


def barras_adesao(p: dict, elegiveis: int) -> list[tuple[str, int, int, int]]:
    """[(rótulo, responderam, podem responder, %)]: a adesão geral e a de cada departamento (quem respondeu, nunca o quê)."""
    def linha(rotulo, parte, total):
        return rotulo, parte or 0, total or 0, round((parte or 0) / total * 100) if total else 0
    return [linha("Adesão geral", p.get("participantes"), elegiveis)] + [
        linha(d.get("nome") or "Sem departamento", d.get("participantes"), d.get("elegiveis")) for d in p.get("adesao_departamentos") or []]


def perguntas_do_texto(texto: str, pergunta_nps: str = "") -> list[dict]:
    """Uma pergunta de 1 a 5 por linha (sem linhas vazias) e, se preenchida, a de 0 a 10 no fim."""
    linhas = [l.strip(" -•\t") for l in (texto or "").splitlines()]
    perguntas = [{"texto": l, "escala": "concordancia"} for l in linhas if l]
    if (pergunta_nps or "").strip():
        perguntas.append({"texto": pergunta_nps.strip(), "escala": "nps"})
    return perguntas


def validar_pesquisa(titulo: str, inicio: date | None, fim: date | None, minimo: int, perguntas: list[dict], hoje: date) -> str | None:
    if len((titulo or "").strip()) < 3:
        return "Dê um título à pesquisa (pelo menos 3 caracteres)."
    if inicio is None or fim is None:
        return "Informe o início e o fim da pesquisa."
    if inicio < hoje:
        return "O início não pode ser no passado."
    if fim < inicio:
        return "O fim não pode ser antes do início."
    if minimo < 3:
        return "O mínimo de respostas por grupo precisa ser 3 ou mais, para ninguém ser identificado."
    if not perguntas:
        return "Inclua pelo menos uma pergunta."
    if len(perguntas) > 30:
        return "Use no máximo 30 perguntas."
    curtas = [i for i, p in enumerate(perguntas, start=1) if len(p["texto"]) < 5]
    if curtas:
        return f"A pergunta {curtas[0]} está curta demais (mínimo de 5 caracteres)."
    longas = [i for i, p in enumerate(perguntas, start=1) if len(p["texto"]) > 500]
    if longas:
        return f"A pergunta {longas[0]} passou de 500 caracteres."
    return None


def periodo(p: dict) -> str:
    return f"{data_br(p.get('data_inicio'))} a {data_br(p.get('data_fim'))}"


def _pct(parte: int, total: int) -> int:
    return round((parte or 0) / total * 100) if total else 0


def resumo_resultado(r: dict) -> dict:
    """Média, % favorável e desfavorável e, na escala de recomendação, o NPS (promotores − detratores)."""
    n = r.get("quantidade") or 0
    fav, desf = _pct(r.get("favoraveis"), n), _pct(r.get("desfavoraveis"), n)
    media = r.get("media")
    return {"n": n, "media": f"{float(media):.1f}".replace(".", ",") if media is not None else "—", "favoravel": fav, "desfavoravel": desf,
            "nps": fav - desf if r.get("escala") == "nps" else None}


def resumo_card(perguntas: list[dict], dados: dict) -> dict:
    """Cartão "Resultado" (Figma 249:4645): o eNPS geral, a primeira pergunta de 1 a 5 com a média e o pior tema (a menor
    média de 1 a 5). Só com os resultados gerais que o backend liberou."""
    linhas = [l for l in resultados_por_pergunta(perguntas, dados) if l["geral"]]
    nps = next((l["geral"]["nps"] for l in linhas if l["escala"] == "nps"), None)
    concordancia = [l for l in linhas if l["escala"] == "concordancia"]
    destaque = (concordancia[0]["texto"], f'{concordancia[0]["geral"]["media"]} de 5') if concordancia else None
    pior = min(concordancia, key=lambda l: float(l["geral"]["media"].replace(",", "."))) if len(concordancia) > 1 else None
    return {"enps": nps, "destaque": destaque, "pior_tema": pior["texto"] if pior else None}


def resultados_por_pergunta(perguntas: list[dict], dados: dict) -> list[dict]:
    """Cada pergunta com o geral e os departamentos que atingiram o mínimo (os outros não vêm do backend)."""
    nomes = {d.get("id"): d.get("nome") for d in dados.get("departamentos") or []}
    linhas = []
    for p in sorted(perguntas, key=lambda x: x.get("ordem") or 0):
        do_p = [r for r in dados.get("resultados") or [] if r.get("pergunta_id") == p["id"]]
        geral = next((r for r in do_p if r.get("departamento_id") is None), None)
        grupos = sorted(((nomes.get(r.get("departamento_id")) or "Sem departamento", resumo_resultado(r)) for r in do_p if r.get("departamento_id") is not None),
                        key=lambda g: g[0])
        linhas.append({"texto": p.get("texto"), "escala": p.get("escala") or "concordancia", "geral": resumo_resultado(geral) if geral else None, "grupos": grupos})
    return linhas
