"""
Espelho de ponto mensal do colaborador (tarefa 78 da change concluir-frontend-streamlit). Funções puras, sem
Streamlit. O fluxo completo, caso a caso, está em `docs/fluxos/ponto-mensal.md`.

Cada dia do mês, do primeiro ponto registrado (ou da admissão) até hoje, recebe exatamente uma situação, nesta
ordem de precedência:
  1. tem registro de ponto        -> as marcações e a situação do registro; "corrigir" o que não estiver em análise
  2. é hoje e não tem registro    -> "Sem marcação hoje" (marca-se pelo "Marcar agora")
  3. férias aprovadas             -> "Férias", sem correção
  4. ausência aprovada            -> pelo tipo: "Atestado", "Falta justificada", "Licença", "Afastamento"; sem correção
     ausência em análise          -> "Ausência em análise", sem correção
  5. ausência recusada            -> "Falta injustificada", com "corrigir dia"
  6. feriado nacional             -> "Feriado", com "corrigir dia" (quem trabalhou pede a correção)
  7. sábado ou domingo            -> "Folga", com "corrigir dia"
  8. dia útil passado sem nada    -> "Sem registro" no mês corrente; "Falta injustificada" nos meses encerrados;
                                     com "corrigir dia" ou "registrar ausência"
Dias futuros não aparecem. Os meses vão do primeiro ponto registrado até hoje, sem limite.
"""

import calendar
import csv
import io
from datetime import date, timedelta

from onboarding_modelo import data_br
from pagamento_modelo import MESES
from ponto_modelo import MARCACOES, ROTULO_CAMPO, TIPOS_AUSENCIA, hora, horas_trabalhadas

_DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
_STATUS_REGISTRO = {"Completo": ("COMPLETO", "ok"), "Ajustado": ("AJUSTADO", "amb"), "Incompleto": ("INCOMPLETO", "err"), "Aberto": ("EM ANDAMENTO", "amb")}
CAMPOS = [c for c, _ in MARCACOES]


def _dia(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def rotulo_mes(ano: int, mes: int) -> str:
    return f"{MESES[mes - 1]}/{ano}"


_ROTULO_AUSENCIA = {"Atestado": "ATESTADO", "Falta": "FALTA JUSTIFICADA", "Licenca": "LICENÇA", "Afastamento": "AFASTAMENTO"}


def primeiro_dia(admissao, registros: list[dict]) -> date | None:
    """O primeiro ponto registrado; sem registro, a admissão. Se houver registro antes da admissão, vale o registro."""
    datas = [d for d in (_dia(r.get("data")) for r in registros) if d]
    candidatos = [d for d in (min(datas) if datas else None, _dia(admissao)) if d]
    return min(candidatos) if candidatos else None


def meses_disponiveis(admissao, registros: list[dict], hoje: date) -> list[tuple[int, int]]:
    """Do mês atual para trás, até o mês do primeiro ponto registrado (ou da admissão), sem limite."""
    inicio = primeiro_dia(admissao, registros) or hoje
    ano, mes, saida = hoje.year, hoje.month, []
    while (ano, mes) >= (inicio.year, inicio.month):
        saida.append((ano, mes))
        ano, mes = (ano, mes - 1) if mes > 1 else (ano - 1, 12)
    return saida or [(hoje.year, hoje.month)]


def anos_disponiveis(meses: list[tuple[int, int]]) -> list[int]:
    return sorted({a for a, _ in meses}, reverse=True)


def meses_do_ano(meses: list[tuple[int, int]], ano: int) -> list[int]:
    return [m for a, m in meses if a == ano]


def _cobre(item: dict, d: date) -> bool:
    a, b = _dia(item.get("data_inicio")), _dia(item.get("data_fim")) or _dia(item.get("data_inicio"))
    return bool(a and b and a <= d <= b)


def espelho_do_mes(registros: list[dict], ausencias: list[dict], correcoes: list[dict], ferias: list[dict], feriados: list[dict],
                   ano: int, mes: int, hoje: date, admissao=None, inicio: date | None = None, prazo_dias: int | None = None) -> list[dict]:
    """Uma linha por dia: {'dia', 'data', 'marcas', 'trabalhado', 'horas', 'status', 'tom', 'registro_id', 'acao', 'nota',
    'pendentes'}. `acao`: 'corrigir' (há registro), 'corrigir_dia' (dia passado sem registro) ou None."""
    # `inicio`: quando os registros são só do mês (folha da equipe), a data do primeiro ponto vem de fora.
    # `prazo_dias` (tarefa 79): prazo do RH para o colaborador pedir correção; o backend recusa fora dele. Vazio = sem limite.
    inicio_valido = inicio or primeiro_dia(admissao, registros)
    por_dia = {_dia(r.get("data")): r for r in registros if _dia(r.get("data"))}
    feriados_nac = {_dia(f.get("data")): f.get("nome") or "Feriado" for f in feriados
                    if f.get("ativo", True) and (f.get("abrangencia") or "nacional") == "nacional" and _dia(f.get("data"))}
    ferias_ok = [f for f in ferias if f.get("status") in ("Aprovada", "Concluida")]
    aus_validas = [a for a in ausencias if a.get("status") != "Rejeitada"]
    aus_recusadas = [a for a in ausencias if a.get("status") == "Rejeitada"]
    mes_encerrado = (ano, mes) < (hoje.year, hoje.month)
    linhas = []
    for n in range(1, calendar.monthrange(ano, mes)[1] + 1):
        d = date(ano, mes, n)
        if d > hoje or (inicio_valido and d < inicio_valido):
            continue
        rotulo = f"{_DIAS[d.weekday()]}, {d:%d/%m}"
        base = {"dia": rotulo, "data": d, "marcas": ["—"] * 4, "trabalhado": "—", "horas": 0.0, "registro_id": None, "acao": None, "nota": "", "pendentes": []}
        reg = por_dia.get(d)
        if reg:
            cor = [c for c in correcoes if c.get("registro_ponto_id") == reg.get("id")]
            pendentes = [c.get("campo") for c in cor if c.get("status") == "pendente"]
            recusadas = [c for c in cor if c.get("status") == "rejeitada"]
            status, tom = _STATUS_REGISTRO.get(reg.get("status"), (str(reg.get("status") or "—").upper(), "neu"))
            if reg.get("status") == "Aberto" and d < hoje:
                status, tom = "INCOMPLETO", "err"
            nota = ""
            if pendentes:
                nota = "Em análise: " + ", ".join(ROTULO_CAMPO.get(c, c) for c in CAMPOS if c in pendentes)
            elif recusadas:
                ultima = max(recusadas, key=lambda c: str(c.get("data_decisao") or ""))
                nota = f"Correção recusada ({ROTULO_CAMPO.get(ultima.get('campo'), 'marcação')}): {ultima.get('motivo_decisao') or 'sem motivo informado'}"
            linhas.append(dict(base, marcas=[hora(reg.get(c)) or "—" for c in CAMPOS], trabalhado=horas_trabalhadas(reg.get("horas_trabalhadas")),
                               horas=float(reg.get("horas_trabalhadas") or 0), status=status, tom=tom, registro_id=reg.get("id"),
                               acao="corrigir" if len(pendentes) < 4 else None, nota=nota, pendentes=pendentes))
            continue
        if d == hoje:
            linhas.append(dict(base, status="SEM MARCAÇÃO HOJE", tom="neu", nota='Use "Marcar agora" no topo da tela.'))
            continue
        fer = next((f for f in ferias_ok if _cobre(f, d)), None)
        if fer:
            linhas.append(dict(base, status="FÉRIAS", tom="azul", trabalhado="Férias"))
            continue
        aus = next((a for a in aus_validas if _cobre(a, d)), None)
        if aus:
            pendente = aus.get("status") == "Pendente"
            status = "AUSÊNCIA EM ANÁLISE" if pendente else _ROTULO_AUSENCIA.get(aus.get("tipo"), "JUSTIFICADO")
            linhas.append(dict(base, status=status, tom="amb" if pendente else "azul", trabalhado=TIPOS_AUSENCIA.get(aus.get("tipo"), "Ausência")))
            continue
        recusada = next((a for a in aus_recusadas if _cobre(a, d)), None)
        if recusada:
            linhas.append(dict(base, status="FALTA INJUSTIFICADA", tom="err", acao="corrigir_dia",
                               nota=f"{TIPOS_AUSENCIA.get(recusada.get('tipo'), 'Ausência')} recusada pelo RH. Se trabalhou, peça a correção."))
            continue
        if d in feriados_nac:
            linhas.append(dict(base, status="FERIADO", tom="neu", nota=f"{feriados_nac[d]}. Trabalhou? Peça a correção.", acao="corrigir_dia"))
            continue
        if d.weekday() >= 5:
            linhas.append(dict(base, status="FOLGA", tom="neu", acao="corrigir_dia"))
            continue
        if mes_encerrado:
            linhas.append(dict(base, status="FALTA INJUSTIFICADA", tom="err", acao="corrigir_dia",
                               nota="Mês encerrado sem marcação nem ausência. Ainda dá para pedir a correção ou registrar a ausência."))
        else:
            linhas.append(dict(base, status="SEM REGISTRO", tom="err", acao="corrigir_dia",
                               nota="Esqueceu de marcar? Peça a correção. Faltou? Registre a ausência."))
    return aplicar_prazo(linhas, hoje, prazo_dias)


NOTA_PRAZO = "Fora do prazo para pedir correção."


def limite_prazo(hoje: date, prazo_dias: int | None) -> date | None:
    """Primeiro dia que ainda aceita pedido de correção (o backend compara a data com hoje − prazo)."""
    if not prazo_dias or prazo_dias <= 0:
        return None
    return hoje - timedelta(days=int(prazo_dias))


def aplicar_prazo(linhas: list[dict], hoje: date, prazo_dias: int | None) -> list[dict]:
    """Tira a ação de corrigir dos dias fora do prazo e explica o porquê. Pedidos já em análise continuam visíveis."""
    limite = limite_prazo(hoje, prazo_dias)
    if limite is None:
        return linhas
    for l in linhas:  # o aviso completo (gestor ou RH ajustam) fica acima da tabela: aviso_prazo()
        if l["acao"] and l["data"] < limite:
            l["acao"] = None
            l["nota"] = f'{l["nota"]} · {NOTA_PRAZO}' if l["nota"] and not l["nota"].startswith(("Esqueceu", "Mês encerrado")) else NOTA_PRAZO
    return linhas


def aviso_prazo(linhas: list[dict], hoje: date, prazo_dias: int | None) -> str:
    """Aviso acima do espelho quando algum dia do mês já passou do prazo; vazio quando não há."""
    limite = limite_prazo(hoje, prazo_dias)
    if limite is None or not any(l["data"] < limite for l in linhas):
        return ""
    return (f"Dias antes de {data_br(limite.isoformat())} passaram do prazo de {texto_prazo(prazo_dias)} para pedir correção. "
            "Se algo estiver errado, fale com o seu gestor ou com o RH, que podem ajustar.")


def texto_prazo(prazo_dias: int | None) -> str:
    if not prazo_dias:
        return "Sem limite"
    return f"{prazo_dias} dia{'s' if prazo_dias != 1 else ''}"


def resumo_do_mes(linhas: list[dict]) -> dict:
    horas = sum(l["horas"] for l in linhas)
    return {
        "horas": horas_trabalhadas(horas) if horas else "0h00",
        "dias_trabalhados": sum(1 for l in linhas if l["registro_id"] and any(m != "—" for m in l["marcas"])),
        "sem_registro": sum(1 for l in linhas if l["status"] in ("SEM REGISTRO", "INCOMPLETO")),
        "faltas_injustificadas": sum(1 for l in linhas if l["status"] == "FALTA INJUSTIFICADA"),
        "atestados": sum(1 for l in linhas if l["status"] == "ATESTADO"),
        "em_analise": sum(len(l["pendentes"]) for l in linhas),
    }


def campos_livres(linha: dict) -> list[str]:
    """As marcações que ainda podem ser corrigidas no dia (as que já estão em análise ficam fora)."""
    return [c for c in CAMPOS if c not in linha.get("pendentes", [])]


def csv_do_mes(linhas: list[dict]) -> bytes:
    """O espelho do mês em CSV (separador ';', com BOM, para abrir direto em planilha)."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["Dia", "Data", *[r for _, r in MARCACOES], "Trabalhado", "Situação", "Observação"])
    for l in linhas:
        escritor.writerow([l["dia"].split(",")[0], data_br(l["data"].isoformat()), *l["marcas"], l["trabalhado"], l["status"], l["nota"]])
    return saida.getvalue().encode("utf-8-sig")

