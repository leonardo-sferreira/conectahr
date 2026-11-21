"""Mede o contraste de texto do tema (tarefa 61 da change concluir-frontend-streamlit), sem rede.

Lê o CSS final de `frontend/theme.py` (claro e escuro). Mede cada regra que define a cor do texto e um fundo sólido na
mesma regra (selos, alertas, botões). Mede também as cores de texto soltas contra o fundo de onde elas aparecem: o
cartão e a página (claro: branco e marfim; escuro: cartão e fundo) e o menu lateral, que é grafite nos dois temas.
Critério: WCAG AA, 4,5:1 para texto até 18px. Sai com erro se algum par ficar abaixo.

Uso (na raiz do repositório):
    python tools/medir_contraste.py
"""

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "frontend"))

import theme  # noqa: E402

MINIMO = 4.5
HEX = r"#[0-9A-Fa-f]{6}\b"
# Seletores do menu lateral (fundo grafite nos dois temas).
MENU = ("stSidebar", "navgrupo", "crh-nav", "st-key-nav")
# Cores que não são texto de leitura: bordas, ícones, fundos e o âmbar de botão (texto grafite em cima).
IGNORAR_COR = {theme.AMBAR.upper()}
# Regras cujo fundo vem de outra regra ou do próprio Streamlit: o fundo real, conferido no tema.
FUNDO_REAL = {
    "crh-header": theme.GRAFITE,          # cabeçalho das telas de login, sobre .stApp grafite (_AUTH_CSS)
    "crh-hero": theme.GRAFITE,            # banner do título das páginas (fundo grafite na regra .crh-hero)
    "crh-link-aviso-rotulo": theme.GRAFITE,  # rótulos dos links da tela Entrar, também sobre o grafite
    'ae_aba button[aria-checked="true"]': theme.AMBAR,  # aba ativa: o fundo âmbar está na regra do botão
    "calendar": "#262730",                # calendário do seletor de data: abre com o fundo escuro do Streamlit
    "stExpandSidebarButton": theme.GRAFITE,  # botão de abrir o menu no celular: o fundo grafite está na própria regra
}
# Variáveis de texto de status (tarefa 61): valores do tema claro e do escuro.
VARIAVEIS = {
    "claro": {"--crh-ok": theme.SUCESSO_TEXTO, "--crh-amb": theme.AMBAR_TEXTO, "--crh-err": theme.ERRO_TEXTO},
    "escuro": {"--crh-ok": "#4ADE80", "--crh-amb": theme.AMBAR, "--crh-err": "#FCA5A5"},
}


def luminancia(cor: str) -> float:
    canais = [int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def razao(a: str, b: str) -> float:
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def regras(css: str):
    for seletor, corpo in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        texto = re.search(r"(?<![-\w])color\s*:\s*(" + HEX + ")", corpo)
        fundo = re.search(r"background(?:-color)?\s*:\s*(" + HEX + ")", corpo)
        yield " ".join(seletor.split())[-90:], texto.group(1).upper() if texto else None, fundo.group(1).upper() if fundo else None


def medir(nome: str, css: str, superficies: list[str], menu: str) -> list[tuple]:
    for var, valor in VARIAVEIS[nome].items():
        css = css.replace(f"var({var})", valor)
    abaixo, vistos = [], set()
    for seletor, texto, fundo in regras(css):
        if not texto or texto in IGNORAR_COR:
            continue
        real = next((v for k, v in FUNDO_REAL.items() if k in seletor), None)
        if real:
            pares = [real]
        elif fundo:
            pares = [fundo]
        elif any(m in seletor for m in MENU):
            pares = [menu]
        else:
            pares = superficies
        for f in pares:
            r = razao(texto, f)
            chave = (texto, f, seletor)
            if r < MINIMO and chave not in vistos:
                vistos.add(chave)
                abaixo.append((nome, round(r, 2), texto, f, seletor))
    return abaixo


claro = theme._BASE_CSS + theme._APP_CSS + theme._AUTH_CSS + theme._AVISO_CSS
# No escuro, o CSS claro continua valendo por baixo; entram as regras dele com texto de status por variável (sem fundo
# próprio), que mudam de cor, e as regras do próprio tema escuro.
com_var = "".join(f"{sel}{{{corpo}}}" for sel, corpo in re.findall(r"([^{}]+)\{([^{}]*)\}", claro) if "var(--crh-" in corpo and "background" not in corpo)
escuro = com_var + theme._ESCURO_CSS + theme._AVISO_ESCURO_CSS
problemas = medir("claro", claro, ["#FFFFFF", theme.MARFIM], theme.GRAFITE)
problemas += medir("escuro", escuro, [theme.ESC_CARTAO, theme.ESC_FUNDO], theme.GRAFITE)
for tema, r, texto, fundo, seletor in sorted(problemas, key=lambda p: p[1]):
    print(f"  {tema:6} {r:>4}:1  {texto} sobre {fundo}  ({seletor})")
print(f"\n{len(problemas)} par(es) abaixo de {MINIMO}:1.")
sys.exit(1 if problemas else 0)
