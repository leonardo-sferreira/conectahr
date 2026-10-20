"""
O que cada campo aceita (pedido do usuário, 20/10/2026): número só número, nome só letras, endereço letras e números, e
nenhum campo aceita emoji.

- `limpar(valor, tipo)` é a regra pura: devolve o texto só com o permitido e o que saiu.
- `campo(...)` desenha um campo de um tipo: ao sair do campo (ou ao clicar num botão), o que não é permitido é apagado
  e um aviso flutuante diz o que saiu e por quê. O formulário pergunta `houve_correcao(...)` antes de gravar, para a
  pessoa ver a correção e confirmar com um novo clique.
- `instalar_filtro_emoji()` (chamado uma vez pelo app.py) faz todo `text_input` e `text_area` com `key` tirar emoji e
  caracteres de controle, mesmo os que não usam `campo(...)`.
- `data_por_partes(...)`: data em três listas (dia, mês e ano), para a data de nascimento, em que o calendário obriga a
  voltar mês a mês.

O backend continua sendo a validação de verdade (telefone e número do endereço só com dígitos em `colaboradores`).
"""

import calendar
import functools
import unicodedata
from datetime import date

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.elements.lib.form_utils import is_in_form

_PONTUACAO_ENDERECO = set(" .,-/º°ª#()'&")
_PONTUACAO_NOME = set(" '-.")
_PONTUACAO_EMAIL = set("._%+-@")

# tipo: (o que aceita, explicação no aviso)
TIPOS = {
    "numero": "só números",
    "nome": "só letras (com acento), espaço, hífen e apóstrofo",
    "endereco": "letras, números e a pontuação de endereço",
    "email": "letras, números e . _ % + - @, sem espaço",
    "codigo": "só letras e números, sem espaço",
    "texto": "texto sem emoji",
}
_CHAVE_CORRIGIDOS = "_campos_corrigidos"


def eh_emoji(c: str) -> bool:
    """Emoji, pictograma, seletor de variação, junção de emoji e caractere de controle."""
    codigo = ord(c)
    if c in "\n\t°":
        return False
    if unicodedata.category(c) in ("So", "Cs", "Co", "Cn", "Cc", "Cf", "Sk") and not c.isalnum():
        return True
    return 0x1F000 <= codigo <= 0x1FAFF or 0x2600 <= codigo <= 0x27BF or 0xFE00 <= codigo <= 0xFE0F or codigo in (0x200D, 0x20E3)


def _permitido(c: str, tipo: str) -> bool:
    if eh_emoji(c):
        return False
    if tipo == "numero":
        return c.isdigit() and c.isascii()
    if tipo == "nome":
        return c.isalpha() or c in _PONTUACAO_NOME
    if tipo == "endereco":
        return c.isalnum() or c in _PONTUACAO_ENDERECO
    if tipo == "codigo":
        return c.isascii() and c.isalnum()
    if tipo == "email":
        return c.isascii() and (c.isalnum() or c in _PONTUACAO_EMAIL)
    return True


def limpar(valor: str | None, tipo: str = "texto") -> tuple[str, str]:
    """(texto só com o permitido, o que saiu)."""
    if not valor:
        return valor or "", ""
    fica, sai = [], []
    for c in valor:
        (fica if _permitido(c, tipo) else sai).append(c)
    return "".join(fica), "".join(sai)


def _sanear(chave: str, tipo: str, rotulo: str) -> None:
    valor = st.session_state.get(chave)
    if not isinstance(valor, str):
        return
    limpo, saiu = limpar(valor, tipo)
    if not saiu:
        return
    st.session_state[chave] = limpo
    st.session_state.setdefault(_CHAVE_CORRIGIDOS, []).append(rotulo)
    mostrado = saiu if len(saiu) <= 12 else saiu[:12] + "…"
    st.toast(f"{rotulo}: removemos “{mostrado}”. Este campo aceita {TIPOS.get(tipo, TIPOS['texto'])}.", icon=":material/warning:")


def _com_saneamento(chave, tipo: str, rotulo: str, on_change, args, kwargs):
    """on_change que limpa o campo e depois chama o on_change de quem desenhou o campo."""
    def callback():
        _sanear(chave, tipo, rotulo)
        if on_change:
            on_change(*(args or ()), **(kwargs or {}))
    return callback


def campo(container, rotulo: str, tipo: str, key: str, area: bool = False, **kw) -> str:
    """Um text_input (ou text_area) de um tipo de `TIPOS`, que se limpa ao sair do campo."""
    on_change, args, kwargs = kw.pop("on_change", None), kw.pop("args", None), kw.pop("kwargs", None)
    instalar_filtro_emoji()
    if container is st:
        container = st._main  # st.text_input usa o container principal, que respeita o `with` em volta
    desenhar = _DESENHAR["area" if area else "input"]
    return desenhar(container, rotulo, key=key, on_change=_com_saneamento(key, tipo, rotulo, on_change, args, kwargs), _tipo_campo=tipo, **kw)


def houve_correcao() -> list[str]:
    """Campos limpos desde a última consulta (o clique num botão também dispara a limpeza). O formulário mostra e não
    grava; a lista é consumida aqui, então o clique seguinte segue (dentro de um st.dialog o app.py não roda de novo)."""
    return list(st.session_state.pop(_CHAVE_CORRIGIDOS, None) or [])


def mensagem_correcao(rotulos: list[str]) -> str:
    nomes = ", ".join(dict.fromkeys(rotulos))
    return f"Removemos caracteres que não são aceitos em: {nomes}. Confira os campos e clique de novo."


def fim_da_rodada() -> None:
    """Chamado pelo app.py depois da página: a lista de correções vale só para a rodada em que aconteceram."""
    st.session_state.pop(_CHAVE_CORRIGIDOS, None)


# ---------------------------------------------------------------------------
# Filtro de emoji em todo campo de texto
# ---------------------------------------------------------------------------
_DESENHAR: dict = {}


def _envolver(original):
    @functools.wraps(original)
    def desenhar(self, label, *args, _tipo_campo: str | None = None, **kw):
        if is_in_form(self):
            # Dentro de st.form o Streamlit só aceita callback no botão do formulário: ali vale a validação do envio.
            if _tipo_campo is not None:
                kw.pop("on_change", None)
        elif _tipo_campo is None and kw.get("key") is not None and not kw.get("disabled"):
            kw["on_change"] = _com_saneamento(kw["key"], "texto", str(label), kw.get("on_change"), kw.pop("args", None), kw.pop("kwargs", None))
        return original(self, label, *args, **kw)
    return desenhar


def instalar_filtro_emoji() -> None:
    """Uma vez por processo: todo text_input/text_area com `key` passa a tirar emoji ao sair do campo."""
    if _DESENHAR:
        return
    for nome, chave in (("text_input", "input"), ("text_area", "area")):
        original = getattr(DeltaGenerator, nome)
        envolvido = _envolver(original)
        _DESENHAR[chave] = envolvido
        setattr(DeltaGenerator, nome, envolvido)
        # st.text_input e st.text_area são métodos já ligados ao container principal: passam a usar o envolvido.
        setattr(st, nome, functools.partial(envolvido, st._main))


# ---------------------------------------------------------------------------
# Data em três listas
# ---------------------------------------------------------------------------
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def montar_data(dia, mes, ano) -> date | None:
    """A data das três partes; None se faltar uma ou se o dia não existir no mês (31/02)."""
    if not (dia and mes and ano):
        return None
    if dia > calendar.monthrange(ano, mes)[1]:
        return None
    return date(ano, mes, dia)


def data_por_partes(container, rotulo: str, key: str, ano_min: int, ano_max: int, valor: date | None = None) -> date | None:
    """Dia, mês e ano em listas lado a lado, sob um rótulo. Devolve a data ou None (incompleta ou inválida)."""
    container.html(f'<p class="crh-rotulo-data">{rotulo}</p>')
    c1, c2, c3 = container.columns([1, 1.6, 1.2], gap="small")
    dia = c1.selectbox(f"{rotulo}: dia", list(range(1, 32)), index=valor.day - 1 if valor else None, placeholder="Dia", key=f"{key}_dia", label_visibility="collapsed")
    mes = c2.selectbox(f"{rotulo}: mês", list(range(1, 13)), index=valor.month - 1 if valor else None, format_func=lambda m: MESES[m - 1], placeholder="Mês",
                       key=f"{key}_mes", label_visibility="collapsed")
    anos = list(range(ano_max, ano_min - 1, -1))
    ano = c3.selectbox(f"{rotulo}: ano", anos, index=anos.index(valor.year) if valor and valor.year in anos else None, placeholder="Ano",
                       key=f"{key}_ano", label_visibility="collapsed")
    escolhida = montar_data(dia, mes, ano)
    if dia and mes and ano and escolhida is None:
        container.html(f'<p class="crh-cfg-nota" style="color:#DC2626;margin:0">{MESES[mes - 1]} de {ano} não tem dia {dia}.</p>')
    return escolhida
