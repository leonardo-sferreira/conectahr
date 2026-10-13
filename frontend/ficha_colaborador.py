"""
Ficha do colaborador para o RH (pedido do usuário em 13/10/2026): os dados cadastrais, os documentos enviados e o PDF
da ficha. Funções puras, sem Streamlit.

Dados: o registro de `colaboradores` (RH e Admin), o `organograma` e `documentos` (todos, filtrados pela pessoa).
Minimização (LGPD): o salário não entra (fica só no cadastro) e a conta bancária aparece mascarada, só com os últimos
dígitos; o arquivo de cada documento abre pelo link assinado e auditado, nunca vai para o PDF.
"""

from datetime import datetime

from fpdf import FPDF

from cadastro_modelo import ficha
from comprovante_ponto import _latin1, formatar_cpf
from documentos_modelo import STATUS, linhas_dados, rotulo_tipo
from onboarding_modelo import data_br

SITUACOES = {"ATIVO": "Ativo", "AFASTADO": "Afastado", "DESLIGADO": "Desligado"}
TIPOS_CONTA = {"corrente": "Conta corrente", "poupanca": "Poupança", "salario": "Conta salário"}
AVISO_LGPD = ("Documento com dados pessoais (LGPD): uso restrito ao RH, para a finalidade do vínculo de trabalho. "
              "Não compartilhe fora da empresa. Salário e dados bancários completos ficam só no sistema.")


def _texto(valor) -> str:
    return str(valor).strip() if valor not in (None, "") else "—"


def _telefone(valor) -> str:
    d = "".join(c for c in str(valor or "") if c.isdigit())
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return d or "—"


def _cep(valor) -> str:
    d = "".join(c for c in str(valor or "") if c.isdigit())
    return f"{d[:5]}-{d[5:]}" if len(d) == 8 else (d or "—")


def conta_mascarada(conta, digito) -> str:
    """'123456', '7' -> '•••• 3456-7': o RH reconhece a conta sem que ela apareça inteira."""
    d = "".join(c for c in str(conta or "") if c.isalnum())
    if not d:
        return "—"
    fim = d[-4:] if len(d) > 4 else d
    return f"•••• {fim}" + (f"-{digito}" if digito else "")


def secoes(colab: dict, organograma: dict, usuarios: list[dict], colabs: list[dict]) -> list[tuple[str, list[tuple[str, str]]]]:
    """As seções da ficha: (título, [(rótulo, valor)])."""
    endereco = ", ".join(x for x in (colab.get("logradouro"), colab.get("numero"), colab.get("complemento")) if x)
    cidade = " / ".join(x for x in (colab.get("cidade"), colab.get("estado")) if x)
    vinculo = ficha(colab, organograma, usuarios, colabs)
    vinculo.insert(0, ("Situação", SITUACOES.get(str(colab.get("status") or "").upper(), _texto(colab.get("status")))))
    if colab.get("data_desligamento"):
        vinculo.append(("Desligamento", data_br(colab.get("data_desligamento")) or "—"))
    banco = [("Banco", _texto(colab.get("banco"))), ("Agência", _texto(colab.get("agencia"))),
             ("Conta", conta_mascarada(colab.get("conta"), colab.get("digito"))),
             ("Tipo", TIPOS_CONTA.get(str(colab.get("tipo_conta") or "").lower(), _texto(colab.get("tipo_conta"))))]
    return [
        ("Dados pessoais", [("Nome", _texto(colab.get("nome"))), ("CPF", formatar_cpf(colab.get("cpf")) or "—"),
                            ("Nascimento", data_br(colab.get("data_nascimento")) or "—"), ("E-mail pessoal", _texto(colab.get("email_pessoal"))),
                            ("Telefone", _telefone(colab.get("telefone")))]),
        ("Endereço", [("CEP", _cep(colab.get("cep"))), ("Logradouro", endereco or "—"), ("Bairro", _texto(colab.get("bairro"))),
                      ("Cidade / UF", cidade or "—")]),
        ("Vínculo", vinculo),
        ("Conta bancária", banco),
    ]


def documentos_da_pessoa(documentos: list[dict], colaborador_id) -> list[dict]:
    """Os documentos enviados pela pessoa, do mais recente ao mais antigo, com o que a seta de detalhes usa."""
    linhas = []
    for d in documentos:
        if d.get("colaborador_id") != colaborador_id:
            continue
        selo, tom = STATUS.get(d.get("status"), ("—", "neu"))
        if d.get("estado_verificacao") == "bloqueado":
            selo, tom = "Arquivo bloqueado", "err"
        linhas.append({
            "id": d.get("id"), "documento": d.get("nome_documento") or rotulo_tipo(d.get("tipo")),
            "enviado": data_br(d.get("created_at")) or "—", "validade": data_br(d.get("data_validade")) or "—",
            "situacao": (selo, tom), "arquivo": "bloqueado" if d.get("estado_verificacao") == "bloqueado" else "abrir",
            "motivo_bloqueio": d.get("motivo_bloqueio"), "dados_informados": linhas_dados(d), "_ordem": str(d.get("created_at") or ""),
        })
    linhas.sort(key=lambda l: l["_ordem"], reverse=True)
    for l in linhas:
        l.pop("_ordem")
    return linhas


def ficha_pdf(nome: str, secoes_ficha: list, documentos: list[dict], gerado_por: str, agora: datetime, comprimir: bool = True) -> bytes:
    """O PDF da ficha (A4): as seções, os documentos com os dados informados e o aviso de LGPD. `comprimir=False` deixa o
    texto legível no arquivo (usado nos testes)."""
    pdf = FPDF(format="A4")
    pdf.set_compression(comprimir)
    pdf.set_title(_latin1(f"Ficha do colaborador - {nome}"))
    pdf.set_creator("ConectaRH")
    pdf.set_margins(16, 14, 16)
    pdf.set_auto_page_break(True, 16)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(23, 23, 26)
    pdf.cell(0, 9, _latin1("Ficha do colaborador"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, _latin1(nome), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    def titulo(texto: str) -> None:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(23, 23, 26)
        pdf.set_fill_color(248, 246, 241)
        pdf.cell(0, 7, _latin1(texto), fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def linha(rotulo: str, valor: str) -> None:
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(102, 102, 110)
        pdf.cell(48, 5.5, _latin1(rotulo))
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(23, 23, 26)
        pdf.multi_cell(0, 5.5, _latin1(valor.replace("•", "*")), new_x="LMARGIN", new_y="NEXT")

    for nome_secao, campos in secoes_ficha:
        titulo(nome_secao)
        for rotulo, valor in campos:
            linha(rotulo, valor)
        pdf.ln(2)

    titulo(f"Documentos enviados ({len(documentos)})")
    if not documentos:
        linha("", "Nenhum documento enviado.")
    for d in documentos:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(23, 23, 26)
        pdf.cell(0, 6, _latin1(f"{d['documento']} - {d['situacao'][0]}"), new_x="LMARGIN", new_y="NEXT")
        linha("Enviado em / validade", f"{d['enviado']} / {d['validade']}")
        for rotulo, valor in d["dados_informados"]:
            linha(rotulo, valor)
        pdf.ln(1.5)

    pdf.ln(2)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(102, 102, 110)
    pdf.set_fill_color(248, 246, 241)
    pdf.multi_cell(0, 5, _latin1(f"{AVISO_LGPD} Gerado por {gerado_por} em {agora.strftime('%d/%m/%Y %H:%M')}."), fill=True,
                   new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def nome_arquivo_ficha(nome: str) -> str:
    base = "".join(c if c.isalnum() else "-" for c in (nome or "colaborador").lower()).strip("-")
    while "--" in base:
        base = base.replace("--", "-")
    return f"ficha-{base or 'colaborador'}.pdf"
