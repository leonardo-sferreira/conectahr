"""F18 parcial: modelo, API fictícia e app real. Nenhuma requisição real ou escrita no Xano.

Uso: python tools/testar_indicadores_equipe.py
Prévia Streamlit: --servir-previa (8518); Chrome: --navegador.
"""

import copy
import html
import logging
import re
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").disabled = True

import api_client
import indicadores_equipe_dados as dados
import indicadores_equipe_modelo as modelo
from api_client import ApiError
from streamlit.testing.v1 import AppTest

HOJE = date(2026, 9, 15)
USUARIO = {"id": 999, "colaborador_id": 12, "nome": "Gestor de teste", "perfil": "GESTOR"}
IDS_FOLHA = [9, 10, 11, 13, 14]
IDS_BANCO = [9, 10, 11, 13, 15]
PESSOAS = [{"id": i, "e_voce": i == 12, "status": "Ativo"} for i in [12] + IDS_FOLHA]
ORG = {"departamentos": [{"id": 1, "nome": "Recursos Humanos", "gestor_colaborador_id": 12}],
       "colaboradores": [{"id": i, "departamento_id": 1} for i in [12] + IDS_BANCO]
                       + [{"id": 14, "departamento_id": 2}]}


def ausencia(aid=1, **extras):
    return dict({"id": aid, "colaborador_id": 9, "tipo": "Atestado", "data_inicio": "2026-08-30",
                 "data_fim": "2026-09-02", "status": "Registrado"}, **extras)


class ApiFicticia:
    def __init__(self):
        self.pessoas = copy.deepcopy(PESSOAS)
        self.org = copy.deepcopy(ORG)
        self.bancos = dict(zip(IDS_BANCO, [3 + 1/3, -1, 2, 2, 3 + 1/3]))
        self.meses = {}
        for (ano, mes), total in zip(modelo.meses(HOJE), [6, 9, 4, 11, 14, 12]):
            self.meses[(ano, mes)] = {"registros": [{"id": mes * 100 + pid, "colaborador_id": pid,
                "data": f"{ano}-{mes:02d}-01", "horas_extras": total / 5} for pid in IDS_FOLHA], "ausencias": []}
        self.meses[(2026, 8)]["ausencias"] = [ausencia()]
        self.meses[(2026, 9)]["ausencias"] = [ausencia(), ausencia(2, tipo="Falta"), ausencia(3, tipo="Licenca")]
        self.erros, self.chamadas = {}, []

    def responder(self, method, path, token, canonical, payload=None):
        self.chamadas.append((method, path, canonical))
        if path in self.erros:
            erro = self.erros[path]
            if erro.status_code == 401:
                dados.st.session_state["sessao_expirada"] = True
            raise erro
        if path == "folha_ponto/pessoas":
            assert canonical == api_client.GRUPO_PONTO
            return {"pessoas": copy.deepcopy(self.pessoas)}
        if path.startswith("folha_ponto/mes?"):
            assert canonical == api_client.GRUPO_PONTO
            q = parse_qs(urlsplit(path).query)
            assert "colaborador_id" not in q
            return copy.deepcopy(self.meses[(int(q["ano"][0]), int(q["mes"][0]))])
        if path == "organograma":
            assert canonical == api_client.GRUPO_DEPARTAMENTOS
            return copy.deepcopy(self.org)
        if m := re.fullmatch(r"colaboradores/(\d+)/banco_horas", path):
            assert canonical == api_client.GRUPO_PONTO and int(m[1]) in IDS_BANCO
            return {"saldo_horas": self.bancos.get(int(m[1])), "lancamentos": [{"observacao": "NAO_EXIBIR"}]}
        if path == "minhas_notificacoes":
            return {"notificacoes": [], "total_nao_lidas": 0}
        if path in ("auth/me", "central_de_tarefas", "meu_banco_horas", "colaboradores/aniversariantes", "meus_comunicados"):
            return {}
        if path == "colaboradores/12/onboarding":
            raise ApiError("Sem onboarding.", 404)
        raise AssertionError(f"Endpoint inesperado/proibido no teste F18: {method} {path}")


class Base(unittest.TestCase):
    def setUp(self):
        self.api = ApiFicticia()
        for p in (patch.object(api_client, "_request", side_effect=self.api.responder),
                  patch.object(api_client.requests, "request", side_effect=AssertionError("Teste sem rede")),
                  patch("pagina_indicadores_equipe.hoje_brasilia", return_value=HOJE)):
            p.start()
            self.addCleanup(p.stop)


class ModeloEFontes(Base):
    def setUp(self):
        super().setUp()
        p = patch.object(dados.st, "session_state", {})
        p.start()
        self.addCleanup(p.stop)

    def test_seis_meses_inclusive_corrente_e_virada_de_ano(self):
        self.assertEqual(modelo.meses(date(2026, 2, 28)), [(2025, 9), (2025, 10), (2025, 11), (2025, 12), (2026, 1), (2026, 2)])

    def test_serie_gravada_sem_recalcular_jornada(self):
        serie = modelo.serie_mensal(self.api.meses, IDS_FOLHA, HOJE)
        self.assertEqual([round(i["valor"]) for i in serie], [6, 9, 4, 11, 14, 12])
        self.assertEqual(serie[-1]["texto"], "+12h00")
        self.assertEqual([i["rotulo"] for i in serie], ["abr/26", "mai/26", "jun/26", "jul/26", "ago/26", "set/26"])

    def test_mes_vazio_nao_e_zero(self):
        self.assertEqual(modelo.extras_do_mes([], IDS_FOLHA, 2026, 9, HOJE), (None, "Sem registros"))

    def test_zero_somente_com_registros_validos(self):
        registros = [dict(r, horas_extras=0) for r in self.api.meses[(2026, 9)]["registros"]]
        self.assertEqual(modelo.extras_do_mes(registros, IDS_FOLHA, 2026, 9, HOJE)[0], 0)

    def test_cobertura_parcial_valor_ausente_ou_invalido(self):
        base = self.api.meses[(2026, 9)]["registros"]
        for registros in (base[:-1], [dict(base[0], horas_extras=None)] + base[1:],
                          [dict(base[0], horas_extras=float("nan"))] + base[1:], [dict(base[0], horas_extras=-1)] + base[1:]):
            self.assertIsNone(modelo.extras_do_mes(registros, IDS_FOLHA, 2026, 9, HOJE)[0])

    def test_futuro_fora_do_mes_e_pessoas_fora_do_recorte(self):
        base = self.api.meses[(2026, 9)]["registros"]
        extras = [dict(base[0], id=700, data="2026-09-30", horas_extras=999),
                  dict(base[0], id=701, data="2026-08-01", horas_extras=999),
                  dict(base[0], id=702, colaborador_id=12, horas_extras=999)]
        self.assertAlmostEqual(modelo.extras_do_mes(base + extras, IDS_FOLHA, 2026, 9, HOJE)[0], 12)

    def test_registro_duplicado_e_conflitante(self):
        base = self.api.meses[(2026, 9)]["registros"]
        self.assertAlmostEqual(modelo.extras_do_mes(base + [base[0]], IDS_FOLHA, 2026, 9, HOJE)[0], 12)
        self.assertIsNone(modelo.extras_do_mes(base + [dict(base[0], horas_extras=8)], IDS_FOLHA, 2026, 9, HOJE)[0])

    def test_agrupa_ausencias_por_solicitacao_sem_duplicar_meses(self):
        itens, _ = modelo.ausencias_por_tipo(self.api.meses, IDS_FOLHA, HOJE)
        self.assertEqual(sum(n for _, n in itens), 3)
        self.assertEqual(dict(itens), {"Atestado": 1, "Falta": 1, "Licença": 1})

    def test_ausencia_filtra_status_pessoas_datas_sem_incluir_ferias(self):
        mes = self.api.meses[(2026, 9)]
        mes["ferias"] = [ausencia(8)]
        mes["ausencias"] += [ausencia(4, status="Pendente"), ausencia(5, status="Rejeitada"),
            ausencia(6, colaborador_id=12), ausencia(7, data_inicio="2026-10-01", data_fim="2026-10-05")]
        self.assertEqual(sum(n for _, n in modelo.ausencias_por_tipo(self.api.meses, IDS_FOLHA, HOJE)[0]), 3)

    def test_ausencia_periodo_incompleto_ou_conflito_fica_indisponivel(self):
        self.api.meses[(2026, 4)] = None
        self.assertIsNone(modelo.ausencias_por_tipo(self.api.meses, IDS_FOLHA, HOJE)[0])
        self.api.meses[(2026, 4)] = {"ausencias": [ausencia(tipo="Falta")]}
        self.assertIsNone(modelo.ausencias_por_tipo(self.api.meses, IDS_FOLHA, HOJE)[0])

    def test_banco_positivo_negativo_e_soma_sem_arredondar_individuos(self):
        self.assertAlmostEqual(modelo.total_banco(self.api.bancos, IDS_BANCO), 9 + 2/3)
        self.assertEqual(modelo.saldo(modelo.total_banco(self.api.bancos, IDS_BANCO))[0], "+9h40")
        self.assertEqual(modelo.total_banco({i: -1.5 for i in IDS_BANCO}, IDS_BANCO), -7.5)
        self.assertEqual(modelo.total_banco({i: 1 for i in IDS_BANCO}, IDS_BANCO), 5)

    def test_banco_incompleto_ou_sem_pessoas_nao_vira_zero(self):
        self.assertIsNone(modelo.total_banco({}, IDS_BANCO))
        self.assertIsNone(modelo.total_banco({}, []))
        self.assertIsNone(modelo.total_banco({i: 1 for i in IDS_BANCO}, None))

    def test_protecao_de_grupos_pequenos(self):
        ids = IDS_FOLHA[:4]
        self.assertIsNone(modelo.extras_do_mes([], ids, 2026, 9, HOJE)[0])
        self.assertIsNone(modelo.ausencias_por_tipo(self.api.meses, ids, HOJE)[0])
        self.assertIsNone(modelo.total_banco(self.api.bancos, IDS_BANCO[:4]))

    def test_recortes_distintos_e_exclusao_de_proprio_desligado(self):
        self.api.pessoas.append({"id": 77, "e_voce": False, "status": "Desligado"})
        self.api.org["colaboradores"].append({"id": 77, "departamento_id": 1, "status": "Desligado"})
        d = dados.carregar("teste", USUARIO, HOJE)
        self.assertEqual(d["folha"]["ids"], IDS_FOLHA)
        self.assertEqual(d["banco"]["ids"], IDS_BANCO)
        banco_ids = {int(path.split("/")[1]) for _, path, _ in self.api.chamadas if path.endswith("/banco_horas")}
        self.assertEqual(banco_ids, set(IDS_BANCO))
        self.assertNotIn(USUARIO["id"], banco_ids)

    def test_departamento_nao_identificado_nao_tenta_bancos(self):
        for org in ({}, dict(ORG, departamentos=[]), dict(ORG, departamentos=ORG["departamentos"] * 2)):
            dados.invalidar()
            self.api.org = org
            self.api.chamadas.clear()
            d = dados.carregar("teste", USUARIO, HOJE)
            self.assertIsNone(d["banco"])
            self.assertFalse(any(p.endswith("/banco_horas") for _, p, _ in self.api.chamadas))

    def test_fichas_divergentes_nao_assumem_departamento(self):
        d = dados.carregar("teste", dict(USUARIO, colaborador_id=9), HOJE)
        self.assertIsNone(d["banco"])

    def test_falha_banco_nao_impede_folha(self):
        self.api.erros["colaboradores/9/banco_horas"] = ApiError("Falha.", 500)
        d = dados.carregar("teste", USUARIO, HOJE)
        self.assertIsNone(modelo.total_banco(d["saldos"], IDS_BANCO))
        self.assertIsNotNone(modelo.serie_mensal(d["meses"], IDS_FOLHA, HOJE)[-1]["valor"])

    def test_folha_negada_nao_impede_banco_autorizado(self):
        self.api.erros["folha_ponto/pessoas"] = ApiError("Sem permissão.", 403)
        d = dados.carregar("teste", USUARIO, HOJE)
        self.assertIsNone(d["folha"])
        self.assertIsNotNone(modelo.total_banco(d["saldos"], IDS_BANCO))

    def test_cache_sessao_atualizacao_e_logout(self):
        d = dados.carregar("teste", USUARIO, HOJE)
        quantidade = len(self.api.chamadas)
        dados.carregar("teste", USUARIO, HOJE)
        self.assertEqual(len(self.api.chamadas), quantidade)
        dados.invalidar()
        dados.carregar("teste", USUARIO, HOJE)
        self.assertGreater(len(self.api.chamadas), quantidade)
        dados.st.session_state["ie_periodo"] = "anterior"
        dados.carregar("nova-sessao", USUARIO, HOJE)
        self.assertNotIn("ie_periodo", dados.st.session_state)
        from sessao import limpar_sessao
        dados.st.session_state["tema"] = "escuro"
        limpar_sessao()
        self.assertEqual(dados.st.session_state, {"tema": "escuro"})

    def test_projecao_nao_armazena_campos_sensiveis(self):
        self.api.meses[(2026, 9)]["registros"][0]["cpf"] = "CPF_SIGILO"
        d = dados.carregar("teste", USUARIO, HOJE)
        self.assertNotIn("CPF_SIGILO", str(dados.st.session_state))
        self.assertNotIn("NAO_EXIBIR", str(dados.st.session_state))
        self.assertNotIn("nome", d["folha"])

    def test_payload_parcial_isola_campos_e_nao_inventa_zero(self):
        self.api.meses[(2026, 9)].pop("ausencias")
        d = dados.carregar("teste", USUARIO, HOJE)
        self.assertIsNotNone(modelo.serie_mensal(d["meses"], IDS_FOLHA, HOJE)[-1]["valor"])
        self.assertIsNone(modelo.ausencias_por_tipo(d["meses"], IDS_FOLHA, HOJE)[0])

    def test_saldo_ausente_e_numero_nao_finito_ficam_indisponiveis(self):
        self.api.bancos[9] = None
        d = dados.carregar("teste", USUARIO, HOJE)
        self.assertIsNone(modelo.total_banco(d["saldos"], IDS_BANCO))
        self.assertIsNone(modelo.total_banco({i: 1e308 for i in IDS_BANCO}, IDS_BANCO))

    def test_ficha_ausente_usa_e_voce_nunca_user_id(self):
        d = dados.carregar("teste", dict(USUARIO, colaborador_id=None), HOJE)
        self.assertEqual(d["banco"]["ids"], IDS_BANCO)
        self.assertEqual(d["folha"]["gestor_id"], 12)


class TelaENavegacao(Base):
    def app(self, perfil="GESTOR", tema="claro"):
        at = AppTest.from_file(str(RAIZ / "frontend/app.py"), default_timeout=30)
        for k, v in dict(token="sessao-ficticia", usuario=dict(USUARIO, perfil=perfil), tema=tema,
                         sessao_validada=True, tem_equipe=False).items():
            at.session_state[k] = v
        at.run()
        self.assertFalse(list(at.exception))
        self.api.chamadas.clear()
        at._page_hash = next(h for h, i in at._registered_pages.items() if i.get("url_pathname") == "indicadores-da-equipe")
        at.run()
        self.assertFalse(list(at.exception))
        return at

    def texto(self, at):
        bruto = " ".join(str(e.value) for e in at.get("html"))
        bruto = re.sub(r"<style.*?</style>", "", bruto, flags=re.S)
        return html.unescape(re.sub(r"<[^>]+>", " ", bruto))

    def indicadores(self, at):
        return re.findall(r'class="crh-stat-valor[^\"]*">([^<]*)', " ".join(str(e.value) for e in at.get("html")))

    def test_gestor_cards_coberturas_periodo(self):
        at = self.app()
        self.assertEqual(self.indicadores(at), ["—", "+12h00", "+9h40", "—"])
        texto = self.texto(at)
        for termo in ("Recursos Humanos", "01/04/2026 a 15/09/2026", "Não representa necessariamente todo o departamento", "Saldo corrente", "Contagem única por solicitação", "Clima"):
            self.assertIn(termo.casefold(), texto.casefold())
        self.assertEqual(at.selectbox(key="ie_periodo").options, [modelo.PERIODO])

    def test_navegacao_menu_sem_construcao(self):
        at = self.app()
        at.button(key="nav_Início").click().run()
        at._page_hash = next(h for h, i in at._registered_pages.items() if i.get("page_name") == "Início")
        at.button(key="nav_Indicadores da equipe").click().run()
        self.assertFalse(list(at.exception))
        self.assertFalse(list(at.toast))
        self.assertIn("Horas extras por mês", self.texto(at))

    def test_outros_perfis_sem_menu_nem_consultas(self):
        for perfil in ("RH", "ADMIN", "COLABORADOR"):
            with self.subTest(perfil=perfil):
                at = self.app(perfil)
                self.assertIn("Você não tem permissão", self.texto(at))
                self.assertNotIn("nav_Indicadores da equipe", {b.key for b in at.button})
                self.assertEqual(self.api.chamadas, [])

    def test_mes_atual_vazio_mantem_outros_meses(self):
        self.api.meses[(2026, 9)]["registros"] = []
        at = self.app()
        self.assertEqual(self.indicadores(at)[1], "—")
        self.assertIn("+14h00", self.texto(at))
        self.assertNotIn("0h00", self.texto(at))

    def test_mes_falha_nao_vira_zero_nem_total_parcial_de_ausencias(self):
        self.api.erros["folha_ponto/mes?ano=2026&mes=8"] = ApiError("Falha.", 500)
        at = self.app()
        self.assertIn("Período sem cobertura completa", self.texto(at))
        self.assertEqual(self.indicadores(at)[1], "+12h00")
        self.assertIn("+9h40", self.texto(at))

    def test_banco_parcial_indisponivel_sem_derrubar_horas(self):
        self.api.erros["colaboradores/9/banco_horas"] = ApiError("Sem permissão.", 403)
        at = self.app()
        self.assertEqual(self.indicadores(at), ["—", "+12h00", "—", "—"])
        self.assertIn("falta de permissão", self.texto(at))

    def test_banco_negativo(self):
        self.api.bancos = {i: -1.5 for i in IDS_BANCO}
        self.assertEqual(self.indicadores(self.app())[2], "-7h30")

    def test_sem_pessoas_e_protecao_grupo_pequeno(self):
        for ids in ([], IDS_FOLHA[:3]):
            self.api.pessoas = [PESSOAS[0]] + [p for p in PESSOAS if p["id"] in ids]
            self.api.org["colaboradores"] = [{"id": 12, "departamento_id": 1}]
            at = self.app()
            self.assertEqual(self.indicadores(at), ["—"] * 4)
            self.assertIn("Agregados de grupos com menos de 5", self.texto(at))

    def test_ausencias_vazias_confirmadas(self):
        for mes in self.api.meses.values():
            mes["ausencias"] = []
        self.assertIn("Nenhuma solicitação aprovada ou registrada", self.texto(self.app()))

    def test_fontes_independentes_e_erro_geral_recuperavel(self):
        self.api.erros["organograma"] = ApiError("Falha.", 500)
        at = self.app()
        self.assertEqual(self.indicadores(at)[1:3], ["+12h00", "—"])
        self.api.erros.clear()
        at.button(key="ie_atualizar").click().run()
        self.assertEqual(self.indicadores(at)[2], "+9h40")

    def test_absenteismo_clima_csv_bloqueados_sem_chamadas_restritas(self):
        at = self.app()
        self.assertTrue(at.button(key="ie_csv").disabled)
        self.assertEqual(len(at.get("download_button")), 0)
        self.assertIn("O resultado do clima só aparece para grupos com 5 pessoas ou mais.", self.texto(at))
        self.assertIn("resultado não está disponível para o Gestor", self.texto(at))
        self.assertTrue(all(m == "GET" for m, _, _ in self.api.chamadas))
        self.assertFalse(any("indicadores" in p or "clima" in p or "calendario" in p for _, p, _ in self.api.chamadas))

    def test_sessao_expirada(self):
        self.api.erros["organograma"] = ApiError("Sessão encerrada.", 401)
        at = self.app()
        self.assertNotIn("token", at.session_state)

    def test_privacidade_e_html_escapado(self):
        self.api.org["departamentos"][0]["nome"] = "<b>Departamento fictício</b>"
        self.api.org["colaboradores"][0].update(cpf="CPF_SIGILO", nome="PESSOA_SIGILO")
        for mes in self.api.meses.values():
            mes["registros"][0].update(cpf="CPF_SIGILO", conta="BANCO_SIGILO", observacao="COMENTARIO_SIGILO")
        at = self.app()
        bruto = " ".join(str(e.value) for e in at.get("html"))
        for segredo in ("CPF_SIGILO", "PESSOA_SIGILO", "BANCO_SIGILO", "COMENTARIO_SIGILO", "NAO_EXIBIR", "<b>Departamento fictício</b>"):
            self.assertNotIn(segredo, bruto)
        self.assertIn("&lt;b&gt;Departamento fictício&lt;/b&gt;", bruto)

    def test_temas_claro_escuro_preservam_metricas(self):
        for tema in ("claro", "escuro"):
            at = self.app(tema=tema)
            self.assertEqual(self.indicadores(at), ["—", "+12h00", "+9h40", "—"])
            self.assertEqual(at.session_state["tema"], tema)


def previa():
    import runpy
    import streamlit as st
    import pagina_indicadores_equipe
    if "api_f18_ficticia" not in st.session_state:
        st.session_state.api_f18_ficticia = ApiFicticia()
    api_client._request = st.session_state.api_f18_ficticia.responder
    pagina_indicadores_equipe.hoje_brasilia = lambda: HOJE
    if "token" not in st.session_state:
        st.session_state.update(token="sessao-ficticia", usuario=copy.deepcopy(USUARIO), sessao_validada=True,
                                tem_equipe=False, tema="claro")
    runpy.run_path(str(RAIZ / "frontend/app.py"), run_name="__main__")


def servir_previa():
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=RAIZ / "frontend", prefix="_previa_f18_", suffix=".py", delete=False) as f:
        f.write('import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))\n'
                'from testar_indicadores_equipe import previa\nprevia()\n')
        entrada = Path(f.name)
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(entrada), "--server.headless", "true",
                        "--server.address", "127.0.0.1", "--server.port", "8518"], cwd=RAIZ, check=True)
    finally:
        entrada.unlink(missing_ok=True)


def navegador():
    from playwright.sync_api import sync_playwright, expect
    pasta = RAIZ / "docs/evidencias/frontend-indicadores-equipe"
    pasta.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1150}, device_scale_factor=1)
        page.goto("http://127.0.0.1:8518/indicadores-da-equipe")
        expect(page.locator(".crh-stat-valor")).to_have_text(["—", "+12h00", "+9h40", "—"])
        expect(page.get_by_role("button", name="Exportar CSV", exact=True)).to_be_disabled()
        expect(page.locator(".crh-ie-mes")).to_have_count(6)
        expect(page.get_by_text("Recursos Humanos · últimos 6 meses", exact=True)).to_be_visible()
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(pasta / "indicadores-equipe.png"), full_page=True)
        page.get_by_role("button", name="Início", exact=True).click()
        page.get_by_role("button", name="Indicadores da equipe", exact=True).click()
        expect(page.locator(".crh-ie-mes")).to_have_count(6)
        expect(page.get_by_text("A tela Indicadores da equipe ainda está em construção.", exact=True)).to_have_count(0)
        page.get_by_role("button", name="Gestor de teste", exact=False).click()
        page.get_by_text("Escuro", exact=True).click()
        expect(page.get_by_test_id("stApp")).to_have_attribute("data-test-script-state", "notRunning")
        page.locator(".crh-hero-titulo").click()
        page.get_by_test_id("stMain").evaluate("e => e.scrollTo(0, 0)")
        page.screenshot(path=str(pasta / "indicadores-equipe-escuro.png"), full_page=True)
        browser.close()
    print("OK: Chrome, navegação, dados, CSV indisponível e temas claro/escuro.")


if __name__ == "__main__":
    if "--servir-previa" in sys.argv:
        servir_previa()
    elif "--navegador" in sys.argv:
        navegador()
    else:
        unittest.main(verbosity=2)
