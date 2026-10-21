"""Testes dos treinamentos obrigatórios (change treinamentos-obrigatorios; Figma 549:1319), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (obrigatório para o setor,
conclusão mais recente, situação em dia, vencendo, vencido e pendente, matriz, indicadores, vencimentos, validade
legível, validações e "Meus treinamentos") e as telas (matriz com filtro, catálogo vazio com o sugerido, novo e
editar treinamento, registrar uma turma, vencimentos, acesso e a tela da pessoa). Vídeo (change treinamento-em-video):
o vídeo pelo link (Google Drive ou YouTube), o mínimo assistido, a duração lida do Drive ou da prévia do YouTube ao
salvar e "Concluir treinamento" só liberado depois do mínimo. O Google Drive também é simulado.

Uso (na raiz do repositório):
    python tools/testar_treinamentos.py
"""

import copy
import html as html_lib
import logging
import re
import sys
from datetime import date, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import drive_video  # noqa: E402
import treinamentos_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
chamadas: list[tuple] = []
estado: dict = {}


def iso(dias: int) -> str:
    return (HOJE + timedelta(days=dias)).isoformat()


TREINAMENTOS = [
    {"id": 1, "nome": "Orientação sobre assédio e violência no trabalho", "categoria": "legal", "carga_horas": 2, "validade_meses": 12, "obrigatorio": True,
     "publico": "todos", "departamento_ids": None, "ativo": True},
    {"id": 2, "nome": "NR-35 Trabalho em altura", "categoria": "seguranca", "carga_horas": 8, "validade_meses": 24, "obrigatorio": True,
     "publico": "departamentos", "departamento_ids": ",3,", "ativo": True},
    {"id": 3, "nome": "Excel avançado", "categoria": "desenvolvimento", "carga_horas": 16, "validade_meses": 0, "obrigatorio": False, "publico": "todos", "ativo": True},
]
PESSOAS = [{"id": 8, "nome": "Leonardo dos Santos", "departamento_id": 1}, {"id": 20, "nome": "Bruno Melo", "departamento_id": 2},
           {"id": 21, "nome": "Carla Dias", "departamento_id": 3}]
CONCLUSOES = [{"id": 1, "treinamento_id": 1, "colaborador_id": 8, "concluido_em": iso(-100), "valido_ate": iso(265)},
              {"id": 2, "treinamento_id": 1, "colaborador_id": 20, "concluido_em": iso(-400), "valido_ate": iso(-35)},
              {"id": 3, "treinamento_id": 1, "colaborador_id": 21, "concluido_em": iso(-350), "valido_ate": iso(15)},
              {"id": 4, "treinamento_id": 1, "colaborador_id": 20, "concluido_em": iso(-800), "valido_ate": iso(-435)}]
DADOS = {"hoje": HOJE.isoformat(), "treinamentos": TREINAMENTOS, "conclusoes": CONCLUSOES, "pessoas": PESSOAS,
         "departamentos": [{"id": 1, "nome": "Recursos Humanos"}, {"id": 2, "nome": "TI"}, {"id": 3, "nome": "Operações"}]}
MEUS = {"hoje": HOJE.isoformat(), "obrigatorios": [{"id": 1, "nome": "Orientação sobre assédio e violência no trabalho", "validade_meses": 12},
                                                   {"id": 4, "nome": "Integração de segurança (NR-1)", "validade_meses": 0}],
        "conclusoes": [{"treinamento_id": 1, "nome": "Orientação sobre assédio e violência no trabalho", "carga_horas": 2, "concluido_em": iso(-100),
                        "valido_ate": iso(265), "instrutor": "SESMT", "certificado_url": "https://certificados.exemplo/abc"}]}

api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": True, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.treinamentos = lambda token: copy.deepcopy(estado.get("dados", DADOS))
api_client.salvar_treinamento = lambda token, dados, tid=None: chamadas.append(("salvar", tid, dados)) or {"sucesso": True}
api_client.registrar_conclusao_treinamento = lambda token, *a: chamadas.append(("registrar", *a)) or {"registradas": 2, "puladas": 1, "valido_ate": iso(365)}
api_client.meus_treinamentos = lambda token: copy.deepcopy(estado.get("meus", MEUS))
api_client.progresso_treinamento = lambda token, *a: chamadas.append(("progresso", *a)) or {"segundos_vistos": a[1], "duracao": 1440}
api_client.concluir_treinamento = lambda token, tid: chamadas.append(("concluir", tid)) or {"valido_ate": iso(365)}
# Google Drive simulado: a chave nos secrets e a duração do vídeo.
drive_video.chave_api = lambda: estado.get("chave", "chave-de-teste")
drive_video.duracao_video = lambda vid, chave: chamadas.append(("drive", vid)) or 1440
ID_VIDEO = "1AbCdEfGhIjKlMnOpQrStUvWxYz_-123"
ID_YT = "dQw4w9WgXcQ"
MEUS_VIDEO = dict(MEUS, obrigatorios=[dict(MEUS["obrigatorios"][1], video_drive_id=ID_VIDEO, video_duracao=1440, video_percentual_minimo=95)],
                  progressos=[{"treinamento_id": 4, "segundos_vistos": 893, "posicao": 893}])

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


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def chaves(at: AppTest) -> set:
    return {b.key for b in at.button}


def aviso(at: AppTest) -> str:
    return str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else [t.value for t in at.toast])


def app(pagina: str = "treinamentos", perfil: str = "RH", colaborador_id=8, **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 10, "nome": "Leonardo dos Santos", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": colaborador_id}
    at.session_state["sessao_validada"] = True
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
    return at.run()


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


def aba(at: AppTest, nome: str) -> AppTest:
    at.button_group(key="tr_aba").set_value(nome)
    return at.run()


print("\nRegras (treinamentos_modelo.py)")
conferir(m.obrigatorio_para(TREINAMENTOS[0], 2) and m.obrigatorio_para(TREINAMENTOS[1], 3) and not m.obrigatorio_para(TREINAMENTOS[1], 2)
         and not m.obrigatorio_para(TREINAMENTOS[2], 1), "obrigatório para todos, para o setor, e opcional")
conferir(m.ultima(CONCLUSOES, 1, 20)["id"] == 2, "vale a conclusão mais recente")
conferir(m.situacao(None, HOJE)[0] == "pendente" and m.situacao({"valido_ate": None}, HOJE) == ("em_dia", "Em dia", "ok")
         and m.situacao({"valido_ate": iso(-1)}, HOJE)[0] == "vencido" and m.situacao({"valido_ate": iso(30)}, HOJE)[0] == "vencendo"
         and m.situacao({"valido_ate": iso(31)}, HOJE)[0] == "em_dia", "situação: pendente, sem validade, vencido, vencendo (30 dias) e em dia")
mat = m.matriz(DADOS)
celulas = {l["nome"]: l["celulas"] for l in mat["linhas"]}
conferir([t["id"] for t in mat["colunas"]] == [1, 2] and celulas["Bruno Melo"][2] is None and celulas["Carla Dias"][2][0] == "pendente"
         and celulas["Bruno Melo"][1][0] == "vencido" and celulas["Carla Dias"][1][0] == "vencendo", "matriz: só obrigatórios e célula vazia fora do setor")
conferir(m.indicadores(mat) == [("Em dia", "50%", "verde"), ("Vencendo em 30 dias", "1", "ambar"), ("Vencidos", "1", "negativo"), ("Pendentes", "1", "")],
         "indicadores")
conferir([(v["pessoa"], v["ordem"]) for v in m.vencimentos(mat)] == [("Bruno Melo", 0), ("Carla Dias", 1)], "vencimentos: vencidos primeiro")
conferir(m.validade_legivel(0) == "Sem validade" and m.validade_legivel(12) == "Anual" and m.validade_legivel(24) == "A cada 2 anos" and m.validade_legivel(6) == "A cada 6 meses"
         and m.ids_departamentos([3, 1, 3]) == ",1,3,", "validade legível e lista de departamentos")
conferir("departamento" in m.validar_treinamento("NR-10", "seguranca", 24, 8, True, "departamentos", []) and "categoria" in m.validar_treinamento("NR-10", None, 0, 0, True, "todos", [])
         and "futuro" in m.validar_conclusao(1, [8], HOJE + timedelta(days=1), HOJE) and "http" in m.validar_conclusao(1, [8], HOJE, HOJE, "certificado.pdf")
         and m.validar_conclusao(1, [8], HOJE, HOJE, "https://x") is None, "validações")
mm = m.meus(MEUS)
conferir([o["nome"] for o in mm["obrigatorios"]] == ["Integração de segurança (NR-1)", "Orientação sobre assédio e violência no trabalho"] and mm["obrigatorios"][0]["rotulo"] == "Pendente"
         and "SESMT" in mm["historico"][0]["titulo"], "meus treinamentos: pendente primeiro e histórico")
conferir(m.video_do_link(f"https://drive.google.com/file/d/{ID_VIDEO}/view?usp=sharing") == ("drive", ID_VIDEO)
         and m.video_do_link(f"https://drive.google.com/open?id={ID_VIDEO}") == ("drive", ID_VIDEO) and m.video_do_link(ID_VIDEO) is None
         and m.video_do_link("") is None and m.video_do_link("https://exemplo.com/drive.google.com/file/d/x") is None, "vídeo: link do Drive")
conferir(all(m.video_do_link(l) == ("youtube", ID_YT) for l in (f"https://www.youtube.com/watch?v={ID_YT}&t=30", f"https://youtu.be/{ID_YT}?si=abc",
                                                                f"youtube.com/shorts/{ID_YT}", f"https://m.youtube.com/watch?v={ID_YT}", f"https://www.youtube.com/embed/{ID_YT}"))
         and m.video_do_link("https://www.youtube.com/watch?v=curto") is None and m.link_video("youtube", ID_YT) == f"https://www.youtube.com/watch?v={ID_YT}"
         and m.link_video("drive", ID_VIDEO).startswith("https://drive.google.com/file/d/"), "vídeo: link do YouTube (watch, youtu.be, shorts, embed)")
conferir("inválido" in m.validar_video("video.mp4", 95) and "50%" in m.validar_video("", 40) and m.validar_video(f"https://drive.google.com/file/d/{ID_VIDEO}/view", 95) is None,
         "vídeo: validações do link e do mínimo")
conferir(m.percentual_visto(893, 1440) == 62 and not m.pode_concluir(1367, 1440, 95) and m.pode_concluir(1368, 1440, 95) and not m.pode_concluir(10, 0, 95)
         and m.duracao_legivel(1440) == "24 min" and m.duracao_legivel(4500) == "1 h 15 min", "vídeo: percentual, mínimo para concluir (a conta do backend) e duração")
mv = m.meus(MEUS_VIDEO)
conferir(mv["videos"][0]["vistos"] == 893 and mv["videos"][0]["minimo"] == 95 and "Vídeo de 24 min" in mv["videos"][0]["detalhe"]
         and mv["obrigatorios"][0]["nome"].endswith("· vídeo") and m.meus(MEUS)["videos"] == [], "vídeo: meus treinamentos com o progresso")

print("\nTreinamentos do RH (Figma 549:1321)")
at = app()
t = texto(at)
conferir("Treinamentos obrigatórios: quem fez, quem está vencendo e quem falta" in t and "50%" in t and "Bruno Melo" in t and "Vencido" in t
         and "Célula vazia" in t, "matriz com indicadores")
at.selectbox(key="tr_f_dep").set_value(3)
at = at.run()
conferir("Carla Dias" in texto(at) and "Bruno Melo" not in texto(at), "filtro de departamento")
at = aba(app(dados=dict(DADOS, treinamentos=[], conclusoes=[])), "Catálogo")
conferir("Catálogo vazio" in texto(at), "catálogo vazio oferece o sugerido")
at = clicar(at, "tr_sugeridos")
conferir(len([c for c in chamadas if c[0] == "salvar"]) == len(m.SUGERIDOS) and "sugeridos criados" in aviso(at), "cria o catálogo sugerido")
at = aba(app(), "Catálogo")
conferir("A cada 2 anos" in texto(at) and "Operações" in texto(at) and "Opcional" in texto(at), "catálogo com validade e público")
at = clicar(at, "tr_editar_2")
at.toggle(key="tr_form_ativo").set_value(False)
at = clicar(at.run(), "tr_form_ok")
conferir(any(c[0] == "salvar" and c[1] == 2 and c[2]["ativo"] is False and c[2]["departamento_ids"] == ",3," for c in chamadas), "editar e desativar mantendo o setor")
at = clicar(app(), "tr_novo")
at.selectbox(key="tr_form_cat").set_value("seguranca")
at.text_input(key="tr_form_nome").set_value("NR-10 Eletricidade")
at.radio(key="tr_form_publico").set_value("departamentos")
at = at.run()
at = clicar(at, "tr_form_ok")
conferir("pelo menos um departamento" in texto(at) and not any(c[0] == "salvar" for c in chamadas), "obrigatório para setores exige um setor")
at.multiselect(key="tr_form_deps").set_value([2])
at = clicar(at.run(), "tr_form_ok")
conferir(any(c[0] == "salvar" and c[1] is None and c[2]["departamento_ids"] == ",2," for c in chamadas), "novo treinamento para um setor")
at = clicar(app(), "tr_novo")
at.selectbox(key="tr_form_cat").set_value("legal")
at.text_input(key="tr_form_nome").set_value("Orientação sobre assédio")
at.text_input(key="tr_form_video").set_value("https://exemplo.com/video.mp4")
at = clicar(at.run(), "tr_form_ok")
conferir("Link do vídeo inválido" in texto(at) and not any(c[0] in ("salvar", "drive") for c in chamadas), "vídeo: link que não é do Drive nem do YouTube é recusado")
at.text_input(key="tr_form_video").set_value(f"https://drive.google.com/file/d/{ID_VIDEO}/view?usp=sharing")
at = at.run()
at.number_input(key="tr_form_pct").set_value(90)
at = clicar(at.run(), "tr_form_ok")
conferir(("drive", ID_VIDEO) in chamadas and any(c[0] == "salvar" and c[2]["video_drive_id"] == ID_VIDEO and c[2]["video_duracao"] == 1440
                                                 and c[2]["video_percentual_minimo"] == 90 for c in chamadas), "vídeo: lê a duração no Drive e salva id, duração e mínimo")
at = clicar(app(chave=None), "tr_novo")
at.selectbox(key="tr_form_cat").set_value("legal")
at.text_input(key="tr_form_nome").set_value("Orientação sobre assédio")
at.text_input(key="tr_form_video").set_value(f"https://drive.google.com/file/d/{ID_VIDEO}/view")
at = clicar(at.run(), "tr_form_ok")
conferir("Falta configurar o Google Drive" in texto(at) and not any(c[0] == "salvar" for c in chamadas), "vídeo: Drive sem a chave da API, não salva e explica")
at.text_input(key="tr_form_video").set_value(f"https://youtu.be/{ID_YT}")
at = clicar(at.run(), "tr_form_ok")
conferir(not at.exception and "Espere a prévia do YouTube" in texto(at) and not any(c[0] == "salvar" for c in chamadas),
         "vídeo: YouTube sem a duração da prévia ainda, não salva")
at.session_state[f"tr_yt_dur_{ID_YT}"] = 212
at = clicar(at.run(), "tr_form_ok")
conferir(any(c[0] == "salvar" and c[2]["video_fonte"] == "youtube" and c[2]["video_drive_id"] == ID_YT and c[2]["video_duracao"] == 212 for c in chamadas)
         and not any(c[0] == "drive" for c in chamadas), "vídeo: YouTube salva com a duração da prévia, sem chave e sem chamar o Drive")
at = aba(app(), "Registrar conclusão")
at.selectbox(key="tr_reg_treino").set_value(1)
at.multiselect(key="tr_reg_pessoas").set_value([20, 21])
at.text_input(key="tr_reg_instrutor").set_value("SESMT")
at = clicar(at.run(), "tr_reg_ok")
conferir(any(c[0] == "registrar" and c[1] == 1 and c[2] == [20, 21] and c[4] == "SESMT" for c in chamadas) and "2 conclusões registradas" in aviso(at)
         and "puladas" in aviso(at), "registra uma turma")
at = aba(app(), "Vencimentos")
conferir("Bruno Melo · Orientação sobre assédio" in texto(at) and "Carla Dias" in texto(at), "vencimentos")
at = app(perfil="GESTOR")
conferir("só do RH" in texto(at), "quem não é RH nem Admin: sem acesso")

print("\nMeus treinamentos (Figma 550:1415)")
at = app("meus-treinamentos", perfil="COLABORADOR")
t = texto(at)
conferir("Obrigatórios para você" in t and "Pendente" in t and "Em dia" in t and "Ver certificado" in t, "obrigatórios, situação e certificado")
at = app("meus-treinamentos", perfil="COLABORADOR", meus={"hoje": HOJE.isoformat(), "obrigatorios": [], "conclusoes": []})
conferir("Nenhum treinamento obrigatório para você agora." in texto(at) and "Nenhum treinamento registrado ainda." in texto(at) and not at.exception,
         "sem obrigatórios nem histórico: mensagens, sem erro")
conferir(not at.exception and "Você assistiu" not in texto(at) and "mt_concluir_4" not in chaves(at), "sem vídeo: sem o player")
at = app("meus-treinamentos", perfil="COLABORADOR", meus=MEUS_VIDEO)
t = texto(at)
conferir(not at.exception and "Integração de segurança (NR-1)" in t and "Vídeo de 24 min" in t and "Trechos pulados não contam" in t
         and at.button(key="mt_concluir_4").disabled, "vídeo: player e Concluir travado antes do mínimo (62%)")
at.session_state["mt_vistos_4"] = 1400
at = at.run()
conferir(not at.button(key="mt_concluir_4").disabled, "vídeo: Concluir liberado depois de 95%")
at = clicar(at, "mt_concluir_4")
conferir(("concluir", 4) in chamadas and "Treinamento concluído" in aviso(at), "vídeo: conclui pelo endpoint da pessoa")
at = app("meus-treinamentos", perfil="COLABORADOR", meus=MEUS_VIDEO, chave=None)
conferir("falta configurar o Google Drive" in texto(at) and "mt_concluir_4" not in chaves(at), "vídeo: sem a chave da API, aviso no lugar do player")
yt = dict(MEUS_VIDEO, obrigatorios=[dict(MEUS_VIDEO["obrigatorios"][0], video_drive_id=ID_YT, video_fonte="youtube")])
at = app("meus-treinamentos", perfil="COLABORADOR", meus=yt, chave=None)
conferir(not at.exception and "falta configurar" not in texto(at) and at.button(key="mt_concluir_4").disabled, "vídeo: YouTube toca sem a chave do Google")
at = app("meus-treinamentos", perfil="COLABORADOR", colaborador_id=None)
conferir("não tem ficha" in texto(at), "conta sem ficha: aviso")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
