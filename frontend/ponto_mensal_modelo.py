"""
Espelho de ponto mensal do colaborador (tarefa 78 da change concluir-frontend-streamlit). Funções puras, sem
Streamlit. O fluxo completo, caso a caso, está em `docs/fluxos/ponto-mensal.md`.

Cada dia do mês, da admissão até hoje, recebe exatamente uma situação, nesta ordem de precedência:
  1. tem registro de ponto        -> as marcações e a situação do registro; "corrigir" o que não estiver em análise
  2. é hoje e não tem registro    -> "Sem marcação hoje" (marca-se pelo "Marcar agora")
  3. férias aprovadas             -> "Férias", sem correção
  4. ausência (não recusada)      -> "Justificado" ou "Ausência em análise", sem correção
  5. feriado nacional             -> "Feriado", com "corrigir dia" (quem trabalhou pede a correção)
  6. sábado ou domingo            -> "Folga", com "corrigir dia"
  7. dia útil passado sem nada    -> "Sem registro", com "corrigir dia" ou "registrar ausência"
Dias futuros e anteriores à admissão não aparecem.
"""

import calendar
import csv
import io
from datetime import date

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


def meses_disponiveis(admissao, registros: list[dict], hoje: date, limite: int = 24) -> list[tuple[int, int]]:
    """Do mês atual para trás, até o mês da admissão (ou do primeiro registro), no máximo `limite` meses."""
    inicio = _dia(admissao) or min((d for d in (_dia(r.get("data")) for r in registros) if d), default=hoje)
    ano, mes, saida = hoje.year, hoje.month, []
    while (ano, mes) >= (inicio.year, inicio.month) and len(saida) < limite:
        saida.append((ano, mes))
        ano, mes = (ano, mes - 1) if mes > 1 else (ano - 1, 12)
    return saida or [(hoje.year, hoje.month)]


def _cobre(item: dict, d: date) -> bool:
    a, b = _dia(item.get("data_inicio")), _dia(item.get("data_fim")) or _dia(item.get("data_inicio"))
    return bool(a and b and a <= d <= b)


def espelho_do_mes(registros: list[dict], ausencias: list[dict], correcoes: list[dict], ferias: list[dict], feriados: list[dict],
                   ano: int, mes: int, hoje: date, admissao=None) -> list[dict]:
    """Uma linha por dia: {'dia', 'data', 'marcas', 'trabalhado', 'horas', 'status', 'tom', 'registro_id', 'acao', 'nota',
    'pendentes'}. `acao`: 'corrigir' (há registro), 'corrigir_dia' (dia passado sem registro) ou None."""
    inicio_valido = _dia(admissao)
    por_dia = {_dia(r.get("data")): r for r in registros if _dia(r.get("data"))}
    feriados_nac = {_dia(f.get("data")): f.get("nome") or "Feriado" for f in feriados
                    if f.get("ativo", True) and (f.get("abrangencia") or "nacional") == "nacional" and _dia(f.get("data"))}
    ferias_ok = [f for f in ferias if f.get("status") in ("Aprovada", "Concluida")]
    aus_validas = [a for a in ausencias if a.get("status") != "Rejeitada"]
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
            linhas.append(dict(base, status="AUSÊNCIA EM ANÁLISE" if pendente else "JUSTIFICADO", tom="amb" if pendente else "azul",
                               trabalhado=TIPOS_AUSENCIA.get(aus.get("tipo"), "Ausência")))
            continue
        if d in feriados_nac:
            linhas.append(dict(base, status="FERIADO", tom="neu", nota=f"{feriados_nac[d]}. Trabalhou? Peça a correção.", acao="corrigir_dia"))
            continue
        if d.weekday() >= 5:
            linhas.append(dict(base, status="FOLGA", tom="neu", acao="corrigir_dia"))
            continue
        linhas.append(dict(base, status="SEM REGISTRO", tom="err", acao="corrigir_dia",
                           nota="Esqueceu de marcar? Peça a correção. Faltou? Registre a ausência."))
    return linhas


def resumo_do_mes(linhas: list[dict]) -> dict:
    horas = sum(l["horas"] for l in linhas)
    return {
        "horas": horas_trabalhadas(horas) if horas else "0h00",
        "dias_trabalhados": sum(1 for l in linhas if l["registro_id"] and any(m != "—" for m in l["marcas"])),
        "sem_registro": sum(1 for l in linhas if l["status"] in ("SEM REGISTRO", "INCOMPLETO")),
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

