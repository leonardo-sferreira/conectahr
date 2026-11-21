"""Feriados e pontos facultativos além dos nacionais da BrasilAPI (change ponto-rep-p-e-ferias-clt, tarefa 7.1).

- Páscoa (algoritmo de Meeus/Jones/Butcher) e as datas móveis: Carnaval (segunda e terça, Páscoa - 48 e - 47), Quarta-Feira
  de Cinzas (- 46), Paixão de Cristo (- 2) e Corpus Christi (+ 60).
- Pontos facultativos federais de 2026: Portaria MGI nº 11.460, de 29/12/2025 (DOU de 30/12/2025, seção 1, p. 59),
  https://www.in.gov.br/web/dou/-/portaria-mgi-n-11.460-de-29-de-dezembro-de-2025-678388627. A portaria de 2027 sai em
  dezembro de 2026; até lá, 2027 fica só com os de SP.
- Estado de São Paulo: 9 de julho, data magna (Lei estadual nº 9.497, de 05/03/1997).
- Cidade de São Paulo: 25 de janeiro (aniversário) e Corpus Christi (Lei municipal nº 14.485/2007, art. 10, citada no
  calendário oficial da Prefeitura para 2026).

Uso (na raiz do repositório):
    python tools/feriados.py            # confere as datas (Páscoa, Corpus Christi e a portaria de 2026)
    python tools/feriados.py --json     # a lista para a carga (ConectaHR/semear_feriados)
"""

import json
import sys
from datetime import date, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def pascoa(ano: int) -> date:
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def moveis(ano: int) -> dict:
    p = pascoa(ano)
    return {"carnaval_segunda": p - timedelta(days=48), "carnaval_terca": p - timedelta(days=47), "cinzas": p - timedelta(days=46),
            "paixao": p - timedelta(days=2), "pascoa": p, "corpus_christi": p + timedelta(days=60)}


# Portaria MGI nº 11.460/2025, art. 1º: só os pontos facultativos (os feriados nacionais vêm da BrasilAPI).
FACULTATIVOS_FEDERAIS = {
    2026: [
        ("2026-02-16", "Carnaval", None),
        ("2026-02-17", "Carnaval", None),
        ("2026-02-18", "Quarta-Feira de Cinzas", "até as 14h"),
        ("2026-04-20", "Ponto facultativo (véspera de Tiradentes)", None),
        ("2026-06-04", "Corpus Christi", None),
        ("2026-06-05", "Ponto facultativo (após Corpus Christi)", None),
        ("2026-10-28", "Dia do Servidor Público federal", None),
        ("2026-12-24", "Véspera do Natal", "após as 13h"),
        ("2026-12-31", "Véspera do Ano Novo", "após as 13h"),
    ],
}


def lista(ano: int) -> list[dict]:
    m = moveis(ano)
    itens = [{"data": d, "nome": n, "tipo": "ponto_facultativo", "abrangencia": "nacional", "observacao": o, "estado": None, "municipio": None}
             for d, n, o in FACULTATIVOS_FEDERAIS.get(ano, [])]
    itens += [
        {"data": f"{ano}-07-09", "nome": "Revolução Constitucionalista (data magna de SP)", "tipo": "feriado", "abrangencia": "estadual",
         "observacao": None, "estado": "SP", "municipio": None},
        {"data": f"{ano}-01-25", "nome": "Aniversário da cidade de São Paulo", "tipo": "feriado", "abrangencia": "municipal",
         "observacao": None, "estado": "SP", "municipio": "São Paulo"},
        {"data": m["corpus_christi"].isoformat(), "nome": "Corpus Christi", "tipo": "feriado", "abrangencia": "municipal",
         "observacao": None, "estado": "SP", "municipio": "São Paulo"},
    ]
    return sorted(itens, key=lambda x: (x["data"], x["abrangencia"]))


def conferir() -> int:
    falhas = []

    def ok(cond, descricao):
        print("  ok:" if cond else "  FALHA:", descricao)
        if not cond:
            falhas.append(descricao)

    ok(pascoa(2026) == date(2026, 4, 5) and pascoa(2027) == date(2027, 3, 28), "Páscoa: 05/04/2026 e 28/03/2027")
    ok(moveis(2026)["corpus_christi"] == date(2026, 6, 4) and moveis(2027)["corpus_christi"] == date(2027, 5, 27), "Corpus Christi: 04/06/2026 e 27/05/2027")
    m = moveis(2026)
    portaria = {d for d, _, _ in FACULTATIVOS_FEDERAIS[2026]}
    ok({m["carnaval_segunda"].isoformat(), m["carnaval_terca"].isoformat(), m["cinzas"].isoformat(), m["corpus_christi"].isoformat()} <= portaria,
       "as datas móveis batem com a portaria de 2026 (Carnaval, Cinzas e Corpus Christi)")
    ok(moveis(2026)["paixao"] == date(2026, 4, 3), "Paixão de Cristo: 03/04/2026 (feriado nacional da portaria)")
    ok(len(FACULTATIVOS_FEDERAIS[2026]) == 9, "9 pontos facultativos na portaria de 2026")
    ok(len(lista(2026)) == 12 and len(lista(2027)) == 3, "carga: 12 itens em 2026 e 3 em 2027 (a portaria de 2027 ainda não saiu)")
    print(f"\n{6 - len(falhas)}/6 verificações ok.")
    return 1 if falhas else 0


if __name__ == "__main__":
    if "--json" in sys.argv:
        print(json.dumps(lista(2026) + lista(2027), ensure_ascii=False))
    else:
        sys.exit(conferir())
