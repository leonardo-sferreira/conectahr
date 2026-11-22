"""Testes dos treinamentos obrigatórios (change treinamentos-obrigatorios; Figma 549:1319), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (obrigatório para o setor,
conclusão mais recente, situação em dia, vencendo, vencido e pendente, matriz, indicadores, vencimentos, validade
legível, validações e "Meus treinamentos") e as telas (matriz com filtro, catálogo vazio com o sugerido, novo e
editar treinamento, registrar uma turma, vencimentos, acesso e a tela da pessoa). Vídeo (change treinamento-em-video):
o vídeo pelo link do YouTube (o do Google Drive é recusado desde a change remover-video-drive), o mínimo assistido, a
duração lida da prévia do YouTube ao salvar e "Concluir treinamento" só liberado depois do mínimo. Cards (change
cards-de-treinamentos): situação e filtro de cada card, capa automática, corte da descrição, links de leitura, validações
do conteúdo e da capa, a grade com os filtros, o detalhe com "Voltar" mantendo o filtro, a leitura que só conclui depois
de abrir e confirmar, e o modal do RH com o tipo de conteúdo.

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

CAPA = "1b4e28ba-2fa1-11d2-883f-0016d3cca427.webp"
CARDS = [
    {"id": 1, "nome": "Orientação sobre assédio e violência no trabalho", "descricao": "Lei 14.457/2022.", "categoria": "legal", "carga_horas": 2, "validade_meses": 12,
     "obrigatorio": True, "conteudo_tipo": "video"},
    {"id": 4, "nome": "Integração de segurança (NR-1)", "descricao": "Riscos do ambiente e como agir.", "categoria": "seguranca", "carga_horas": 1, "validade_meses": 0,
     "obrigatorio": True, "conteudo_tipo": "pdf", "tem_arquivo": True},
    {"id": 6, "nome": "LGPD no dia a dia", "descricao": "Dados pessoais com segurança.", "categoria": "compliance", "carga_horas": 2, "validade_meses": 12,
     "obrigatorio": True, "conteudo_tipo": "apresentacao", "conteudo_url": "https://docs.google.com/presentation/d/1AbCdEfGhIjKlMn/edit", "capa_path": CAPA},
    {"id": 5, "nome": "Excel avançado", "descricao": "", "categoria": "desenvolvimento", "carga_horas": 16, "validade_meses": 0, "obrigatorio": False,
     "conteudo_tipo": "video", "video_drive_id": "dQw4w9WgXcQ", "video_fonte": "youtube", "video_duracao": 600},
]
MEUS["cards"] = CARDS
MEUS["capas"] = [{"caminho": CAPA, "url": "https://armazenamento.exemplo/assinado/capa.webp?token=y"}]
MEUS["progressos"] = [{"treinamento_id": 6, "aberto_em": 1700000000000}]

api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": True, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.meu_humor = lambda token: {"ciclo": 0, "respondeu": True}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.treinamentos = lambda token: copy.deepcopy(estado.get("dados", DADOS))
api_client.salvar_treinamento = lambda token, dados, tid=None: chamadas.append(("salvar", tid, dados)) or {"sucesso": True}
api_client.registrar_conclusao_treinamento = lambda token, *a: chamadas.append(("registrar", *a)) or {"registradas": 2, "puladas": 1, "valido_ate": iso(365)}
def _meus_treinamentos(token):
    chamadas.append(("meus",))
    if estado.get("erro_meus"):
        raise ApiError(estado["erro_meus"], 500)
    return copy.deepcopy(estado.get("meus", MEUS))


def _conteudo_treinamento(token, tid):
    chamadas.append(("conteudo", tid))
    if estado.get("erro_conteudo"):
        raise ApiError(estado["erro_conteudo"], 404)
    return copy.deepcopy(estado.get("conteudo", {"tipo": "pdf", "arquivo": True, "url": "https://armazenamento.exemplo/assinado/nr-1.pdf?token=x"}))


api_client.meus_treinamentos = _meus_treinamentos
api_client.progresso_treinamento = lambda token, *a: chamadas.append(("progresso", *a)) or {"segundos_vistos": a[1], "duracao": 1440}
api_client.concluir_treinamento = lambda token, tid, confirmo_leitura=False: chamadas.append(("concluir", tid, confirmo_leitura)) or {"valido_ate": iso(365)}
api_client.conteudo_treinamento = _conteudo_treinamento
api_client.abrir_treinamento = lambda token, tid: chamadas.append(("abrir", tid)) or {"aberto_em": 1}
ID_VIDEO = "1AbCdEfGhIjKlMnOpQrStUvWxYz_-123"
ID_YT = "dQw4w9WgXcQ"
MEUS_VIDEO = dict(MEUS, obrigatorios=[dict(MEUS["obrigatorios"][1], video_drive_id=ID_VIDEO, video_duracao=1440, video_percentual_minimo=95)],
                  cards=[dict(CARDS[1], conteudo_tipo="video", tem_arquivo=False, video_drive_id=ID_YT, video_fonte="youtube", video_duracao=1440,
                              video_percentual_minimo=95)],
                  progressos=[{"treinamento_id": 4, "segundos_vistos": 893, "posicao": 893}])
MEUS_VIDEO_DRIVE = dict(MEUS_VIDEO, cards=[dict(MEUS_VIDEO["cards"][0], video_drive_id=ID_VIDEO, video_fonte="drive")])

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
    at.session_state["menu_grupos"] = {"RH": True, "Equipe": True, "Admin": True}  # grupos do menu abertos (o fechado é testado em testar_menu)
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
conferir("inválido" in m.validar_video("video.mp4", 95) and "50%" in m.validar_video("", 40) and "Google Drive" in m.validar_video(f"https://drive.google.com/file/d/{ID_VIDEO}/view", 95)
         and m.validar_video(f"https://youtu.be/{ID_YT}", 95) is None,
         "vídeo: validações do link e do mínimo")
conferir(m.percentual_visto(893, 1440) == 62 and not m.pode_concluir(1367, 1440, 95) and m.pode_concluir(1368, 1440, 95) and not m.pode_concluir(10, 0, 95)
         and m.duracao_legivel(1440) == "24 min" and m.duracao_legivel(4500) == "1 h 15 min", "vídeo: percentual, mínimo para concluir (a conta do backend) e duração")
mv = m.meus(MEUS_VIDEO)
conferir(mv["videos"][0]["vistos"] == 893 and mv["videos"][0]["minimo"] == 95 and "Vídeo de 24 min" in mv["videos"][0]["detalhe"]
         and mv["obrigatorios"][0]["nome"].endswith("· vídeo") and m.meus(MEUS)["videos"] == [], "vídeo: meus treinamentos com o progresso")

print("\nCards (treinamentos_modelo.py; change cards-de-treinamentos)")
lc = m.cards(MEUS)
por_filtro = {f: [c["id"] for c in lc if c["situacao"]["filtro"] == f] for f in m.FILTROS}
conferir(por_filtro == {"pendentes": [4, 5], "andamento": [6], "concluidos": [1]} and m.contagem(lc) == {"pendentes": 2, "andamento": 1, "concluidos": 1}
         and m.filtro_inicial(lc) == "pendentes", "cards: filtros (pendente e opcional, leitura aberta, em dia) e o primeiro filtro com itens")
sit = {c["id"]: c["situacao"] for c in lc}
conferir(sit[4]["rotulo"] == "Pendente" and sit[5]["rotulo"] == "Opcional" and sit[6]["rotulo"] == "Em andamento" and sit[1]["filtro"] == "concluidos",
         "cards: rótulos de situação")
conferir(m.filtro_inicial([c for c in lc if c["id"] == 1]) == "concluidos" and m.filtro_inicial([]) == "pendentes", "cards: filtro inicial sem pendentes")
venc = m.situacao_card(CARDS[0], [{"treinamento_id": 1, "valido_ate": iso(-3)}], {"segundos_vistos": 30}, HOJE)
conferir(venc["filtro"] == "andamento" and venc["rotulo"].startswith("Vencido") and venc["tom"] == "err", "cards: vencido e começado fica em andamento com o selo de vencido")
op = m.situacao_card(CARDS[3], [{"treinamento_id": 5, "valido_ate": None}], None, HOJE)
conferir(op["filtro"] == "concluidos" and op["rotulo"] == "Concluído", "cards: opcional concluído")
capas = {c["id"]: c["capa"] for c in lc}
conferir(m.mapa_capas(MEUS["capas"]) == {CAPA: "https://armazenamento.exemplo/assinado/capa.webp?token=y"}
         and m.mapa_capas([{"caminho": "x.webp"}, "lixo", None]) == {} and m.mapa_capas(None) == {}, "cards: capas assinadas (lista do backend) viram mapa")
conferir(capas[6] == "https://armazenamento.exemplo/assinado/capa.webp?token=y" and capas[5] == "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg" and capas[4] is None
         and m.capa({"conteudo_tipo": "pdf", "conteudo_url": "https://drive.google.com/file/d/1AbCdEfGh/view"}, {}) == "https://drive.google.com/thumbnail?id=1AbCdEfGh&sz=w640"
         and m.capa({"video_drive_id": ID_VIDEO}, {}) == f"https://drive.google.com/thumbnail?id={ID_VIDEO}&sz=w640"
         and m.capa({"capa_path": CAPA, "video_drive_id": ID_YT, "video_fonte": "youtube"}, {}) == f"https://img.youtube.com/vi/{ID_YT}/hqdefault.jpg",
         "cards: capa enviada, miniatura do YouTube, do Drive, ou nenhuma (ilustração)")
conferir(m.capa_padrao("seguranca") == "app/static/capas/seguranca.svg" and m.capa_padrao(None) == "app/static/capas/desenvolvimento.svg"
         and all((RAIZ / "frontend/static/capas" / f"{c}.svg").exists() for c in m.CATEGORIAS), "cards: ilustração de cada categoria existe")
longo = "palavra " * 40
conferir(m.resumo(longo).endswith("…") and len(m.resumo(longo)) <= 171 and m.resumo("  curta   ") == "curta" and m.resumo(None) == "", "cards: corte da descrição")
conferir({c["id"]: c["tipo_rotulo"] for c in lc} == {1: "Vídeo", 4: "Leitura (PDF)", 6: "Apresentação", 5: "Vídeo · 10 min"}, "cards: tipo de conteúdo")
conferir(next(c for c in lc if c["id"] == 4)["com_conteudo"] and not next(c for c in lc if c["id"] == 1)["com_conteudo"]
         and next(c for c in lc if c["id"] == 5)["video"]["duracao"] == 600, "cards: com conteúdo (vídeo sem link não tem; PDF com arquivo tem)")
conferir(m.link_leitura("pdf", "https://drive.google.com/file/d/1AbCdEfGhIj/view?usp=sharing") == "https://drive.google.com/file/d/1AbCdEfGhIj/view"
         and m.link_leitura("pdf", "https://docs.google.com/presentation/d/1AbCdEfGhIjKl/edit") is None
         and m.link_leitura("apresentacao", "https://docs.google.com/presentation/d/1AbCdEfGhIjKl/edit#slide=id.p") == "https://docs.google.com/presentation/d/1AbCdEfGhIjKl/edit"
         and m.link_leitura("apresentacao", "https://drive.google.com/file/d/1AbCdEfGhIj/view") == "https://drive.google.com/file/d/1AbCdEfGhIj/view"
         and m.link_leitura("apresentacao", "https://exemplo.com/presentation/d/1AbCdEfGhIjKl/edit") is None
         and m.link_leitura("pdf", "https://drive.google.com/file/d/1Ab CdE/view") is None and m.link_leitura("pdf", "") is None,
         "cards: links aceitos (Drive para PDF; Slides ou Drive para apresentação; outro site não)")
conferir(m.url_embutida("https://docs.google.com/presentation/d/1AbCdEfGhIjKl/edit") == "https://docs.google.com/presentation/d/1AbCdEfGhIjKl/embed"
         and m.url_embutida("https://drive.google.com/file/d/1AbCdEfGhIj/view") == "https://drive.google.com/file/d/1AbCdEfGhIj/preview"
         and m.url_embutida("https://armazenamento.exemplo/x.pdf?t=1") == "https://armazenamento.exemplo/x.pdf?t=1" and m.url_embutida(None) is None,
         "cards: endereço embutido (Slides /embed, Drive /preview, PDF assinado como está)")
conferir(m.validar_conteudo("video", None, None, 0) is None and "Envie o arquivo PDF" in m.validar_conteudo("pdf", "", None, 0)
         and m.validar_conteudo("pdf", "", None, 0, tem_arquivo_salvo=True) is None and "um dos dois" in m.validar_conteudo("pdf", "https://drive.google.com/file/d/x/view", "a.pdf", 10)
         and "inválido" in m.validar_conteudo("pdf", "https://exemplo.com/a.pdf", None, 0) and "Slides" in m.validar_conteudo("apresentacao", "https://exemplo.com/a", None, 0)
         and "20 MB" in m.validar_conteudo("pdf", None, "a.pdf", m.TAMANHO_PDF + 1) and "PDF" in m.validar_conteudo("pdf", None, "a.docx", 10)
         and "vazio" in m.validar_conteudo("pdf", None, "a.pdf", 0) and m.validar_conteudo("pdf", None, "A.PDF", 10) is None,
         "cards: validações do conteúdo (arquivo ou link, um dos dois, host, tamanho e extensão)")
conferir("JPG" in m.validar_capa("capa.gif", 10) and "5 MB" in m.validar_capa("capa.png", m.TAMANHO_CAPA + 1) and m.validar_capa("capa.JPEG", 10) is None
         and "vazio" in m.validar_capa("capa.webp", 0), "cards: validações da capa")
import io  # noqa: E402

from PIL import Image  # noqa: E402

_png = io.BytesIO()
_img = Image.new("RGB", (1200, 1200), "orange")
_exif = Image.Exif()
_exif[0x010F] = "Camera de teste"
_img.save(_png, format="JPEG", exif=_exif)
_saida = m.tratar_capa(_png.getvalue())
_aberta = Image.open(io.BytesIO(_saida))
conferir(_aberta.size == (640, 360) and _aberta.format == "WEBP" and not _aberta.getexif(), "cards: capa reduzida a 640 × 360 em WebP, sem metadados")
_grande = io.BytesIO()
Image.new("1", (9000, 6000)).save(_grande, format="PNG")
try:
    m.tratar_capa(_grande.getvalue())
    conferir(False, "cards: capa com pixels demais é recusada antes de decodificar")
except ValueError as _e:
    conferir("grande demais" in str(_e) and len(_grande.getvalue()) < m.TAMANHO_CAPA, "cards: capa com pixels demais é recusada antes de decodificar")
try:
    m.tratar_capa(b"isto nao e uma imagem")
    conferir(False, "cards: arquivo que não é imagem é recusado")
except ValueError:
    conferir(True, "cards: arquivo que não é imagem é recusado")

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
conferir("Link do vídeo inválido" in texto(at) and not any(c[0] == "salvar" for c in chamadas), "vídeo: link que não é do YouTube é recusado")
at.text_input(key="tr_form_video").set_value(f"https://drive.google.com/file/d/{ID_VIDEO}/view?usp=sharing")
at = clicar(at.run(), "tr_form_ok")
conferir("não usa mais vídeos do Google Drive" in texto(at) and not any(c[0] == "salvar" for c in chamadas),
         "vídeo: link do Google Drive é recusado, com a orientação de usar o YouTube")
at.text_input(key="tr_form_video").set_value(f"https://youtu.be/{ID_YT}")
at = clicar(at.run(), "tr_form_ok")
conferir(not at.exception and "Espere a prévia do YouTube" in texto(at) and not any(c[0] == "salvar" for c in chamadas),
         "vídeo: YouTube sem a duração da prévia ainda, não salva")
at.session_state[f"tr_yt_dur_{ID_YT}"] = 212
at = clicar(at.run(), "tr_form_ok")
conferir(any(c[0] == "salvar" and c[2]["video_fonte"] == "youtube" and c[2]["video_drive_id"] == ID_YT and c[2]["video_duracao"] == 212 for c in chamadas)
         , "vídeo: YouTube salva com a duração da prévia, sem chave")
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

print("\nMeus treinamentos em cards (Figma 633:1470)")
at = app("meus-treinamentos", perfil="COLABORADOR")
t = texto(at)
conferir(not at.exception and at.button_group(key="mt_filtro").options == ["Pendentes (2)", "Em andamento (1)", "Concluídos (1)"],
         "grade: filtros com a contagem")
conferir(at.button_group(key="mt_filtro").value == "pendentes" and {"mt_abrir_4", "mt_abrir_5"} <= chaves(at) and "mt_abrir_6" not in chaves(at)
         and "Integração de segurança (NR-1)" in t and "Excel avançado" in t and "Leitura (PDF)" in t and "Opcional" in t, "grade: abre em Pendentes com os cards do filtro")
htmls = " ".join(str(e.value) for e in at.get("html"))
conferir("app/static/capas/seguranca.svg" in htmls and "img.youtube.com/vi/dQw4w9WgXcQ" in htmls and 'aria-label="Capa de Excel avançado"' in htmls
         and "Abrir: Integração de segurança (NR-1)" in [b.label for b in at.button], "grade: capa com a ilustração por baixo, rótulo acessível e botão do card")
conferir("Histórico" in t and "Ver certificado" in t and "SESMT" in t, "grade: histórico com o certificado")
at.button_group(key="mt_filtro").set_value("andamento")
at = at.run()
conferir({"mt_abrir_6"} == {k for k in chaves(at) if str(k).startswith("mt_abrir_")} and "capa.webp" in " ".join(str(e.value) for e in at.get("html")),
         "grade: Em andamento mostra a apresentação aberta, com a capa enviada")
at = clicar(at, "mt_abrir_6")
t = texto(at)
conferir(not at.exception and "LGPD no dia a dia" in t and "Dados pessoais com segurança." in t and ("conteudo", 6) in chamadas
         and "Arquivo no Google Drive" not in t
         and not any(c[0] == "abrir" for c in chamadas), "detalhe: apresentação já aberta busca o conteúdo sem marcar a abertura de novo")
conferir(any("Voltar para Em andamento" in b.label for b in at.button) and at.button(key="mt_concluir_6").disabled
         and not at.checkbox(key="mt_li_6").disabled, "detalhe: Voltar com o filtro e Concluir travado até confirmar")
at.checkbox(key="mt_li_6").check()
at = at.run()
conferir(not at.button(key="mt_concluir_6").disabled, "detalhe: confirmar libera Concluir")
at = clicar(at, "mt_concluir_6")
conferir(("concluir", 6, True) in chamadas and "Treinamento concluído" in aviso(at), "detalhe: conclui a leitura com a confirmação")
at = app("meus-treinamentos", perfil="COLABORADOR")
at.button_group(key="mt_filtro").set_value("andamento")
at = clicar(at.run(), "mt_abrir_6")
at = clicar(at, "mt_btn_voltar")
conferir(at.button_group(key="mt_filtro").value == "andamento" and "mt_abrir_6" in chaves(at) and "mt_btn_voltar" not in chaves(at),
         "Voltar: a grade volta no filtro Em andamento")
at = clicar(app("meus-treinamentos", perfil="COLABORADOR"), "mt_abrir_4")
conferir(("conteudo", 4) in chamadas and ("abrir", 4) in chamadas and not at.checkbox(key="mt_li_4").disabled and at.button(key="mt_concluir_4").disabled
         and "PDF do treinamento" in texto(at) and at.get("iframe"), "detalhe: PDF do bucket (arquivo: true) marca a abertura e mostra o visualizador")
chamadas.clear()
at = at.run()
# A primeira abertura descarta os dados guardados (a grade passa a "Em andamento"): a interação seguinte os busca uma vez.
conferir(chamadas == [("meus",)], "detalhe: depois da primeira abertura, busca os dados uma vez")
chamadas.clear()
at = at.run()
conferir(("abrir", 4) not in chamadas and ("conteudo", 4) not in chamadas and ("meus",) not in chamadas,
         "detalhe: não repete a abertura, nem pede outro endereço ou os dados a cada interação")
sem_arquivo = dict(MEUS, cards=[dict(CARDS[1], tem_arquivo=False)])
at = clicar(app("meus-treinamentos", perfil="COLABORADOR", meus=sem_arquivo), "mt_abrir_4")
conferir("ainda não anexou o conteúdo" in texto(at) and not any(c[0] in ("conteudo", "abrir") for c in chamadas), "detalhe: leitura sem conteúdo avisa")
at = clicar(app("meus-treinamentos", perfil="COLABORADOR", erro_conteudo="Treinamento não encontrado."), "mt_abrir_4")
conferir(not at.exception and "Treinamento não encontrado." in texto(at) and "mt_concluir_4" not in chaves(at), "detalhe: erro ao buscar o conteúdo, sem conclusão")
at = clicar(app("meus-treinamentos", perfil="COLABORADOR", conteudo={"tipo": "pdf", "url": "<script>alert(1)</script>"}), "mt_abrir_4")
conferir(not at.exception and "Não foi possível abrir o conteúdo" in texto(at) and not at.get("iframe") and ("abrir", 4) not in chamadas,
         "detalhe: endereço que não é https não vai para o iframe nem marca a abertura")
at = app("meus-treinamentos", perfil="COLABORADOR", meus={"hoje": HOJE.isoformat(), "obrigatorios": [], "cards": [], "conclusoes": []})
conferir("Nenhum treinamento para você agora" in texto(at) and "Nenhum treinamento registrado ainda." in texto(at) and not at.exception,
         "vazio: estado vazio do Figma e histórico vazio, sem erro")
so_feitos = dict(MEUS, cards=[CARDS[0]])
at = app("meus-treinamentos", perfil="COLABORADOR", meus=so_feitos)
conferir(at.button_group(key="mt_filtro").value == "concluidos", "grade: sem pendentes, abre em Concluídos")
at.button_group(key="mt_filtro").set_value("pendentes")
at = at.run()
conferir("Nada pendente" in texto(at), "grade: filtro sem itens mostra a mensagem")
at = app("meus-treinamentos", perfil="COLABORADOR", erro_meus="Serviço indisponível.")
conferir(not at.exception and "Serviço indisponível." in texto(at), "erro: a mensagem da API")

print("\nVídeo no detalhe (change treinamento-em-video)")
at = app("meus-treinamentos", perfil="COLABORADOR", meus=MEUS_VIDEO)
conferir(at.button_group(key="mt_filtro").value == "andamento" and "Vídeo · 24 min" in texto(at), "vídeo começado fica em Em andamento")
at = clicar(at, "mt_abrir_4")
t = texto(at)
conferir(not at.exception and "Integração de segurança (NR-1)" in t and "Vídeo de 24 min" in t and "Trechos pulados não contam" in t
         and at.button(key="mt_concluir_4").disabled, "vídeo: player e Concluir travado antes do mínimo (62%)")
at.session_state["mt_vistos_4"] = 1400
at = at.run()
conferir(not at.button(key="mt_concluir_4").disabled, "vídeo: Concluir liberado depois de 95%")
at = clicar(at, "mt_concluir_4")
conferir(("concluir", 4, False) in chamadas and "Treinamento concluído" in aviso(at), "vídeo: conclui pelo endpoint da pessoa")
at = clicar(app("meus-treinamentos", perfil="COLABORADOR", meus=MEUS_VIDEO_DRIVE), "mt_abrir_4")
conferir(not at.exception and "estava no Google Drive" in texto(at) and "mt_concluir_4" not in chaves(at),
         "vídeo antigo do Google Drive: aviso para o RH trocar o link, sem player")
at = app("meus-treinamentos", perfil="COLABORADOR")
at.button_group(key="mt_filtro").set_value("concluidos")
at = clicar(at.run(), "mt_abrir_1")
conferir("não tem vídeo no ConectaRH" in texto(at) and "mt_concluir_1" not in chaves(at), "vídeo: treinamento sem vídeo explica que o RH registra")
at = app("meus-treinamentos", perfil="COLABORADOR", colaborador_id=None)
conferir("não tem ficha" in texto(at), "conta sem ficha: aviso")

print("\nModal do RH: tipo de conteúdo (Figma 636:1771)")
at = clicar(app(), "tr_novo")
conferir(at.button_group(key="tr_form_tipo").value == "video" and "tr_form_video" in {w.key for w in at.text_input}, "modal: novo vem como vídeo")
at.selectbox(key="tr_form_cat").set_value("compliance")
at.text_input(key="tr_form_nome").set_value("LGPD no dia a dia")
at.button_group(key="tr_form_tipo").set_value("apresentacao")
at = at.run()
conferir("tr_form_video" not in {w.key for w in at.text_input} and at.radio(key="tr_form_origem").value == "arquivo", "modal: apresentação troca os campos")
at = clicar(at, "tr_form_ok")
conferir("Cole o link do Google Slides" in texto(at) and not any(c[0] == "salvar" for c in chamadas), "modal: apresentação sem arquivo nem link não salva")
at.radio(key="tr_form_origem").set_value("link")
at = at.run()
at.text_input(key="tr_form_link").set_value("https://exemplo.com/slides")
at = clicar(at.run(), "tr_form_ok")
conferir("Link inválido" in texto(at) and not any(c[0] == "salvar" for c in chamadas), "modal: link de outro site é recusado")
at.text_input(key="tr_form_link").set_value("https://docs.google.com/presentation/d/1AbCdEfGhIjKlMn/edit?usp=sharing")
at = clicar(at.run(), "tr_form_ok")
salvo = next((c[2] for c in chamadas if c[0] == "salvar"), {})
conferir(salvo.get("conteudo_tipo") == "apresentacao" and salvo.get("conteudo_url") == "https://docs.google.com/presentation/d/1AbCdEfGhIjKlMn/edit"
         and salvo.get("conteudo_path") is None and salvo.get("video_drive_id") is None and salvo.get("capa_path") is None,
         "modal: salva a apresentação pelo Slides, sem os campos de vídeo")
com_pdf = dict(DADOS, treinamentos=DADOS["treinamentos"] + [{"id": 9, "nome": "NR-1", "categoria": "seguranca", "carga_horas": 1, "validade_meses": 0, "obrigatorio": True,
                                                              "publico": "todos", "ativo": True, "conteudo_tipo": "pdf", "conteudo_path": "1b4e28ba-2fa1-11d2-883f-0016d3cca427.pdf",
                                                              "capa_path": CAPA}])
at = aba(app(dados=com_pdf), "Catálogo")
conferir("Leitura (PDF)" in texto(at), "catálogo: marca o tipo de leitura")
at = clicar(at, "tr_editar_9")
conferir(at.button_group(key="tr_form_tipo").value == "pdf" and "continua valendo" in texto(at) and "tr_form_capa_remover" in {c.key for c in at.checkbox},
         "modal: editar PDF mostra o arquivo atual e a opção de remover a capa")
at.checkbox(key="tr_form_capa_remover").check()
at = clicar(at.run(), "tr_form_ok")
salvo = next((c[2] for c in chamadas if c[0] == "salvar"), {})
conferir(salvo.get("conteudo_path") == "1b4e28ba-2fa1-11d2-883f-0016d3cca427.pdf" and salvo.get("capa_path") is None and salvo.get("conteudo_tipo") == "pdf"
         and salvo.get("conteudo_url") is None, "modal: editar mantém o PDF e remove a capa")
at = clicar(aba(app(dados=com_pdf), "Catálogo"), "tr_editar_9")
at.button_group(key="tr_form_tipo").set_value("video")
at = clicar(at.run(), "tr_form_ok")
salvo = next((c[2] for c in chamadas if c[0] == "salvar"), {})
conferir(salvo.get("conteudo_tipo") == "video" and salvo.get("conteudo_path") is None and salvo.get("conteudo_url") is None and salvo.get("capa_path") == CAPA,
         "modal: trocar para vídeo limpa o PDF e mantém a capa")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
