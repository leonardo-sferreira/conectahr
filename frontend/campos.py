"""
O que cada campo aceita (pedido do usuário, 20/10/2026): número só número, nome só letras, endereço letras e números, e
nenhum campo aceita emoji.

Como funciona (sem mexer no que a pessoa digita, e sem callback):
- todo `text_input`/`text_area` com `key` se registra na rodada e, se tiver o que não é permitido, mostra um aviso
  vermelho logo abaixo;
- todo botão `type="primary"` (Salvar, Enviar, Admitir...) confere os campos registrados: se algum tiver o que não é
  permitido, mostra um aviso flutuante ("Não é permitido emoji em …") e o clique não grava.

Versão anterior (PR #73) apagava o caractere num callback com `st.toast`; dentro de um st.dialog isso apaga a página
inteira (o Streamlit avisa: "displaying elements in a callback during a fragment rerun is not supported"). Por isso aqui
nada roda em callback.

- `campo(...)` desenha um campo de um tipo de `TIPOS`.
- `nova_rodada()` (app.py, a cada execução completa) zera o registro; `instalar()` (app.py, uma vez) liga o aviso e a
  conferência dos botões.
- `data_por_partes(...)`: data em três listas (dia, mês e ano), para a data de nascimento.
- `limpar(...)` é a regra pura (usada também para tirar a máscara de valores já gravados, como o telefone).

O backend continua sendo a validação de verdade (telefone e número do endereço só com dígitos em `colaboradores`).
"""

import calendar
import functools
import html
import unicodedata
from datetime import date

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

_PONTUACAO_ENDERECO = set(" .,-/º°ª#()'&")
_PONTUACAO_NOME = set(" '-.")
_PONTUACAO_EMAIL = set("._%+-@")

# tipo: o que aceita (vai no aviso)
TIPOS = {
    "numero": "só números",
    "nome": "só letras (com acento), espaço, hífen e apóstrofo",
    "endereco": "letras, números e a pontuação de endereço",
    "email": "letras, números e . _ % + - @, sem espaço",
    "codigo": "só letras e números, sem espaço",
    "texto": "texto sem emoji",
}
_REGISTRO = "_campos_da_rodada"


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
    """(texto só com o permitido, o que não é permitido)."""
    if not valor:
        return valor or "", ""
    fica, sai = [], []
    for c in valor:
        (fica if _permitido(c, tipo) else sai).append(c)
    return "".join(fica), "".join(sai)


def aviso(rotulo: str, valor: str | None, tipo: str) -> str | None:
    """A frase do aviso, ou None se o valor só tem o permitido."""
    saiu = limpar(valor, tipo)[1]
    if not saiu:
        return None
    tem_emoji = any(eh_emoji(c) for c in saiu)
    if tipo == "texto" or (tem_emoji and all(eh_emoji(c) for c in saiu)):
        return f"{rotulo}: não é permitido emoji. Apague para continuar."
    mostrado = "".join(dict.fromkeys(c for c in saiu if not c.isspace())) or "espaço"
    return f"{rotulo}: aceita {TIPOS[tipo]}. Apague “{mostrado[:12]}” para continuar."


# ---------------------------------------------------------------------------
# Registro da rodada e conferência dos botões
# ---------------------------------------------------------------------------
def nova_rodada() -> None:
    """app.py, a cada execução completa: os campos da rodada anterior saem do registro. Num st.dialog (fragmento) o
    app.py não roda de novo: os campos da página continuam registrados (seguem na tela, atrás do modal)."""
    st.session_state[_REGISTRO] = {}


def _registrar(chave: str, rotulo: str, tipo: str) -> None:
    st.session_state.setdefault(_REGISTRO, {})[chave] = (rotulo, tipo)


def campos_invalidos() -> list[str]:
    """Os avisos dos campos registrados nesta rodada que têm o que não é permitido."""
    avisos = []
    for chave, (rotulo, tipo) in list((st.session_state.get(_REGISTRO) or {}).items()):
        valor = st.session_state.get(chave)
        if isinstance(valor, str) and (frase := aviso(rotulo, valor, tipo)):
            avisos.append(frase)
    return avisos


_DESENHAR: dict = {}


def _envolver_campo(original):
    @functools.wraps(original)
    def desenhar(self, label, *args, _tipo_campo: str | None = None, **kw):
        valor = original(self, label, *args, **kw)
        chave = kw.get("key")
        if chave is not None and not kw.get("disabled"):
            tipo = _tipo_campo or "texto"
            _registrar(chave, str(label), tipo)
            if isinstance(valor, str) and (frase := aviso(str(label), valor, tipo)):
                self.html(f'<p class="crh-campo-invalido">{html.escape(frase)}</p>')
        return valor
    return desenhar


def _envolver_botao(original):
    @functools.wraps(original)
    def botao(self, label, *args, **kw):
        clicado = original(self, label, *args, **kw)
        if clicado and kw.get("type") == "primary" and (avisos := campos_invalidos()):
            # Pop-up de aviso (no corpo da página, nunca em callback) e o clique não vale.
            st.toast(" ".join(avisos), icon=":material/block:")
            return False
        return clicado
    return botao


def instalar() -> None:
    """Uma vez por processo: campos com aviso e registro; botões principais com a conferência."""
    if _DESENHAR:
        return
    for nome, chave, envolver in (("text_input", "input", _envolver_campo), ("text_area", "area", _envolver_campo), ("button", "botao", _envolver_botao)):
        envolvido = envolver(getattr(DeltaGenerator, nome))
        _DESENHAR[chave] = envolvido
        setattr(DeltaGenerator, nome, envolvido)
        # st.text_input, st.text_area e st.button são métodos ligados ao container principal: passam a usar o envolvido.
        setattr(st, nome, functools.partial(envolvido, st._main))


def campo(container, rotulo: str, tipo: str, key: str, area: bool = False, **kw) -> str:
    """Um text_input (ou text_area) de um tipo de `TIPOS`."""
    instalar()
    if container is st:
        container = st._main  # st.text_input usa o container principal, que respeita o `with` em volta
    return _DESENHAR["area" if area else "input"](container, rotulo, key=key, _tipo_campo=tipo, **kw)


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
        container.html(f'<p class="crh-campo-invalido">{MESES[mes - 1]} de {ano} não tem dia {dia}.</p>')
    return escolhida
