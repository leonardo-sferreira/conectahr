"""
Regras de apresentação de "Benefícios" (tarefa 82 da change concluir-frontend-streamlit). Funções puras, sem
Streamlit. A conferir com o Figma, que estava fora do ar quando a tela foi feita.

O RH cadastra o catálogo (nome, tipo, operadora) e vincula cada benefício à pessoa, com o valor pago pela empresa,
o desconto do colaborador e a vigência. Encerrar não apaga: o histórico continua. O colaborador vê os seus.
"""

from datetime import date

from onboarding_modelo import data_br

TIPOS = {
    "vale_refeicao": "Vale-refeição",
    "vale_alimentacao": "Vale-alimentação",
    "vale_transporte": "Vale-transporte",
    "plano_saude": "Plano de saúde",
    "plano_odontologico": "Plano odontológico",
    "seguro_vida": "Seguro de vida",
    "auxilio_home_office": "Auxílio home office",
    "auxilio_creche": "Auxílio-creche",
    "outro": "Outro",
}


def moeda(valor) -> str:
    """R$ 1.234,56."""
    numero = float(valor or 0)
    inteiro, centavos = f"{numero:,.2f}".split(".")
    return f"R$ {inteiro.replace(',', '.')},{centavos}"


def _vigente(v: dict, hoje: date) -> bool:
    fim = v.get("data_fim")
    return bool(v.get("ativo")) and (not fim or str(fim)[:10] >= hoje.isoformat())


def linhas(vinculos: list[dict], hoje: date) -> dict:
    """{'ativos', 'encerrados', 'total_empresa', 'total_desconto'}; cada linha com nome, tipo, operadora, valores e vigência."""
    ativos, encerrados = [], []
    for v in vinculos:
        linha = {
            "id": v.get("id"), "nome": v.get("nome") or "Benefício", "tipo": TIPOS.get(v.get("tipo"), "Outro"),
            "operadora": v.get("operadora") or "", "valor_empresa": moeda(v.get("valor_empresa")), "desconto": moeda(v.get("desconto_colaborador")),
            "desde": data_br(v.get("data_inicio")) or "—", "ate": data_br(v.get("data_fim")) or "",
            "observacao": v.get("observacao") or "", "_empresa": float(v.get("valor_empresa") or 0), "_desconto": float(v.get("desconto_colaborador") or 0),
        }
        (ativos if _vigente(v, hoje) else encerrados).append(linha)
    return {
        "ativos": ativos, "encerrados": encerrados,
        "total_empresa": moeda(sum(l["_empresa"] for l in ativos)), "total_desconto": moeda(sum(l["_desconto"] for l in ativos)),
    }


def validar_beneficio(nome: str, tipo: str | None) -> str | None:
    if len((nome or "").strip()) < 2:
        return "Informe o nome do benefício."
    if tipo not in TIPOS:
        return "Escolha o tipo."
    return None


def validar_vinculo(beneficio_id, valor_empresa, desconto, inicio: date | None, fim: date | None) -> str | None:
    if not beneficio_id:
        return "Escolha o benefício."
    if valor_empresa is None or float(valor_empresa) < 0:
        return "Informe o valor pago pela empresa (pode ser 0)."
    if desconto is None or float(desconto) < 0:
        return "Informe o desconto do colaborador (pode ser 0)."
    if not inicio:
        return "Informe o início."
    if fim and fim < inicio:
        return "O fim precisa ser igual ou depois do início."
    return None
