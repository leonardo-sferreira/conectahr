"""Testes por HTTP das funções de conformidade (changes canal-de-denuncias, riscos-psicossociais e
treinamentos-obrigatorios), com login de verdade. Não grava nada: só lê e testa recusas.

Roda no seu terminal: pede e-mail, senha e o código que chega por e-mail. Com uma conta do RH ou do Admin, confere as
rotas do RH; com qualquer conta, as da própria pessoa; e confere que a fila de denúncias só abre para quem é da
comissão de ética.

Uso (na raiz do repositório):
    python tools/testar_conformidade_http.py
"""

import sys
import tomllib
from pathlib import Path

from ler_senha import ler_senha
from limite_http import pedir

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
SEGREDOS = tomllib.loads((RAIZ / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
BASE = SEGREDOS["xano"]["auth_base_url"].rstrip("/").rsplit("api:", 1)[0]
AUT, COL = "kFmShhlY", "ySciQ2YN"
INEXISTENTE = 999999999
falhas: list[str] = []
total = 0


def conferir(ok, descricao, detalhe=None):
    global total
    total += 1
    print("  ok:" if ok else "  FALHA:", descricao, "" if ok or detalhe is None else f"-> {detalhe}")
    if not ok:
        falhas.append(descricao)


def chamar(metodo, caminho, token=None, corpo=None, grupo=COL):
    r = pedir(metodo, f"{BASE}api:{grupo}/{caminho}", json=corpo, headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


print("\nConta para o teste (RH ou Admin confere também as rotas do RH)")
email = input("  e-mail: ").strip()
senha = ler_senha()
st, d = chamar("POST", "auth/login", corpo={"email": email, "password": senha}, grupo=AUT)
if st != 200:
    sys.exit(f"  login recusado ({st}): {d.get('message')}")
codigo = input("  código de acesso (chegou por e-mail): ").strip()
st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Conformidade"}, grupo=AUT)
if st != 200:
    sys.exit(f"  código recusado ({st}): {d.get('message')}")
tok, usuario = d["token"], d.get("usuario") or {}
perfil = str(usuario.get("perfil") or "").strip().upper()
rh = perfil in ("RH", "ADMIN")

print("\nCanal de denúncias")
st, me = chamar("GET", "auth/me", tok, grupo=AUT)
membro = bool(me.get("membro_comissao_etica"))
conferir(st == 200 and "membro_comissao_etica" in me, "auth/me diz se a conta é da comissão de ética", (st, me.get("message")))
st, d = chamar("GET", "minha_comissao_etica", tok)
conferir(st == 200 and d.get("membro") == membro, "minha_comissao_etica igual ao auth/me", st)
st, d = chamar("GET", "denuncias", tok)
conferir(st == (200 if membro else 403), f"fila de denúncias: {'abre para membro' if membro else '403 para quem não é da comissão (mesmo RH ou Admin)'}", (st, d.get("message")))
if membro:
    conferir({"nova", "em_apuracao", "concluida_no_ano"} <= set(d.get("contagens") or {}), "fila com as contagens")
    conferir(all("identificacao" not in x for x in d.get("denuncias") or []), "a lista não traz a identificação")
st, d = chamar("GET", "comissao_etica", tok)
conferir(st == (200 if perfil == "ADMIN" else 403), "membros da comissão: só o Admin", st)

print("\nRiscos psicossociais (NR-1)")
if rh:
    st, d = chamar("GET", "pesquisas_clima_rh", tok)
    conferir(st == 200 and all("tipo" in p for p in d.get("pesquisas") or []), "pesquisas do RH com o tipo", (st, d.get("message")))
    st, d = chamar("GET", "acoes_psicossociais", tok)
    conferir(st == 200 and isinstance(d.get("acoes"), list), "plano de ação", (st, d.get("message")))
    st, d = chamar("POST", "acoes_psicossociais", tok, {"pesquisa_id": INEXISTENTE, "dimensao": "Carga e ritmo de trabalho", "medida": "Teste de recusa da rota",
                                                        "responsavel": "RH", "prazo": "2099-12-31"})
    conferir(st == 404, "ação em avaliação inexistente: 404 sem gravar", (st, d.get("message")))
    st, d = chamar("PATCH", f"acoes_psicossociais/{INEXISTENTE}", tok, {"status": "concluida"})
    conferir(st == 404, "atualizar ação inexistente: 404", st)
else:
    st, d = chamar("GET", "acoes_psicossociais", tok)
    conferir(st == 403, "quem não é RH nem Admin não vê o plano: 403", st)

print("\nTreinamentos")
st, d = chamar("GET", "meus_treinamentos", tok)
conferir(st in (200, 404), "meus treinamentos: qualquer perfil (404 só sem ficha)", (st, d.get("message")))
if st == 200:
    conferir(isinstance(d.get("obrigatorios"), list) and isinstance(d.get("conclusoes"), list), "obrigatórios e conclusões")
if rh:
    st, d = chamar("GET", "treinamentos", tok)
    conferir(st == 200 and {"treinamentos", "conclusoes", "pessoas", "departamentos"} <= set(d), "catálogo, conclusões e pessoas numa chamada", (st, d.get("message")))
    st, d = chamar("POST", "treinamentos", tok, {"nome": "Teste", "categoria": "qualquer", "carga_horas": 1, "validade_meses": 0, "obrigatorio": True, "publico": "todos"})
    conferir(st == 400, "categoria inválida: 400 sem gravar", (st, d.get("message")))
    st, d = chamar("POST", f"treinamentos/{INEXISTENTE}/conclusoes", tok, {"colaborador_ids": [1], "concluido_em": "2026-01-01"})
    conferir(st == 404, "conclusão em treinamento inexistente: 404", (st, d.get("message")))
else:
    st, d = chamar("GET", "treinamentos", tok)
    conferir(st == 403, "quem não é RH nem Admin não vê o catálogo do RH: 403", st)

print(f"\n{total - len(falhas)}/{total} verificações ok.")
sys.exit(1 if falhas else 0)
