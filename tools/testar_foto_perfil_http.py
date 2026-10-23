"""Testes por HTTP da foto de perfil (change foto-de-perfil), com login de verdade.

Roda no seu terminal. Pede uma conta com ficha de colaborador (a que envia a foto) e, opcional, uma do RH ou do Admin
(a que remove). Para cada uma, e-mail, senha e o código que chega por e-mail. A foto do teste é uma imagem de cor
sólida gerada aqui, sem dado pessoal. Confere:
- envio pelo endereço de uso único, gravação e a URL assinada abrindo;
- o arquivo não abre sem assinatura (o bucket é privado);
- a foto aparece no organograma visto pela própria conta;
- caminho fora do padrão e arquivo que não foi enviado são recusados;
- o Colaborador não remove a foto de outra pessoa pela rota do RH (403);
- o RH exige justificativa e remove; depois, a foto some.
No fim, a foto de teste é removida.

Uso (na raiz do repositório):
    python tools/testar_foto_perfil_http.py
"""

import io
import sys
import tomllib
import uuid
from pathlib import Path

import requests
from PIL import Image

from ler_senha import ler_senha
from limite_http import pedir

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
SEGREDOS = tomllib.loads((RAIZ / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
BASE = SEGREDOS["xano"]["auth_base_url"].rstrip("/").rsplit("api:", 1)[0]
AUT, COL, DEP = "kFmShhlY", "ySciQ2YN", "wcbcMmlw"
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


def entrar(papel, opcional=False):
    print(f"\nConta {papel}")
    email = input("  e-mail" + (" (Enter para pular)" if opcional else "") + ": ").strip()
    if opcional and not email:
        return None, {}
    senha = ler_senha()
    st, d = chamar("POST", "auth/login", corpo={"email": email, "password": senha}, grupo=AUT)
    if st != 200:
        sys.exit(f"  login recusado ({st}): {d.get('message')}")
    codigo = input("  código de acesso (chegou por e-mail): ").strip()
    st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Foto de perfil"}, grupo=AUT)
    if st != 200:
        sys.exit(f"  código recusado ({st}): {d.get('message')}")
    return d["token"], d.get("usuario") or {}


def foto_de_teste() -> bytes:
    saida = io.BytesIO()
    Image.new("RGB", (256, 256), (245, 166, 35)).save(saida, format="WEBP", quality=85)
    return saida.getvalue()


tok, usuario = entrar("que envia a foto (com ficha de colaborador)")
colab_id = usuario.get("colaborador_id")
if not colab_id:
    sys.exit("  a conta precisa ter ficha de colaborador.")
tok_rh, rh = entrar("do RH ou Admin, para testar a remoção", opcional=True)

print("\nSem login")
st, _ = chamar("POST", "minha_foto/envio", corpo={})
conferir(st == 401, "envio sem token: 401", st)

print("\nEnviar a foto")
st, envio = chamar("POST", "minha_foto/envio", tok, {})
conferir(st == 200 and envio.get("upload_url") and str(envio.get("caminho", "")).endswith(".webp"), "endereço de envio de uso único", (st, envio.get("message")))
caminho = envio.get("caminho")
if envio.get("upload_url"):
    r = requests.put(envio["upload_url"], data=foto_de_teste(), headers={"Content-Type": "image/webp"}, timeout=60)
    conferir(r.ok, "o arquivo chega ao armazenamento", r.status_code)
st, d = chamar("POST", "minha_foto", tok, {"caminho": caminho})
url = d.get("foto_url")
conferir(st == 200 and url, "grava a foto e devolve a URL assinada", (st, d.get("message")))
if url:
    conferir(requests.get(url, timeout=30).status_code == 200, "a URL assinada abre")
    conferir("token=" in url, "a URL tem assinatura (não é um link público permanente)")
    supabase = url.split("/storage/v1/")[0]
    conferir(requests.get(f"{supabase}/storage/v1/object/public/fotos-perfil/{caminho}", timeout=30).status_code != 200,
             "sem assinatura, o arquivo não abre (bucket privado)")
st, org = chamar("GET", "organograma", tok, grupo=DEP)
eu = next((c for c in org.get("colaboradores") or [] if c.get("id") == colab_id), {})
conferir(st == 200 and eu.get("foto_url") and "foto_path" not in eu, "a foto aparece no organograma, sem o caminho do arquivo", st)

print("\nRecusas")
st, d = chamar("POST", "minha_foto", tok, {"caminho": "../outra-pessoa.webp"})
conferir(st == 400, "caminho fora do padrão: 400", (st, d.get("message")))
st, d = chamar("POST", "minha_foto", tok, {"caminho": f"{uuid.uuid4()}.webp"})
conferir(st == 400, "arquivo que não foi enviado: 400", (st, d.get("message")))
if str(usuario.get("perfil") or "").upper() not in ("RH", "ADMIN"):
    st, d = chamar("DELETE", f"colaboradores/{colab_id}/foto?justificativa=Teste%20sem%20permissao", tok)
    conferir(st == 403, "Colaborador não usa a rota do RH: 403", (st, d.get("message")))

if tok_rh:
    print("\nRemoção pelo RH")
    st, d = chamar("DELETE", f"colaboradores/{colab_id}/foto?justificativa=curta", tok_rh)
    conferir(st == 400, "justificativa curta: 400", (st, d.get("message")))
    st, d = chamar("DELETE", f"colaboradores/{colab_id}/foto?justificativa=TESTE%20autom%C3%A1tico%20de%20remo%C3%A7%C3%A3o", tok_rh)
    conferir(st == 200, "o RH remove com justificativa", (st, d.get("message")))
    st, d = chamar("GET", "minha_foto", tok)
    conferir(st == 200 and d.get("foto_url") is None, "depois da remoção, sem foto (aparecem as iniciais)", d)

print("\nLimpeza")
st, d = chamar("DELETE", "minha_foto", tok)
conferir(st == 200, "a foto de teste é removida", (st, d.get("message")))

print(f"\n{total - len(falhas)}/{total} verificações ok.")
sys.exit(1 if falhas else 0)
