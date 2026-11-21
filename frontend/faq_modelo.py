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


PUBLICOS = {"todos": "Toda a empresa", "departamento": "Um departamento", "perfil": "Um perfil"}
PERFIS_ALVO = ["Colaborador", "Gestor", "RH", "Admin"]
SITUACOES_COMUNICADO = {None: "Situação: Todos", "publicado": "Situação: Publicados", "agendado": "Situação: Agendados",
                        "encerrado": "Situação: Encerrados", "arquivado": "Situação: Arquivados"}


def situacao_comunicado(c: dict, hoje: date) -> tuple[str, str, str]:
    """(chave, rótulo, tom do selo): arquivado, agendado (começa depois de hoje), encerrado (vigência passou) ou publicado."""
    if not c.get("ativo", True):
        return "arquivado", "Arquivado", "neu"
    inicio, fim = _dia(c.get("data_inicio")), _dia(c.get("data_fim"))
    if inicio and inicio > hoje:
        return "agendado", "Agendado", "azul"
    if fim and fim < hoje:
        return "encerrado", "Encerrado", "neu"
    return "publicado", "Publicado", "ok"


def linhas_comunicados_rh(comunicados: list[dict], deps: dict, hoje: date, situacao: str | None = None) -> list[dict]:
    """Lista do RH (Figma 245:594): [{id, titulo, publico, publicacao, vigencia, situacao, arquivavel}]."""
    linhas = []
    for c in comunicados_ordenados(comunicados or []):
        chave, rotulo, tom = situacao_comunicado(c, hoje)
        if situacao and chave != situacao:
            continue
        publico = c.get("publico_alvo")
        alvo = (deps.get(c.get("departamento_id")) or "Departamento") if publico == "departamento" else (c.get("perfil_alvo") or "Perfil") if publico == "perfil" else "Toda a empresa"
        inicio, fim = _dia(c.get("data_inicio")), _dia(c.get("data_fim"))
        linhas.append({"id": c.get("id"), "titulo": c.get("titulo") or "Comunicado", "publico": alvo, "publicacao": f"{inicio:%d/%m/%Y}" if inicio else "—",
                       "vigencia": f"até {fim:%d/%m/%Y}" if fim else "sem fim", "situacao": (rotulo, tom), "arquivavel": chave != "arquivado",
                       "conteudo": c.get("conteudo") or ""})
    return linhas


def validar_comunicado(titulo: str, conteudo: str, publico: str, departamento_id, perfil_alvo, inicio: date | None, fim: date | None) -> str | None:
    """Os limites de `comunicados` POST, antes de enviar."""
    if not 3 <= len((titulo or "").strip()) <= 200:
        return "O título tem de 3 a 200 caracteres."
    if not 5 <= len((conteudo or "").strip()) <= 5000:
        return "O texto tem de 5 a 5.000 caracteres."
    if publico not in PUBLICOS:
        return "Escolha para quem é o comunicado."
    if publico == "departamento" and not departamento_id:
        return "Escolha o departamento."
    if publico == "perfil" and perfil_alvo not in PERFIS_ALVO:
        return "Escolha o perfil."
    if not inicio:
        return "Informe a data de publicação."
    if fim and fim < inicio:
        return "O fim da vigência não pode ser antes da publicação."
    return None


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
