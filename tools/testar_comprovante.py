"""Testes do comprovante de registro de ponto em PDF (change ponto-rep-p-e-ferias-clt, tarefa 4.1).

Sem rede. Gera o PDF sem compressão e confere que o texto tem os campos do art. 79 da Portaria
MTP nº 671/2021: título, NSR, empregador com CNPJ, local, nome e CPF do trabalhador, data e hora,
registro no INPI e hash.

Uso (na raiz do repositório):
    python tools/testar_comprovante.py
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

import comprovante_ponto as c  # noqa: E402

falhas: list[str] = []
total = 0


def conferir(ok: bool, descricao: str) -> None:
    global total
    total += 1
    if ok:
        print("  ok:", descricao)
    else:
        falhas.append(descricao)
        print("  FALHA:", descricao)


# Dados fictícios, como no Figma 465:830.
MARCACAO = {"nsr": 1286, "data_hora_marcacao_txt": "2026-10-14T13:01:00-0300",
            "hash": "3f9a1c5e8b2d47f0a6c19e3b5d7f2a8c4e6b1d9f0a3c5e7b9d1f2a4c6e8b0d2f"}
EMPREGADOR = {"razao_social": "ConectaRH Tecnologia Ltda (ficticio)", "tipo_identificador": "cnpj", "identificador": "12345678000190",
              "cno_caepf": "", "local_prestacao": "Av. Paulista, 1000 - Bela Vista, Sao Paulo/SP", "inpi_registro": "BR512026000000"}
TRABALHADOR = {"nome": "Leonardo dos Santos", "cpf": "12345678909"}

print("\nFormatação")
conferir(c.formatar_nsr(1286) == "000001286", "NSR com 9 dígitos")
conferir(c.formatar_cpf("12345678909") == "123.456.789-09", "CPF com pontos e traço")
conferir(c.formatar_cnpj("12345678000190") == "12.345.678/0001-90", "CNPJ com pontos, barra e traço")
conferir(c.data_hora_comprovante("2026-10-14T13:01:00-0300") == "14/10/2026 13:01 (UTC-03:00)", "data e hora com o fuso")
conferir("CPF 123.456.789-09" in c.identificacao_empregador({**EMPREGADOR, "tipo_identificador": "cpf", "identificador": "12345678909"}),
         "empregador pessoa física sai com CPF")
conferir("CNO/CAEPF 123456789012" in c.identificacao_empregador({**EMPREGADOR, "cno_caepf": "123456789012"}), "CNO ou CAEPF quando houver")

print("\nTexto do PDF (art. 79)")
pdf = c.comprovante_pdf(MARCACAO, EMPREGADOR, TRABALHADOR, comprimir=False)
# No PDF, os parênteses do texto saem escapados ("\(").
texto = pdf.decode("latin-1").replace(r"\(", "(").replace(r"\)", ")")
conferir(pdf.startswith(b"%PDF"), "o arquivo é um PDF")
for descricao, trecho in (
    ("título", "Comprovante de Registro de Ponto do Trabalhador"),
    ("NSR", "000001286"),
    ("empregador e CNPJ", "ConectaRH Tecnologia Ltda (ficticio) · CNPJ 12.345.678/0001-90"),
    ("local da prestação", "Av. Paulista, 1000 - Bela Vista, Sao Paulo/SP"),
    ("nome e CPF do trabalhador", "Leonardo dos Santos · CPF 123.456.789-09"),
    ("data e horário", "14/10/2026 13:01 (UTC-03:00)"),
    ("registro no INPI", "BR512026000000"),
    ("hash SHA-256", MARCACAO["hash"]),
    ("aviso sem ICP-Brasil", "sem assinatura eletr"),
):
    conferir(trecho in texto, f"tem {descricao}")
conferir(c.nome_arquivo(MARCACAO) == "comprovante-ponto-nsr-000001286.pdf", "nome do arquivo com o NSR")
conferir(c.comprovante_pdf(MARCACAO, EMPREGADOR, TRABALHADOR).startswith(b"%PDF"), "PDF comprimido também é gerado")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    sys.exit(1)
