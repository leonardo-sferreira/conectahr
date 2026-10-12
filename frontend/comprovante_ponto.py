"""
Comprovante de Registro de Ponto do Trabalhador em PDF (Portaria MTP nº 671/2021, arts. 79 e 80; change
ponto-rep-p-e-ferias-clt, tarefa 4.1; Figma 465:830). Sem Streamlit.

Os dados vêm prontos do backend (`ponto/marcar` e `ponto/comprovantes`): NSR, data e hora com fuso, hash,
empregador e trabalhador. Aqui só se formata. Fonte Helvetica do próprio PDF (sem arquivo de fonte), em
ISO 8859-1: os textos evitam caracteres fora dela (ex.: travessão vira hífen).
"""

from fpdf import FPDF

TITULO = "Comprovante de Registro de Ponto do Trabalhador"
RODAPE = "Documento gerado pelo ConectaRH, sem assinatura eletrônica ICP-Brasil (projeto acadêmico)."


def _digitos(valor) -> str:
    return "".join(c for c in str(valor or "") if c.isdigit())


def formatar_cpf(cpf) -> str:
    d = _digitos(cpf)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if len(d) == 11 else d


def formatar_cnpj(cnpj) -> str:
    d = _digitos(cnpj)
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}" if len(d) == 14 else d


def formatar_nsr(nsr) -> str:
    return _digitos(nsr).rjust(9, "0")


def identificacao_empregador(empregador: dict) -> str:
    """'Razão social · CNPJ 12.345.678/0001-90' (ou CPF), mais o CNO/CAEPF quando houver."""
    tipo = str(empregador.get("tipo_identificador") or "cnpj").lower()
    if tipo in ("cpf", "2"):
        doc = f"CPF {formatar_cpf(empregador.get('identificador'))}"
    else:
        doc = f"CNPJ {formatar_cnpj(empregador.get('identificador'))}"
    texto = f"{empregador.get('razao_social') or ''} · {doc}"
    if cno := _digitos(empregador.get("cno_caepf")):
        texto += f" · CNO/CAEPF {cno}"
    return texto


def data_hora_comprovante(data_hora_txt: str) -> str:
    """'2026-10-14T13:01:00-0300' -> '14/10/2026 13:01 (UTC-03:00)'."""
    t = str(data_hora_txt or "")
    if len(t) < 16:
        return t
    fuso = t[19:] if len(t) >= 24 else ""
    fuso_txt = f" (UTC{fuso[:3]}:{fuso[3:]})" if len(fuso) == 5 else ""
    return f"{t[8:10]}/{t[5:7]}/{t[:4]} {t[11:16]}{fuso_txt}"


def campos_comprovante(marcacao: dict, empregador: dict, trabalhador: dict) -> list[tuple[str, str]]:
    """Os campos do art. 79, na ordem do Figma, como (rótulo, valor)."""
    return [
        ("NSR", formatar_nsr(marcacao.get("nsr"))),
        ("Empregador", identificacao_empregador(empregador)),
        ("Local da prestação de serviço", str(empregador.get("local_prestacao") or "")),
        ("Trabalhador", f"{trabalhador.get('nome') or ''} · CPF {formatar_cpf(trabalhador.get('cpf'))}"),
        ("Data e horário da marcação", data_hora_comprovante(marcacao.get("data_hora_marcacao_txt"))),
        ("Registro do programa no INPI (REP-P)", str(empregador.get("inpi_registro") or "")),
        ("Código hash (SHA-256)", str(marcacao.get("hash") or "")),
    ]


def _latin1(texto: str) -> str:
    return texto.replace("—", "-").replace("–", "-").encode("latin-1", "replace").decode("latin-1")


def comprovante_pdf(marcacao: dict, empregador: dict, trabalhador: dict, comprimir: bool = True) -> bytes:
    """O PDF de uma marcação. `comprimir=False` deixa o texto legível no arquivo (usado nos testes)."""
    pdf = FPDF(orientation="landscape", format=(148, 210))  # A5
    pdf.set_compression(comprimir)
    pdf.set_title(TITULO)
    pdf.set_creator("ConectaRH")
    pdf.set_margins(14, 12, 14)
    pdf.set_auto_page_break(True, 12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(23, 23, 26)
    pdf.cell(0, 9, _latin1(TITULO), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    for rotulo, valor in campos_comprovante(marcacao, empregador, trabalhador):
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(102, 102, 110)
        pdf.cell(0, 4.5, _latin1(rotulo), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Courier" if rotulo.startswith("Código hash") else "Helvetica", "", 8 if rotulo.startswith("Código hash") else 11)
        pdf.set_text_color(23, 23, 26)
        pdf.multi_cell(0, 5.5, _latin1(valor), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.2)
    pdf.ln(1)
    pdf.set_fill_color(248, 246, 241)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(102, 102, 110)
    pdf.multi_cell(0, 6, _latin1(RODAPE), fill=True, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def nome_arquivo(marcacao: dict) -> str:
    return f"comprovante-ponto-nsr-{formatar_nsr(marcacao.get('nsr'))}.pdf"
