"""Testes por HTTP do REP-P (change ponto-rep-p-e-ferias-clt), com login de verdade.

Roda no seu terminal: pede e-mail, senha (sem mostrar) e o código de acesso que chega por e-mail.
Nada disso é gravado. Usa duas contas:
  - uma de COLABORADOR (com ficha, admissão até hoje), que marca o ponto e pede correção;
  - uma de RH ou ADMIN, que consulta e decide.

ATENÇÃO: as marcações feitas aqui ficam para sempre na ARP (o REP-P não apaga nada). Use contas
de teste.

Uso (na raiz do repositório):
    python tools/testar_rep_p_http.py
"""

import sys
import tomllib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))
import rep_modelo as m  # noqa: E402
from ler_senha import ler_senha

SEGREDOS = tomllib.loads((RAIZ / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
BASE = SEGREDOS["xano"]["auth_base_url"].rstrip("/").rsplit("api:", 1)[0]
AUT, PONTO, COLAB = "kFmShhlY", "4PXzu46t", "ySciQ2YN"
BRT = timezone(timedelta(hours=-3))

falhas: list[str] = []
total = 0


def conferir(ok: bool, descricao: str, detalhe=None) -> None:
    global total
    total += 1
    if ok:
        print("  ok:", descricao)
    else:
        falhas.append(descricao)
        print("  FALHA:", descricao, "" if detalhe is None else f"-> {detalhe}")


def chamar(metodo, grupo, caminho, token=None, corpo=None, params=None):
    r = requests.request(metodo, f"{BASE}api:{grupo}/{caminho}", json=corpo, params=params,
                         headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=20)
    try:
        dados = r.json()
    except ValueError:
        dados = {}
    return r.status_code, dados


def entrar(papel: str) -> tuple[str, dict]:
    print(f"\nConta {papel}")
    email = input("  e-mail: ").strip()
    senha = ler_senha()
    st, d = chamar("POST", AUT, "auth/login", corpo={"email": email, "password": senha})
    if st != 200:
        sys.exit(f"  login recusado ({st}): {d.get('message')}")
    codigo = input("  código de acesso (chegou por e-mail): ").strip()
    st, d = chamar("POST", AUT, "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste REP-P"})
    if st != 200:
        sys.exit(f"  código recusado ({st}): {d.get('message')}")
    return d["token"], d.get("usuario") or {}


def caso(titulo):
    print(f"\n{titulo}")


tok_c, _ = entrar("COLABORADOR")
tok_rh, usuario_rh = entrar("RH ou ADMIN")

caso("Permissões (2.4)")
st, _ = chamar("GET", PONTO, "empregador", tok_c)
conferir(st == 403, "colaborador não vê o empregador (403)", st)
st, _ = chamar("POST", PONTO, "rep/eventos", tok_c, {"evento": "08"})
conferir(st == 403, "colaborador não registra evento do REP (403)", st)
st, emp = chamar("GET", PONTO, "empregador", tok_rh)
conferir(st == 200 and emp.get("empregador"), "RH vê o empregador", st)
e = emp.get("empregador") or {}
corpo = {k: e.get(k) for k in ("tipo_identificador", "identificador", "cno_caepf", "razao_social", "local_prestacao", "inpi_registro",
                               "desenvolvedor_tipo_identificador", "desenvolvedor_identificador", "desenvolvedor_nome", "desenvolvedor_email",
                               "ptrp_nome", "ptrp_versao")}
st, d = chamar("PUT", PONTO, "empregador", tok_rh, corpo)
conferir(st == 200 and d.get("registro_tipo_2") is False, "salvar sem mudar o empregador não grava registro tipo 2", (st, d.get("registro_tipo_2")))

caso("Marcação no REP-P (3.1)")
st, antes = chamar("GET", PONTO, "meu_ponto", tok_c)
hoje = datetime.now(BRT).date().isoformat()
qtd_antes = sum(1 for mc in (antes.get("marcacoes") or []) if mc.get("data") == hoje)
nsrs = []
for i in range(2):
    st, d = chamar("POST", PONTO, "ponto/marcar", tok_c)
    conferir(st == 200 and d.get("marcacao", {}).get("nsr"), f"marcação {qtd_antes + i + 1} do dia gravada com NSR", (st, d.get("message")))
    nsrs.append((d.get("marcacao") or {}).get("nsr"))
    if i == 1:
        cp = d.get("comprovante") or {}
        conferir(cp.get("empregador", {}).get("identificador") and cp.get("trabalhador", {}).get("cpf") and d["marcacao"].get("hash"),
                 "resposta traz os dados do comprovante (empregador, CPF, hash)")
conferir(nsrs[0] and nsrs[1] and nsrs[1] > nsrs[0], "NSR cresce entre as marcações", nsrs)
st, depois = chamar("GET", PONTO, "meu_ponto", tok_c)
qtd_depois = sum(1 for mc in (depois.get("marcacoes") or []) if mc.get("data") == hoje)
conferir(qtd_depois == qtd_antes + 2, "meu_ponto devolve as marcações do dia", (qtd_antes, qtd_depois))

caso("Comprovantes (3.3)")
st, cps = chamar("GET", PONTO, "ponto/comprovantes", tok_c)
conferir(st == 200 and {n for n in nsrs} <= {mc["nsr"] for mc in cps.get("marcacoes") or []}, "as marcações de agora estão nos comprovantes", st)
conferir((cps.get("empregador") or {}).get("inpi_registro") is not None and (cps.get("trabalhador") or {}).get("cpf"), "comprovantes trazem empregador e trabalhador")

caso("Pedido de correção (3.2)")
ontem = (datetime.now(BRT).date() - timedelta(days=1))
inicio_ontem = datetime(ontem.year, ontem.month, ontem.day, 9, 0, tzinfo=BRT)
st, d = chamar("POST", PONTO, "ponto/correcao", tok_c, {"data": ontem.isoformat(), "tipo": "inclusao",
                                                      "data_hora": int((inicio_ontem + timedelta(days=2)).timestamp() * 1000),
                                                      "justificativa": "teste: horario no futuro"})
conferir(st == 400, "horário no futuro é recusado", (st, d.get("message")))
st, d = chamar("POST", PONTO, "ponto/correcao", tok_c, {"data": ontem.isoformat(), "tipo": "inclusao",
                                                      "data_hora": int(inicio_ontem.timestamp() * 1000), "justificativa": "teste REP-P: entrada esquecida"})
conferir(st == 200 and d.get("correcao", {}).get("status") == "pendente", "pedido de inclusão de ontem fica pendente", (st, d.get("message")))
correcao_id = (d.get("correcao") or {}).get("id")

caso("Decisão vira tratamento (3.2)")
if correcao_id:
    st, d = chamar("POST", PONTO, f"correcoes_ponto/{correcao_id}/aprovar", tok_rh)
    conferir(st == 200, "RH aprova o pedido", (st, d.get("message")))
    st, mp = chamar("GET", PONTO, "meu_ponto", tok_c)
    tr = [t for t in mp.get("tratamentos") or [] if t.get("correcao_ponto_id") == correcao_id]
    conferir(len(tr) == 1 and tr[0]["tipo"] == "inclusao", "a aprovação criou o tratamento de inclusão", tr)
    reg = next((r for r in mp.get("registros") or [] if r.get("data") == ontem.isoformat()), {})
    conferir(reg.get("status") == "Ajustado", "o dia de ontem ficou AJUSTADO", reg.get("status"))

caso("Folha do mês sem CPF nem hash (3.3)")
hoje_d = datetime.now(BRT).date()
st, folha = chamar("GET", PONTO, "folha_ponto/mes", tok_rh, params={"ano": hoje_d.year, "mes": hoje_d.month})
mcs = folha.get("marcacoes") or []
conferir(st == 200 and mcs, "a folha traz as marcações do mês", st)
conferir(all("cpf" not in mc and "hash" not in mc for mc in mcs), "a folha não expõe CPF nem hash")

caso("Cadeia de hashes (2.3)")
ok_cadeia = True
try:
    import subprocess, json  # noqa: E401
    proc = subprocess.run(["xano", "function", "run", "ConectaHR/registros_arp", "-p", "ConectaRH", "--json",
                           json.dumps({"inicio": "2026-01-01", "fim": "2030-12-31"}), "--no-input-check"],
                          capture_output=True, text=True, encoding="utf-8", shell=(sys.platform == "win32"))
    arp = json.JSONDecoder().raw_decode(proc.stdout[proc.stdout.index("{"):])[0]["result"]
    conferir(m.conferir_cadeia(arp) == [], "cadeia íntegra depois das marcações deste teste")
except Exception as exc:  # sem a CLI do Xano, pula
    print("  (pulado: precisa da CLI do Xano com o perfil ConectaRH)", exc)

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
