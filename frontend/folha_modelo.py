"""
Regras de apresentação da "Folha de ponto" do gestor e do RH (tarefa 81 da change concluir-frontend-streamlit).
Funções puras, sem Streamlit. Reaproveita o espelho mensal do colaborador (`ponto_mensal_modelo.py`): a folha de
cada pessoa é o mesmo espelho, só que com os dados que `folha_ponto/mes` devolve.

Quem pode ver e ajustar é o backend: RH e Admin, todos; os demais, a si mesmos, quem os tem como superior direto e,
de quem não tem superior, o departamento que gerenciam. Ninguém ajusta o próprio ponto: o pedido vai para o superior.
"""

import csv
import io
from datetime import date

from ponto_mensal_modelo import espelho_do_mes, meses_disponiveis, primeiro_dia, resumo_do_mes


def _da_pessoa(itens: list[dict], colaborador_id) -> list[dict]:
    return [i for i in itens if i.get("colaborador_id") == colaborador_id]


def inicio_da_pessoa(pessoa: dict) -> date | None:
    """O primeiro ponto registrado da pessoa (ou a admissão, se ela ainda não marcou ponto)."""
    registros = [{"data": pessoa["primeiro_registro"]}] if pessoa.get("primeiro_registro") else []
    return primeiro_dia(pessoa.get("data_admissao"), registros)


def meses_da_pessoa(pessoa: dict, hoje: date) -> list[tuple[int, int]]:
    registros = [{"data": pessoa["primeiro_registro"]}] if pessoa.get("primeiro_registro") else []
    return meses_disponiveis(pessoa.get("data_admissao"), registros, hoje)


def meses_da_equipe(pessoas: list[dict], hoje: date) -> list[tuple[int, int]]:
    """Do mês atual até o primeiro ponto de qualquer pessoa da lista, sem limite."""
    inicios = [d for d in (inicio_da_pessoa(p) for p in pessoas) if d]
    return meses_disponiveis(min(inicios).isoformat() if inicios else None, [], hoje)


def espelho_da_pessoa(pessoa: dict, mes_dados: dict, feriados: list[dict], ano: int, mes: int, hoje: date) -> list[dict]:
    pid = pessoa.get("id")
    return espelho_do_mes(
        _da_pessoa(mes_dados.get("registros") or [], pid), _da_pessoa(mes_dados.get("ausencias") or [], pid),
        _da_pessoa(mes_dados.get("correcoes") or [], pid), _da_pessoa(mes_dados.get("ferias") or [], pid),
        feriados, ano, mes, hoje, pessoa.get("data_admissao"), inicio=inicio_da_pessoa(pessoa),
    )


def linhas_resumo(pessoas: list[dict], mes_dados: dict, feriados: list[dict], ano: int, mes: int, hoje: date,
                  departamentos: dict, cargos: dict, departamento_id=None) -> list[dict]:
    """Uma linha por pessoa para o fechamento do mês: horas, dias com marcação, sem registro, faltas injustificadas e
    atestados. Quem ainda não tinha começado no mês aparece com "—"."""
    linhas = []
    for p in pessoas:
        if departamento_id and p.get("departamento_id") != departamento_id:
            continue
        espelho = espelho_da_pessoa(p, mes_dados, feriados, ano, mes, hoje)
        r = resumo_do_mes(espelho)
        linhas.append({
            "id": p.get("id"), "nome": p.get("nome") or "—", "e_voce": bool(p.get("e_voce")),
            "departamento": departamentos.get(p.get("departamento_id")) or "—", "cargo": cargos.get(p.get("cargo_id")) or "—",
            "horas": r["horas"] if espelho else "—", "dias": r["dias_trabalhados"], "sem_registro": r["sem_registro"],
            "faltas": r["faltas_injustificadas"], "atestados": r["atestados"], "tem_dias": bool(espelho),
        })
    # Quem tem falta injustificada ou dia sem registro primeiro: é o que o RH precisa olhar no fechamento.
    linhas.sort(key=lambda l: (-(l["faltas"] + l["sem_registro"]), l["nome"].casefold()))
    return linhas


def pendentes_da_pessoa(mes_dados: dict) -> list[dict]:
    return [c for c in mes_dados.get("correcoes") or [] if c.get("status") == "pendente"]


def csv_resumo(linhas: list[dict], ano: int, mes: int) -> bytes:
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["Competência", "Pessoa", "Departamento", "Cargo", "Horas", "Dias com marcação", "Sem registro ou incompletos", "Faltas injustificadas", "Atestados"])
    for l in linhas:
        escritor.writerow([f"{mes:02d}/{ano}", l["nome"], l["departamento"], l["cargo"], l["horas"], l["dias"], l["sem_registro"], l["faltas"], l["atestados"]])
    return saida.getvalue().encode("utf-8-sig")
