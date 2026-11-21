"""
Regras da tela "Indicadores gerais" (F33, Figma 249:7492; tarefa 49 da change concluir-frontend-streamlit). Funções
puras, sem Streamlit.

Os números vêm de `indicadores` GET (RH e Admin), que reaproveita `ConectaHR/calcular_indicadores`: headcount,
turnover, absenteísmo, distribuição por departamento e horas extras do período. Quando a empresa tem menos pessoas que
o mínimo do backend, os totais vêm nulos e a tela mostra "Oculto", nunca zero. As admissões e os desligamentos por
trimestre saem de uma consulta por trimestre ao mesmo endpoint.
"""

from datetime import date, timedelta

PERIODOS = {3: "3 meses", 6: "6 meses", 12: "12 meses"}


def _menos_meses(d: date, meses: int) -> date:
    ano, mes = d.year, d.month - meses
    while mes <= 0:
        mes += 12
        ano -= 1
    return date(ano, mes, 1)


def periodo(meses: int, hoje: date) -> tuple[str, str]:
    """(início, fim) em aaaa-mm-dd: do primeiro dia de `meses - 1` meses atrás até hoje."""
    return _menos_meses(hoje, meses - 1).isoformat(), hoje.isoformat()


def trimestres(hoje: date, quantos: int = 4) -> list[tuple[str, str, str]]:
    """Os últimos `quantos` trimestres, do mais antigo ao atual (que termina hoje): [(rótulo "T4/25", início, fim)]."""
    tri = (hoje.month - 1) // 3
    saida = []
    for k in range(quantos - 1, -1, -1):
        t, ano = tri - k, hoje.year
        while t < 0:
            t += 4
            ano -= 1
        inicio = date(ano, 3 * t + 1, 1)
        fim_trimestre = (date(ano + (1 if t == 3 else 0), 1 if t == 3 else 3 * t + 4, 1)) - timedelta(days=1)
        saida.append((f"T{t + 1}/{str(ano)[2:]}", inicio.isoformat(), min(fim_trimestre, hoje).isoformat()))
    return saida


def _pct(valor) -> str:
    if valor is None:
        return "—"
    v = float(valor)
    return f"{int(v)}%" if v.is_integer() else f"{v:.1f}%".replace(".", ",")


def cartoes(ind: dict, meses: int) -> list[tuple[str, str, str]]:
    omitido = bool(ind.get("totais_omitidos"))
    ativos = (ind.get("headcount") or {}).get("ativos")
    return [
        ("Headcount", "Oculto" if omitido or ativos is None else str(ativos), ""),
        (f"Turnover ({meses} meses)", _pct((ind.get("turnover") or {}).get("percentual")), "ambar"),
        ("Absenteísmo", _pct((ind.get("absenteismo") or {}).get("percentual")), ""),
        ("eNPS", "—", "verde"),
    ]


def serie_trimestres(por_trimestre: list[tuple[str, dict]]) -> list[dict]:
    """Colunas de admissões e desligamentos, no formato de `theme.render_horas_mensais`."""
    serie = []
    for rotulo, ind in por_trimestre:
        t = ind.get("turnover") or {}
        for chave, sufixo in (("admissoes_periodo", "adm."), ("desligamentos_periodo", "desl.")):
            n = t.get(chave)
            serie.append({"rotulo": f"{rotulo} {sufixo}", "valor": n, "texto": "—" if n is None else str(n),
                          "situacao": "admissões" if sufixo == "adm." else "desligamentos"})
    return serie


def distribuicao(ind: dict, maximo: int = 4) -> list[tuple[str, int]] | None:
    """Headcount por departamento, do maior ao menor; além de `maximo - 1` departamentos, o resto vira "Outros"."""
    if ind.get("totais_omitidos"):
        return None
    linhas = sorted(((d.get("nome") or "Sem departamento", int(d.get("quantidade") or 0)) for d in ind.get("distribuicao_departamento") or []),
                    key=lambda x: -x[1])
    linhas = [l for l in linhas if l[1] > 0]
    if len(linhas) > maximo:
        linhas = linhas[:maximo - 1] + [("Outros", sum(n for _, n in linhas[maximo - 1:]))]
    return linhas


def horas_extras(ind: dict) -> str:
    h = ind.get("horas_extras_periodo")
    if h is None:
        return "—"
    h = float(h)
    return f"+{h:.0f}h" if h == int(h) else f"+{h:.1f}h".replace(".", ",")
