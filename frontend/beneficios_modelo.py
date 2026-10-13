"""
Regras de apresentação de "Benefícios" (tarefa 82 da change concluir-frontend-streamlit). Funções puras, sem
Streamlit. A conferir com o Figma, que estava fora do ar quando a tela foi feita.

O RH cadastra o catálogo (nome, tipo, operadora) e vincula cada benefício à pessoa, com o valor pago pela empresa,
o desconto do colaborador e a vigência. Encerrar não apaga: o histórico continua. O colaborador vê os seus.

Apresentação (change apresentacao-de-beneficios): o colaborador vê os benefícios ativos como itens que abrem, com a
descrição, os links e os materiais que o RH cadastrou, sem valores.
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


# ---------------------------------------------------------------------------
# Apresentação dos benefícios (change apresentacao-de-beneficios, D3 a D5)
# ---------------------------------------------------------------------------
MAX_LINKS = 10


def apresentacao(vinculos: list[dict], hoje: date) -> list[dict]:
    """Os benefícios vigentes da pessoa para a tela de apresentação, sem valores: nome, tipo, operadora, descrição,
    links e materiais (id e nome). Um benefício aparece uma vez, mesmo com dois vínculos vigentes."""
    vistos, itens = set(), []
    for v in vinculos:
        chave = v.get("beneficio_id") or v.get("id")
        if not _vigente(v, hoje) or chave in vistos:
            continue
        vistos.add(chave)
        itens.append({
            "beneficio_id": chave, "nome": v.get("nome") or "Benefício", "tipo": TIPOS.get(v.get("tipo"), "Outro"),
            "operadora": v.get("operadora") or "", "descricao": v.get("descricao") or "",
            "links": [l for l in (v.get("links") or []) if l.get("url")], "arquivos": v.get("arquivos") or [],
        })
    return sorted(itens, key=lambda i: i["nome"].casefold())


def links_texto(links: list[dict] | None) -> str:
    """Links para o campo de edição: um por linha, "Título | https://endereço"."""
    return "\n".join(f"{l.get('titulo', '')} | {l.get('url', '')}" for l in links or [])


def ler_links(texto: str) -> tuple[list[dict], str | None]:
    """Lê o campo de links (um por linha, "Título | https://endereço"); devolve (links, erro). Linha em branco é ignorada."""
    links = []
    for numero, linha in enumerate((texto or "").splitlines(), start=1):
        if not linha.strip():
            continue
        if "|" not in linha:
            return [], f"Linha {numero} dos links: use \"Título | https://endereço\"."
        titulo, url = (parte.strip() for parte in linha.split("|", 1))
        if not 2 <= len(titulo) <= 80:
            return [], f"Linha {numero} dos links: o título precisa ter de 2 a 80 caracteres."
        if not url.lower().startswith("https://") or len(url) < 12 or len(url) > 500:
            return [], f"Linha {numero} dos links: o endereço precisa começar com https://."
        links.append({"titulo": titulo, "url": url})
    if len(links) > MAX_LINKS:
        return [], f"Cadastre no máximo {MAX_LINKS} links."
    return links, None


def validar_material(nome: str, nome_arquivo: str | None, tamanho: int | None) -> str | None:
    """Material de leitura do benefício: nome que o colaborador vê e o arquivo (mesmas regras dos documentos)."""
    from documentos_modelo import TAMANHO_MAXIMO, TIPOS_ARQUIVO, extensao

    if not 2 <= len((nome or "").strip()) <= 100:
        return "Dê um nome ao material, como \"Guia do plano\"."
    if not nome_arquivo:
        return "Anexe o arquivo do material."
    if extensao(nome_arquivo) not in TIPOS_ARQUIVO:
        return "Envie um arquivo PDF, JPG ou PNG."
    if not tamanho:
        return "O arquivo está vazio. Escolha outro."
    if tamanho > TAMANHO_MAXIMO:
        return "O arquivo pode ter no máximo 10 MB."
    return None


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
