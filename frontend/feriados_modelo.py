"""
Regras de apresentação da aba "Feriados" da Estrutura da empresa (Figma 468:838; change ponto-rep-p-e-ferias-clt,
tarefas 7.1 e 7.3). Funções puras, sem Streamlit.

Os nacionais vêm da BrasilAPI (`feriados/importar`, RH e Admin): o backend grava só as datas que ainda não têm
feriado nacional, e Carnaval e Corpus Christi entram como ponto facultativo. Estaduais e municipais são do RH.
"""

from datetime import date

TIPOS = {"feriado": ("Feriado", "err"), "ponto_facultativo": ("Ponto facultativo", "amb")}
NOTA = ("Os feriados nacionais vêm da BrasilAPI (brasilapi.com.br), uma API pública: só o ano vai na consulta. Importar de "
        "novo não duplica. Carnaval e Corpus Christi entram como ponto facultativo. Feriado e ponto facultativo contam como "
        "dia sem expediente no ponto.")


def _dia(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def abrangencia(f: dict) -> str:
    """"Nacional", "Estadual — SP" ou "Municipal — São Paulo/SP"."""
    tipo = f.get("abrangencia") or "nacional"
    if tipo == "estadual":
        return f"Estadual — {f.get('estado')}" if f.get("estado") else "Estadual"
    if tipo == "municipal":
        lugar = "/".join(p for p in (f.get("municipio"), f.get("estado")) if p)
        return f"Municipal — {lugar}" if lugar else "Municipal"
    return "Nacional"


def linhas_feriados(feriados: list[dict], ano: int) -> list[dict]:
    """Os feriados ativos do ano em ordem de data: {'data', 'nome', 'tipo', 'tom', 'abrangencia'}."""
    linhas = []
    for f in feriados:
        d = _dia(f.get("data"))
        if not d or d.year != ano or not f.get("ativo", True):
            continue
        tipo, tom = TIPOS.get(f.get("tipo"), TIPOS["feriado"])
        linhas.append({"_d": d, "data": f"{d:%d/%m}", "nome": f.get("nome") or "—", "tipo": tipo, "tom": tom, "abrangencia": abrangencia(f)})
    linhas.sort(key=lambda l: (l["_d"], l["nome"]))
    for l in linhas:
        l.pop("_d")
    return linhas


def anos_feriados(hoje: date) -> list[int]:
    """O ano passado, o atual e o seguinte."""
    return [hoje.year - 1, hoje.year, hoje.year + 1]


def mensagem_importacao(resposta: dict) -> str:
    importados, ja = int(resposta.get("importados") or 0), int(resposta.get("ja_existiam") or 0)
    if not importados:
        return f"Nenhum feriado novo em {resposta.get('ano')}: os {ja} nacionais já estavam cadastrados."
    plural = importados != 1
    return f"{importados} {'feriados nacionais importados' if plural else 'feriado nacional importado'} para {resposta.get('ano')}" + (
        f"; {ja} já estava{'m' if ja != 1 else ''} cadastrado{'s' if ja != 1 else ''}." if ja else ".")
