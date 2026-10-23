"""
Regras do organograma (change organograma-hierarquia; Figma 224:3593). Funções puras, sem Streamlit.

A árvore segue o superior direto (`colaborador.superior_colaborador_id`, D1): abaixo de cada pessoa ficam as que a têm
como superior. Fica no topo quem não tem superior ou aponta para alguém fora do organograma (desligado). Um ciclo
(A abaixo de B e B abaixo de A, por engano de cadastro) não some: a pessoa de nível mais alto do ciclo vai para o topo.
O nível do cargo (`nivel_hierarquico`, D2) ordena e rotula; cargo sem nível vem depois. Só nome, cargo, nível e
departamento aparecem (D5).
"""

import unicodedata

SEM_NIVEL = "Sem nível"
_ORDEM_SEM_NIVEL = 10_000


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto or "") if unicodedata.category(c) != "Mn").casefold()


def iniciais(nome: str) -> str:
    partes = [p for p in (nome or "").split() if p[:1].isalpha()]
    return (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper() if partes else "?"


def _chave(p: dict) -> tuple:
    return (p["ordem_nivel"], _sem_acento(p["nome"]))


def montar(org: dict) -> dict:
    """{id: pessoa} com {'id', 'nome', 'iniciais', 'cargo', 'nivel', 'ordem_nivel', 'departamento', 'departamento_id',
    'superior_id'}; `superior_id` já é o efetivo (None no topo, inclusive quem fechava um ciclo)."""
    niveis = {n.get("id"): n for n in org.get("niveis") or []}
    cargos = {c.get("id"): c for c in org.get("cargos") or []}
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or []}
    pessoas = {}
    for c in org.get("colaboradores") or []:
        cargo = cargos.get(c.get("cargo_id")) or {}
        nivel = niveis.get(cargo.get("nivel_hierarquico_id"))
        pessoas[c.get("id")] = {
            "id": c.get("id"), "nome": c.get("nome") or "Colaborador", "iniciais": iniciais(c.get("nome") or ""),
            "cargo": cargo.get("nome") or "", "nivel": (nivel or {}).get("nome") or "",
            "ordem_nivel": int((nivel or {}).get("ordem") or _ORDEM_SEM_NIVEL), "departamento": deps.get(c.get("departamento_id")) or "",
            "departamento_id": c.get("departamento_id"), "superior_id": c.get("superior_colaborador_id"),
            "foto_url": c.get("foto_url"),
        }
    for p in pessoas.values():
        if p["superior_id"] not in pessoas or p["superior_id"] == p["id"]:
            p["superior_id"] = None
    # Ciclos: quem, subindo, encontra a si mesmo de novo. A pessoa de nível mais alto do ciclo vai para o topo.
    for pid in list(pessoas):
        vistos, atual = [], pid
        while atual is not None and atual not in vistos:
            vistos.append(atual)
            atual = pessoas[atual]["superior_id"]
        if atual is not None:
            ciclo = vistos[vistos.index(atual):]
            cabeca = min(ciclo, key=lambda i: _chave(pessoas[i]))
            pessoas[cabeca]["superior_id"] = None
    return pessoas


def topo(pessoas: dict) -> list[dict]:
    """Quem não tem superior no organograma, pelo nível e pelo nome."""
    return sorted((p for p in pessoas.values() if p["superior_id"] is None), key=_chave)


def abaixo(pessoas: dict, pid) -> list[dict]:
    """Quem tem `pid` como superior direto, pelo nível e pelo nome."""
    return sorted((p for p in pessoas.values() if p["superior_id"] == pid), key=_chave)


def caminho(pessoas: dict, pid) -> list[dict]:
    """Do topo até `pid` (inclusive). `montar` já desfez os ciclos, então a subida termina."""
    lista, atual = [], pessoas.get(pid)
    while atual is not None:
        lista.append(atual)
        atual = pessoas.get(atual["superior_id"])
    return list(reversed(lista))


def por_nivel(lista: list[dict]) -> list[tuple[str, list[dict]]]:
    """[(nível, pessoas)] na ordem da lista (que já vem pelo nível); sem nível, "Sem nível"."""
    grupos: list[tuple[str, list[dict]]] = []
    for p in lista:
        rotulo = p["nivel"] or SEM_NIVEL
        if grupos and grupos[-1][0] == rotulo:
            grupos[-1][1].append(p)
        else:
            grupos.append((rotulo, [p]))
    return grupos


def detalhe(p: dict) -> str:
    """"Analista de RH · Analista · Recursos Humanos"."""
    return " · ".join(x for x in (p["cargo"], p["nivel"], p["departamento"]) if x) or "—"


def buscar(pessoas: dict, texto: str = "", departamento_id=None) -> list[dict]:
    """Pessoas com todas as palavras no nome, no cargo ou no nível (sem acento), do departamento escolhido."""
    palavras = _sem_acento(texto).split()
    saida = []
    for p in pessoas.values():
        if departamento_id and p["departamento_id"] != departamento_id:
            continue
        alvo = _sem_acento(f"{p['nome']} {p['cargo']} {p['nivel']}")
        if all(w in alvo for w in palavras):
            saida.append(p)
    return sorted(saida, key=_chave)


# ---------------------------------------------------------------------------
# Estrutura da empresa: níveis e cargos
# ---------------------------------------------------------------------------
def linhas_niveis(niveis: list[dict], cargos: list[dict]) -> list[dict]:
    """{'id', 'ordem', 'nome', 'ativo', 'cargos'} pela ordem: quantos cargos usam cada nível."""
    uso = {}
    for c in cargos:
        uso[c.get("nivel_hierarquico_id")] = uso.get(c.get("nivel_hierarquico_id"), 0) + 1
    return [{"id": n.get("id"), "ordem": int(n.get("ordem") or 0), "nome": n.get("nome") or "", "ativo": bool(n.get("ativo", True)),
             "cargos": uso.get(n.get("id"), 0)} for n in sorted(niveis, key=lambda n: (int(n.get("ordem") or 0), _sem_acento(n.get("nome") or "")))]


def validar_nivel(nome: str, ordem) -> str | None:
    if len((nome or "").strip()) < 2:
        return "Escreva o nome do nível (pelo menos 2 caracteres)."
    if len(nome.strip()) > 60:
        return "O nome do nível pode ter no máximo 60 caracteres."
    if ordem is None or not 1 <= int(ordem) <= 99:
        return "A ordem vai de 1 (topo) a 99."
    return None
