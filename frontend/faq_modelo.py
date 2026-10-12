"""
Regras de apresentação de "Comunicados e FAQ" (Figma 217:154 e 245:594; pedido do usuário em 12/10/2026). Funções puras,
sem Streamlit.

Dados: `artigos_faq` (os ativos, para todos) e `meus_comunicados` (os vigentes e visíveis à pessoa). As categorias da FAQ são
as do backend (`artigo_faq.categoria`); o comunicado não tem categoria.
"""

import unicodedata
from datetime import date

CATEGORIAS = {"ferias": "Férias", "ponto": "Ponto", "documentos": "Documentos", "politicas_internas": "Políticas internas"}
_PUBLICO_ALVO = {"todos": "Toda a empresa", "departamento": "Seu departamento"}


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto or "") if unicodedata.category(c) != "Mn").casefold()


def filtrar_artigos(artigos: list[dict], categoria: str | None = None, busca: str = "") -> list[dict]:
    """Os artigos ativos da categoria (None = todas) que têm todas as palavras da busca no título ou na resposta, sem
    diferença de acento nem de maiúscula. Em ordem de categoria e título."""
    palavras = _sem_acento(busca).split()
    saida = []
    for a in artigos:
        if not a.get("ativo", True) or (categoria and a.get("categoria") != categoria):
            continue
        texto = _sem_acento(f"{a.get('titulo') or ''} {a.get('conteudo') or ''}")
        if all(p in texto for p in palavras):
            saida.append(a)
    ordem = list(CATEGORIAS)
    saida.sort(key=lambda a: (ordem.index(a["categoria"]) if a.get("categoria") in ordem else len(ordem), _sem_acento(a.get("titulo") or "")))
    return saida


def contagem_por_categoria(artigos: list[dict]) -> dict:
    """{categoria: quantos artigos ativos}."""
    contagem = {c: 0 for c in CATEGORIAS}
    for a in artigos:
        if a.get("ativo", True) and a.get("categoria") in contagem:
            contagem[a["categoria"]] += 1
    return contagem


def _dia(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def meta_comunicado(c: dict) -> str:
    """"Toda a empresa · publicado em 01/09/2026 · vigente até 30/09/2026"."""
    publico = c.get("publico_alvo")
    partes = [c.get("perfil_alvo") if publico == "perfil" else _PUBLICO_ALVO.get(publico, "")]
    if inicio := _dia(c.get("data_inicio")):
        partes.append(f"publicado em {inicio:%d/%m/%Y}")
    if fim := _dia(c.get("data_fim")):
        partes.append(f"vigente até {fim:%d/%m/%Y}")
    return " · ".join(p for p in partes if p)


def comunicados_ordenados(comunicados: list[dict]) -> list[dict]:
    """Do mais recente para o mais antigo (pela data de início)."""
    return sorted(comunicados, key=lambda c: str(c.get("data_inicio") or ""), reverse=True)


def validar_artigo(categoria: str | None, titulo: str, conteudo: str) -> str | None:
    """Os limites do backend (`artigos_faq` POST): categoria da lista, título até 200 e resposta até 5.000 caracteres."""
    if categoria not in CATEGORIAS:
        return "Escolha a categoria."
    if len((titulo or "").strip()) < 5:
        return "Escreva a pergunta (pelo menos 5 caracteres)."
    if len(titulo.strip()) > 200:
        return "A pergunta pode ter no máximo 200 caracteres."
    if len((conteudo or "").strip()) < 10:
        return "Escreva a resposta (pelo menos 10 caracteres)."
    if len(conteudo.strip()) > 5000:
        return "A resposta pode ter no máximo 5.000 caracteres."
    return None
