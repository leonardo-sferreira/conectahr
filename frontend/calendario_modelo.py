"""
Regras da tela "Calendário" (Figma 233:2394; tarefa 56 da change concluir-frontend-streamlit). Funções puras, sem
Streamlit.

Os dados vêm de `calendario` GET: feriados ativos (todos veem) e férias aprovadas com nome e período. Colaborador e
Gestor recebem só as férias do próprio departamento; RH e Admin, as de todos. As ausências não aparecem: o tipo de uma
ausência pode revelar dado de saúde.
"""

import calendar
from datetime import date, datetime, timezone

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
SEMANA = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]


def _dia(valor) -> date | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(valor / 1000, tz=timezone.utc).date()
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _feriados(feriados: list[dict]) -> list[tuple[date, str, str]]:
    saida = []
    for f in feriados or []:
        d = _dia(f.get("data"))
        if d and f.get("ativo", True):
            facultativo = f.get("tipo") == "ponto_facultativo"
            saida.append((d, f.get("nome") or ("Ponto facultativo" if facultativo else "Feriado"), "facultativo" if facultativo else "feriado"))
    return saida


def _ferias(ferias: list[dict]) -> list[tuple[date, date, str]]:
    saida = []
    for f in ferias or []:
        inicio, fim = _dia(f.get("data_inicio")), _dia(f.get("data_fim"))
        if inicio and fim and f.get("status", "Aprovada") in ("Aprovada", "Concluida"):
            saida.append((inicio, fim, f.get("nome") or "Colega"))
    return saida


def semanas(ano: int, mes: int, feriados: list[dict], ferias: list[dict], hoje: date, mostrar_ferias: bool = True) -> list[list[dict | None]]:
    """Semanas de domingo a sábado; None fora do mês. Cada dia: {dia, fds, hoje, marcas: [(texto, tipo)]}."""
    marcas: dict[date, list] = {}
    for d, nome, tipo in _feriados(feriados):
        marcas.setdefault(d, []).append((nome, tipo))
    periodos = _ferias(ferias) if mostrar_ferias else []
    saida = []
    for semana in calendar.Calendar(firstweekday=6).monthdatescalendar(ano, mes):
        linha = []
        for d in semana:
            if d.month != mes:
                linha.append(None)
                continue
            do_dia = list(marcas.get(d, []))
            do_dia += [(f"Férias — {nome}", "ferias") for i, f, nome in periodos if i <= d <= f]
            linha.append({"dia": d.day, "fds": d.weekday() >= 5, "hoje": d == hoje, "marcas": do_dia})
        saida.append(linha)
    return saida


def _curto(d: date) -> str:
    return f"{d:%d/%m}"


def proximos(feriados: list[dict], ferias: list[dict], hoje: date, quantos: int = 6, mostrar_ferias: bool = True) -> list[dict]:
    """Os próximos eventos a partir de hoje (férias em andamento contam): [{titulo, quando, tipo}]."""
    eventos = [(d, {"titulo": f"{'Ponto facultativo' if tipo == 'facultativo' else 'Feriado'} — {nome}", "quando": _curto(d), "tipo": tipo})
               for d, nome, tipo in _feriados(feriados) if d >= hoje]
    if mostrar_ferias:
        eventos += [(max(i, hoje), {"titulo": f"Férias — {nome}", "quando": f"{i:%d} a {_curto(f)}" if i.month == f.month else f"{_curto(i)} a {_curto(f)}",
                                    "tipo": "ferias"}) for i, f, nome in _ferias(ferias) if f >= hoje]
    eventos.sort(key=lambda e: e[0])
    return [e for _, e in eventos[:quantos]]


def mes_vizinho(ano: int, mes: int, passo: int) -> tuple[int, int]:
    indice = ano * 12 + (mes - 1) + passo
    return indice // 12, indice % 12 + 1


def nota_escopo(perfil: str) -> str:
    if str(perfil).upper() in ("RH", "ADMIN"):
        return "Você vê as férias aprovadas de toda a empresa."
    return "Você vê só as férias aprovadas do seu departamento."
