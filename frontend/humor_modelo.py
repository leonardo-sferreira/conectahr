"""
Regras do termômetro de humor (Figma, seção 23, 563:850; change termometro-de-humor). Funções puras, sem Streamlit.

A pergunta volta a cada 10 dias: o ciclo 0 vai de 21/10/2026 a 30/10/2026, e o ciclo n começa 10 × n dias depois (o
backend calcula o ciclo de hoje; aqui só as datas para mostrar). A nota vai de 1 (muito mal) a 5 (muito bem), e o
motivo é opcional, de uma lista fechada. O backend guarda só contagens; as médias e os percentuais saem aqui, a
partir da distribuição das 5 notas. Grupo abaixo do mínimo chega sem distribuição (None) e aparece como "—".
"""

from datetime import date, timedelta

ANCORA = date(2026, 10, 21)
CICLO_DIAS = 10
# (nota, rótulo, classe da cor) — da pior para a melhor.
OPCOES = [(1, "Muito mal", "n1"), (2, "Mal", "n2"), (3, "Mais ou menos", "n3"), (4, "Bem", "n4"), (5, "Muito bem", "n5")]
MOTIVOS = {"carga_trabalho": "Carga de trabalho", "reconhecimento": "Reconhecimento", "lideranca": "Liderança",
           "colegas": "Relacionamento com colegas", "comunicacao": "Comunicação", "estrutura": "Estrutura e ferramentas"}
# Queda a partir de 0,3 ponto sobre o ciclo anterior, ou média abaixo de 3, pede atenção.
QUEDA_ATENCAO = 0.3


def inicio_ciclo(ciclo: int) -> date:
    return ANCORA + timedelta(days=CICLO_DIAS * int(ciclo))


def fim_ciclo(ciclo: int) -> date:
    return inicio_ciclo(ciclo) + timedelta(days=CICLO_DIAS - 1)


def periodo(ciclo: int) -> str:
    return f"{inicio_ciclo(ciclo).strftime('%d/%m')} a {fim_ciclo(ciclo).strftime('%d/%m')}"


def proximo(ciclo: int) -> str:
    return inicio_ciclo(int(ciclo) + 1).strftime("%d/%m")


def num_br(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def media(notas: list | None) -> float | None:
    if not notas:
        return None
    total = sum(notas)
    return sum((i + 1) * q for i, q in enumerate(notas)) / total if total else None


def pct(notas: list | None, quais: tuple[int, ...]) -> int | None:
    if not notas or not sum(notas):
        return None
    return round(100 * sum(notas[n - 1] for n in quais) / sum(notas))


def validar_resposta(nota, motivo: str | None) -> str | None:
    if nota not in (1, 2, 3, 4, 5):
        return "Escolha como você está, de muito mal a muito bem."
    if motivo and motivo not in MOTIVOS:
        return "Motivo inválido."
    return None


def situacao_departamento(atual: float | None, anterior: float | None) -> tuple[str, str, str]:
    """(variação legível, selo, tom do selo) de um setor no ciclo atual."""
    if atual is None:
        return "", "Menos de 5 respostas", "neu"
    variacao = "" if anterior is None else f"{'+' if atual - anterior >= 0 else '−'}{num_br(abs(atual - anterior))} vs. ciclo anterior"
    if atual < 3 or (anterior is not None and atual - anterior <= -QUEDA_ATENCAO):
        return variacao, "Atenção", "err"
    if anterior is not None and atual - anterior >= QUEDA_ATENCAO:
        return variacao, "Melhorou", "ok"
    return variacao, "Estável", "ok"


def resumo(dados: dict) -> dict:
    """Tudo o que a tela de resultados mostra, a partir de `humor/resultados`."""
    ciclo = int(dados.get("ciclo") or 0)
    minimo = int(dados.get("minimo") or 5)
    ciclos = dados.get("ciclos") or []
    atual = next((c for c in ciclos if c.get("ciclo") == ciclo), {"respostas": 0, "notas": None})
    m = media(atual.get("notas"))
    part = dados.get("participacao") or {}
    resp, ativos = int(part.get("respondentes") or 0), int(part.get("ativos") or 0)
    bem, mal = pct(atual.get("notas"), (4, 5)), pct(atual.get("notas"), (1, 2))
    indicadores = [
        ("Humor médio (ciclo atual)", f"{num_br(m)} de 5" if m is not None else "—", ""),
        ("Bem ou muito bem", f"{bem}%" if bem is not None else "—", "verde" if bem is not None else ""),
        ("Mal ou muito mal", f"{mal}%" if mal is not None else "—", "negativo" if mal else ""),
        ("Participação", f"{resp} de {ativos} ({round(100 * resp / ativos)}%)" if ativos else "—", ""),
    ]
    barras = []
    for c in ciclos:
        mc = media(c.get("notas"))
        barras.append({"rotulo": inicio_ciclo(c["ciclo"]).strftime("%d/%m"), "media": mc, "texto": num_br(mc) if mc is not None else "—",
                       "atual": c.get("ciclo") == ciclo, "altura": round(mc * 20) if mc is not None else 6})
    departamentos = []
    for d in dados.get("departamentos") or []:
        a, p = d.get("atual") or {}, d.get("anterior") or {}
        if not a.get("respostas") and not p.get("respostas"):
            continue
        ma, mp = media(a.get("notas")), media(p.get("notas"))
        variacao, selo, tom = situacao_departamento(ma, mp)
        departamentos.append({"nome": d.get("nome") or "—", "media": num_br(ma) if ma is not None else "—", "variacao": variacao, "selo": selo,
                              "tom": tom, "ordem": ma if ma is not None else 99})
    motivos = None
    if dados.get("motivos") is not None:
        brutos = dados.get("motivos") or {}
        maior = max([int(v or 0) for v in brutos.values()] or [0])
        motivos = sorted(({"nome": MOTIVOS.get(k, k), "quantidade": int(v or 0), "pct": round(100 * int(v or 0) / maior) if maior else 0}
                          for k, v in brutos.items() if int(v or 0) > 0), key=lambda x: (-x["quantidade"], x["nome"]))
    return {"ciclo": ciclo, "periodo": periodo(ciclo), "proximo": proximo(ciclo), "minimo": minimo, "indicadores": indicadores, "barras": barras,
            "departamentos": sorted(departamentos, key=lambda x: (x["ordem"], x["nome"])), "motivos": motivos,
            "sem_dados": atual.get("notas") is None}
