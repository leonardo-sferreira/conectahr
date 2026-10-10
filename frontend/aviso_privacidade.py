"""
Texto do aviso de privacidade, lido de `docs/lgpd/aviso-de-privacidade.md` (tarefas 5, 59 e 67 da
change concluir-frontend-streamlit).

O arquivo é a fonte única: o documento, as telas do Figma (285:874 sem login e 285:1073 logado) e
esta tela mostram o mesmo texto. Do arquivo, a tela deixa de fora só o que é da documentação: a nota
em citação ("Nota da documentação") e a coluna "Registro" da tabela (códigos F01 a F19). Os links
do arquivo viram texto simples, como no Figma.

Funções puras, sem Streamlit: `carregar()` devolve um dicionário com o que a tela desenha.
"""

import html
import re
from functools import lru_cache
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parent.parent / "docs" / "lgpd" / "aviso-de-privacidade.md"

_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_NEGRITO = re.compile(r"\*\*(.+?)\*\*")


def texto_simples(markdown: str) -> str:
    """Tira links, negrito e crases: o texto como aparece na tela."""
    return _LINK.sub(r"\1", markdown).replace("**", "").replace("`", "")


def em_html(markdown: str) -> str:
    """Trecho de Markdown em linha para HTML seguro: escapa tudo e mantém o negrito só nos rótulos
    terminados em dois-pontos ("Xano:", "Como exercer:"), como no Figma; o resto do negrito do
    documento vira texto normal."""
    texto = html.escape(_LINK.sub(r"\1", markdown).replace("`", ""))
    return _NEGRITO.sub(lambda m: f"<strong>{m.group(1)}</strong>" if m.group(1).endswith(":") else m.group(1), texto)


def _celulas(linha: str) -> list[str]:
    return [c.strip() for c in linha.strip().strip("|").split("|")]


def interpretar(markdown: str) -> dict:
    """{'titulo', 'intro', 'selos', 'tabela': {'cabecalho', 'linhas'}, 'destaque', 'secoes': [...]}.

    Cada seção: {'titulo', 'blocos'}; um bloco é ('p', texto), ('ul', [itens]), ('ol', [itens]) ou
    ('campos', [(rótulo, valor)]) para a lista "Rótulo: valor" do encarregado."""
    aviso = {"titulo": "", "intro": "", "selos": [], "tabela": {"cabecalho": [], "linhas": []}, "destaque": "", "secoes": []}
    secao = None
    blocos: list = []
    for bruto in markdown.splitlines():
        linha = bruto.rstrip()
        if not linha or linha.startswith(">") or re.fullmatch(r"\|?[-| ]+\|?", linha):
            continue
        if linha.startswith("# "):
            aviso["titulo"] = linha[2:].strip()
        elif linha.startswith("## "):
            secao = {"titulo": linha[3:].strip(), "blocos": []}
            aviso["secoes"].append(secao)
            blocos = secao["blocos"]
        elif secao is None:
            if linha.startswith("**Versão:**"):
                resto = texto_simples(linha.replace("**Versão:**", "")).strip()
                aviso["selos"] = [s.strip().rstrip(".") for s in resto.split(". ") if s.strip()]
            elif not aviso["intro"]:
                aviso["intro"] = linha
        elif linha.startswith("|"):
            celulas = _celulas(linha)
            if celulas and celulas[-1] == "Registro" or re.fullmatch(r"F\d\d(, F\d\d)?", celulas[-1]):
                celulas = celulas[:-1]  # coluna só da documentação
            tabela = aviso["tabela"]
            if not tabela["cabecalho"]:
                tabela["cabecalho"] = [texto_simples(c) for c in celulas]
            else:
                tabela["linhas"].append(celulas)
        elif m := re.match(r"^- \*\*(.+?):\*\* (.+)$", linha):
            if blocos and blocos[-1][0] == "campos":
                blocos[-1][1].append((m.group(1), m.group(2)))
            elif aviso["secoes"][-1]["titulo"].startswith("Fale com"):
                blocos.append(("campos", [(m.group(1), m.group(2))]))
            else:
                _item(blocos, "ul", linha[2:])
        elif linha.startswith("- "):
            _item(blocos, "ul", linha[2:])
        elif m := re.match(r"^\d+\. (.+)$", linha):
            _item(blocos, "ol", m.group(1))
        elif aviso["tabela"]["linhas"] and not aviso["destaque"] and len(aviso["secoes"]) == 1:
            aviso["destaque"] = linha  # "O sistema não coleta..." logo depois da tabela
        else:
            blocos.append(("p", linha))
    return aviso


def _item(blocos: list, tipo: str, texto: str) -> None:
    if blocos and blocos[-1][0] == tipo:
        blocos[-1][1].append(texto)
    else:
        blocos.append((tipo, [texto]))


@lru_cache(maxsize=1)
def carregar() -> dict:
    return interpretar(ARQUIVO.read_text(encoding="utf-8"))


def encarregado() -> dict:
    """{'Encarregado': 'a definir', 'Contato': 'privacidade@conectarh.com'}: só a parte antes do parêntese,
    como no cartão de Configurações → Privacidade (Figma 286:878)."""
    for secao in carregar()["secoes"]:
        for tipo, conteudo in secao["blocos"]:
            if tipo == "campos":
                return {rotulo: texto_simples(valor).split(" (")[0].rstrip(".") for rotulo, valor in conteudo}
    return {}


def versao() -> str:
    """"Rascunho de 10/10/2026": o primeiro selo do aviso."""
    selos = carregar()["selos"]
    return selos[0] if selos else ""
