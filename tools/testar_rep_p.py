"""Testes do REP-P (change ponto-rep-p-e-ferias-clt): hash da marcação e cadeia de hashes.

Sem rede por padrão (roda no CI). Com --xano, compara também o hash calculado pelo backend
(`ConectaHR/hash_registro_rep`, pela CLI do Xano, perfil ConectaRH) com o deste módulo.

Uso (na raiz do repositório):
    python tools/testar_rep_p.py
    python tools/testar_rep_p.py --xano
"""

import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

import rep_modelo as m  # noqa: E402

falhas: list[str] = []
total = 0


def conferir(ok: bool, descricao: str) -> None:
    global total
    total += 1
    if not ok:
        falhas.append(descricao)
        print("  FALHA:", descricao)
    else:
        print("  ok:", descricao)


def caso(titulo: str) -> None:
    print(f"\n{titulo}")


def xano(nome: str, entrada: dict) -> dict:
    proc = subprocess.run(["xano", "function", "run", nome, "-p", "ConectaRH", "--json", json.dumps(entrada), "--no-input-check"],
                          capture_output=True, text=True, encoding="utf-8", shell=(sys.platform == "win32"))
    dado, _ = json.JSONDecoder().raw_decode(proc.stdout[proc.stdout.index("{"):])
    return dado.get("result", dado)


DH = "2026-10-14T13:01:00-0300"
caso("Campos e hash do registro tipo 7 (leiaute AFD de 31/07/2026)")
conferir(m.campo_numerico(42, 9) == "000000042" and m.campo_numerico("123.456.789-09", 12) == "012345678909", "campos numéricos com zeros à esquerda")
base = m.linha_base_marcacao(42, DH, "12345678909", DH)
conferir(base == "00000004272026-10-14T13:01:00-03000123456789092026-10-14T13:01:00-0300020", "linha base com os campos 1 a 7")
conferir(len(base) == 73, "campos 1 a 7 ocupam as posições 001 a 073")
conferir(m.hash_marcacao("abc", None) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "SHA-256 do vetor padrão \"abc\"")
anterior = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
conferir(m.hash_marcacao(base, anterior) == "c0aa2ba63ca0d775ab8e4191123a7dd373b1b4892c0793e7fd0fd4393ecc0109", "hash encadeado com o anterior")

caso("Cadeia de hashes")
cadeia, ant = [], None
for nsr, cpf in ((1, "11111111111"), (2, "22222222222"), (4, "11111111111")):
    b = m.linha_base_marcacao(nsr, DH, cpf, DH)
    h = m.hash_marcacao(b, ant)
    cadeia.append({"nsr": nsr, "tipo_registro": 7, "cpf": cpf, "data_hora_marcacao_txt": DH, "data_hora_gravacao_txt": DH, "coletor": "02", "offline": False, "hash": h, "hash_anterior": ant})
    ant = h
cadeia.append({"nsr": 3, "tipo_registro": 5})
conferir(m.conferir_cadeia(cadeia) == [], "cadeia íntegra (registros de outros tipos no meio não contam)")
adulterada = [dict(r) for r in cadeia]
adulterada[1]["data_hora_marcacao_txt"] = "2026-10-14T13:05:00-0300"
problemas = m.conferir_cadeia(adulterada)
conferir(any("NSR 2" in p for p in problemas), "alterar a hora de uma marcação quebra a conferência")

caso("CRC-16/KERMIT e campos (leiaute AFD, item 8)")
conferir(m.crc16_kermit("123456789") == "2189", "CRC-16/KERMIT de \"123456789\" = \"2189\" (exemplo do leiaute)")
conferir(m.campo_alfa("Ação", 6) == "Ação  " and m.campo_alfa("abcdef", 3) == "abc", "alfanumérico à esquerda, com espaços")
conferir(m.dh(1795223765665) == "2026-11-20T22:16:00-0300", "DH no horário de Brasília, segundos 00")

EMPREGADOR = {"tipo_identificador": "cnpj", "identificador": "12.345.678/0001-90", "cno_caepf": "", "razao_social": "Empresa Fictícia Ltda",
              "inpi_registro": "BR512026000001", "desenvolvedor_tipo_identificador": "cnpj", "desenvolvedor_identificador": "98765432000110"}
GERADO = m.datetime(2026, 11, 21, 15, 0, tzinfo=m.timezone.utc)
regs = [{"nsr": 1, "tipo_registro": 6, "data_hora_gravacao_txt": DH, "dados": {"evento": "07"}},
        {"nsr": 2, "tipo_registro": 2, "data_hora_gravacao_txt": DH, "cpf_responsavel": "11122233344",
         "dados": {"tipo_identificador": "1", "identificador": "12345678000190", "cno_caepf": "", "razao_social": "Empresa Fictícia Ltda",
                   "local_prestacao": "Av. Fictícia, 1000 - São Paulo/SP"}},
        {"nsr": 3, "tipo_registro": 5, "data_hora_gravacao_txt": DH, "cpf": "12345678909", "cpf_responsavel": "11122233344",
         "dados": {"operacao": "I", "nome": "Pessoa Fictícia"}}]
ant = None
for nsr in (4, 5):
    b = m.linha_base_marcacao(nsr, DH, "12345678909", DH)
    ant = m.hash_marcacao(b, ant)
    regs.append({"nsr": nsr, "tipo_registro": 7, "cpf": "12345678909", "data_hora_marcacao_txt": DH, "data_hora_gravacao_txt": DH,
                 "coletor": "02", "offline": False, "hash": ant})

caso("AFD de exemplo (tarefa 5.1)")
afd = m.gerar_afd(EMPREGADOR, regs, "2026-10-01", "2026-10-31", GERADO)
linhas = afd.decode("latin-1").split("\r\n")[:-1]
conferir(afd.endswith(b"\r\n") and b"\n" not in afd.replace(b"\r\n", b""), "ISO 8859-1, uma linha por registro, CR LF")
conferir([len(l) for l in linhas] == [302, 36, 331, 118, 137, 137, 64, 100], "tamanho de cada tipo: 1=302, 6=36, 2=331, 5=118, 7=137, 9=64, assinatura=100")
cab = linhas[0]
conferir(cab[:10] == "0000000001" and cab[10] == "1" and cab[11:25] == "12345678000190" and cab[189:206] == "00000512026000001"
         and cab[206:216] == "2026-10-01" and cab[216:226] == "2026-10-31" and cab[226:250] == "2026-11-21T12:00:00-0300" and cab[250:253] == "004",
         "cabeçalho: empregador, INPI (campo numérico: só os dígitos), período, geração e versão 004")
conferir(m.crc16_kermit(cab[:-4]) == cab[-4:] and m.crc16_kermit(linhas[2][:-4]) == linhas[2][-4:], "CRC do cabeçalho e do tipo 2")
conferir(linhas[3][34] == "I" and linhas[3][35:47] == "012345678909" and linhas[3][47:99].rstrip() == "Pessoa Fictícia", "tipo 5: operação, CPF e nome")
conferir(linhas[1][34:36] == "07", "tipo 6: evento 07 (disponibilidade do serviço)")
conferir(linhas[6] == "999999999" + "000000001" + "000000000" * 2 + "000000001" + "000000001" + "000000002" + "9", "trailer com as contagens")
conferir(linhas[7] == "ASSINATURA_DIGITAL_EM_ARQUIVO_P7S".ljust(100), "linha de assinatura")
conferir(m.conferir_afd(afd) == [], "conferência do AFD gerado: sem problemas")
adulterado = afd.replace(b"Pessoa Fict", b"Pessoa Falx")
conferir(any("CRC" in p for p in m.conferir_afd(adulterado)), "alterar o nome no tipo 5 quebra o CRC")
sem_linha = b"\r\n".join(l for i, l in enumerate(afd.split(b"\r\n")) if i != 4)
conferir(any("trailer" in p for p in m.conferir_afd(sem_linha)), "apagar uma marcação quebra o trailer")
conferir(m.nome_afd(EMPREGADOR) == "AFD0000051202600000112345678000190REP_P.txt", "nome do arquivo: AFD + INPI + CNPJ + REP_P")

caso("AEJ de exemplo (tarefa 5.1)")
orig = [{"id": 10, "data": "2026-10-14", "data_hora_marcacao_txt": "2026-10-14T08:00:00-0300"},
        {"id": 11, "data": "2026-10-14", "data_hora_marcacao_txt": "2026-10-14T08:05:00-0300"},
        {"id": 12, "data": "2026-10-14", "data_hora_marcacao_txt": "2026-10-14T12:00:00-0300"}]
trat = [{"id": 1, "data": "2026-10-14", "tipo": "desconsideracao", "marcacao_id": 11, "motivo": "Marcação em duplicidade"},
        {"id": 2, "data": "2026-10-14", "tipo": "inclusao", "data_hora": int(m.datetime(2026, 10, 14, 21, 0, tzinfo=m.timezone.utc).timestamp() * 1000),
         "motivo": "Esqueceu de marcar a saída"},
        {"id": 3, "data": "2026-10-14", "tipo": "inclusao", "data_hora": int(m.datetime(2026, 10, 14, 22, 0, tzinfo=m.timezone.utc).timestamp() * 1000),
         "motivo": "Inclusão errada"},
        {"id": 4, "data": "2026-10-14", "tipo": "desconsideracao", "anula_tratamento_id": 3, "motivo": "Desfaz a inclusão errada"}]
dia = m.marcacoes_do_dia([dict(o, colaborador_id=7) for o in orig], trat)
conferir([(x["dh"][11:16], x["tp"], x["seq"], x["fonte"]) for x in dia]
         == [("08:00", "E", 1, "O"), ("08:05", "D", 0, "O"), ("12:00", "S", 1, "O"), ("18:00", "E", 2, "I")],
         "dia: pares E/S, a desconsiderada como D e a inclusão desfeita fora")
dados = {"empregador": dict(EMPREGADOR, ptrp_nome="ConectaRH", ptrp_versao="1.0", desenvolvedor_nome="Equipe Fictícia", desenvolvedor_email="dev@exemplo.com"),
         "vinculos": [{"colaborador_id": 7, "cpf": "12345678909", "nome": "Pessoa Fictícia"}],
         "marcacoes": [dict(o, colaborador_id=7) for o in orig], "tratamentos": [dict(x, colaborador_id=7) for x in trat],
         "faltas": [{"colaborador_id": 7, "data": "2026-10-15"}], "banco_horas": [{"colaborador_id": 7, "data": "2026-10-16", "horas": 1.5, "tipo": "credito"}]}
aej = m.gerar_aej(dados, "2026-10-01", "2026-10-31", GERADO).decode("latin-1").split("\r\n")[:-1]
conferir(aej[0] == "01|1|12345678000190|||Empresa Fictícia Ltda|2026-10-01|2026-10-31|2026-11-21T12:00:00-0300|002", "registro 01 (cabeçalho, versão 002)")
conferir(aej[1] == "02|1|3|00000512026000001", "registro 02: REP-P com o número no INPI")
conferir(aej[2] == "03|1|12345678909|Pessoa Fictícia", "registro 03: vínculo")
conferir("05|1|2026-10-14T08:05:00-0300|1|D|000|O||Marcação em duplicidade" in aej and "05|1|2026-10-14T18:00:00-0300||E|002|I||Esqueceu de marcar a saída" in aej,
         "registro 05: desconsiderada com motivo e incluída sem REP, com motivo")
conferir("07|1|2|2026-10-15||" in aej and "07|1|3|2026-10-16|90|1" in aej, "registro 07: falta e banco de horas (90 minutos de crédito)")
conferir(aej[-2] == "99|1|1|1|0|4|0|2|1" and aej[-1] == "ASSINATURA_DIGITAL_EM_ARQUIVO_P7S".ljust(100), "trailer 99 e assinatura")
conferir([len(l.split("|")) for l in aej[:3]] == [10, 4, 4] and all(len(l.split("|")) == 9 for l in aej if l.startswith("05|"))
         and m.nome_aej(EMPREGADOR) == "AEJ12345678000190REP_P.txt", "quantidade de campos por registro (pipe entre os campos) e nome do arquivo")

if "--xano" in sys.argv:
    caso("Mesmo hash no backend (xano function run)")
    r = xano("ConectaHR/hash_registro_rep", {"nsr": 42, "data_hora_marcacao_txt": DH, "cpf": "12345678909", "data_hora_gravacao_txt": DH, "coletor": "02", "offline": False, "hash_anterior": anterior})
    conferir(r.get("linha_base") == base and r.get("hash") == m.hash_marcacao(base, anterior), "backend e frontend calculam a mesma linha e o mesmo hash")
    conferir(xano("ConectaHR/data_hora_afd", {"momento": 1619552640000}) == "2021-04-27T16:44:00-0300", "data e hora no formato DH do exemplo do leiaute")
    arp = xano("ConectaHR/registros_arp", {"inicio": "2026-01-01", "fim": "2030-12-31"})
    nsrs = [r["nsr"] for r in arp]
    conferir(nsrs == list(range(1, len(nsrs) + 1)), f"ARP com NSR de 1 a {len(nsrs)}, sem repetir nem pular")
    conferir(m.conferir_cadeia(arp) == [], f"cadeia de hashes das {sum(1 for r in arp if r['tipo_registro'] == 7)} marcações gravadas confere")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    sys.exit(1)
