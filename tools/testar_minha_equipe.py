"""Verifica Minha equipe (tarefa 57) com dados fictícios e API simulada, sem rede.

Uso na raiz: .venv/Scripts/python.exe tools/testar_minha_equipe.py
Prévia com dados fictícios: .venv/Scripts/python.exe tools/testar_minha_equipe.py --servir-previa
Chrome headless, com a prévia no ar: .venv/Scripts/python.exe tools/testar_minha_equipe.py --navegador
"""

import logging
import copy
import html
import re
import sys
import unittest
from datetime import date, datetime, time, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").disabled = True

import minha_equipe_dados as dados  # noqa: E402
import minha_equipe_modelo as modelo  # noqa: E402
from api_client import ApiError  # noqa: E402
import api_client  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

HOJE = date(2026, 4, 1)
PESSOAS = [
    {"id": 10, "nome": "Gestor de teste", "e_voce": True, "status": "Ativo"},
    {"id": 11, "nome": "Liderada A", "superior_colaborador_id": 10, "departamento_id": 2,
     "status": "Ativo", "cargo_id": 1, "data_admissao": "2026-03-01", "horas_diarias": 8},
    {"id": 12, "nome": "Liderado B", "superior_colaborador_id": 10, "departamento_id": 3,
     "status": "Ferias", "cargo_id": 1, "data_admissao": "2026-03-01", "horas_diarias": 8},
    {"id": 13, "nome": "Outro superior", "superior_colaborador_id": 99, "departamento_id": 2, "status": "Ativo"},
    {"id": 14, "nome": "Sem superior", "superior_colaborador_id": None, "departamento_id": 2, "status": "Ativo"},
    {"id": 15, "nome": "Desligado", "superior_colaborador_id": 10, "status": "Desligado"},
]


def registro(dia: date, status: str, pid=11):
    return {"id": dia.day, "colaborador_id": pid, "data": dia.isoformat(), "status": status,
            "hora_entrada": int(datetime.combine(dia, time(11), tzinfo=timezone.utc).timestamp() * 1000)}


class EscopoEIndicadores(unittest.TestCase):
    def test_somente_liderados_diretos_inclusive_de_outro_departamento(self):
        self.assertEqual([p["id"] for p in modelo.liderados(PESSOAS)], [11, 12])

    def test_nao_confunde_id_do_usuario_com_id_do_colaborador(self):
        self.assertEqual(modelo.colaborador_do_gestor(PESSOAS), 10)
        self.assertEqual(modelo.liderados([{**p, "e_voce": False} for p in PESSOAS]), [])

    def test_sem_equipe_e_status_normalizado(self):
        self.assertEqual(modelo.liderados([]), [])
        self.assertEqual(modelo.liderados([PESSOAS[0], {**PESSOAS[1], "status": " desligado "}]), [])

    def test_semana_de_segunda_a_domingo_e_virada_do_ano(self):
        self.assertEqual(modelo.semana_atual(HOJE), (date(2026, 3, 30), date(2026, 4, 5)))
        self.assertEqual(modelo.meses_da_semana(HOJE), [(2026, 3), (2026, 4)])
        self.assertEqual(modelo.meses_da_semana(date(2027, 1, 1)), [(2026, 12), (2027, 1)])
        self.assertEqual(modelo.meses_da_semana(date(2026, 4, 15)), [(2026, 4)])

    def test_ponto_reutiliza_folha_e_nao_conta_jornada_atual(self):
        meses = {(2026, 3): {"registros": [registro(date(2026, 3, 30), "Aberto")]},
                 (2026, 4): {"registros": [registro(HOJE, "Aberto")]}}
        resultado = modelo.ponto_da_semana(PESSOAS[1], meses, [], HOJE)
        self.assertEqual(resultado["incompletos"], 2)  # Segunda aberta e terça sem marcação, no mês encerrado.
        self.assertEqual(len(resultado["dias"]), 7)
        self.assertTrue(all(l["em_branco"] for l in resultado["dias"] if l["data"] > HOJE))

    def test_mes_ou_feriados_indisponiveis_nao_viram_zero(self):
        meses = {(2026, 3): {}, (2026, 4): None}
        self.assertIsNone(modelo.ponto_da_semana(PESSOAS[1], meses, [], HOJE))
        self.assertIsNone(modelo.ponto_da_semana(PESSOAS[1], {(2026, 3): {}, (2026, 4): {}}, None, HOJE))

    def test_ferias_aprovadas_inclusive_nos_limites(self):
        ferias = {"ferias": [
            {"colaborador_id": 11, "data_inicio": "2026-03-20", "data_fim": "2026-04-01", "status": "Aprovada"},
            {"colaborador_id": 12, "data_inicio": "2026-04-01", "data_fim": "2026-04-10", "status": "Aprovada"},
            {"colaborador_id": 11, "data_inicio": "2026-04-01", "data_fim": "2026-04-10", "status": "Pendente"},
            {"colaborador_id": 11, "data_inicio": "2026-04-02", "data_fim": "2026-04-10", "status": "Aprovada"},
        ]}
        self.assertEqual(len(modelo.ferias_atuais(11, ferias, HOJE)), 1)
        self.assertEqual(len(modelo.ferias_atuais(12, ferias, HOJE)), 1)
        self.assertEqual(modelo.ferias_atuais(99, ferias, HOJE), [])
        self.assertIsNone(modelo.ferias_atuais(11, None, HOJE))

    def test_pedidos_filtrados_por_liderado_e_status(self):
        central = {"fila_ferias_pendentes": [{"colaborador_id": 11, "status": "Pendente"},
                                           {"colaborador_id": 13, "status": "Pendente"}],
                   "fila_ausencias_pendentes": [{"colaborador_id": 12, "status": "Pendente"}],
                   "fila_documentos_pendentes": [{"colaborador_id": 11}],
                   "fila_desligamentos_pendentes": [{"colaborador_id": 11}]}
        correcoes = {"correcoes": [{"colaborador_id": 11, "status": "pendente"},
                                   {"colaborador_id": 12, "status": "aprovada"},
                                   {"colaborador_id": 10, "status": "pendente"}]}
        grupos = modelo.pendencias_por_pessoa(modelo.liderados(PESSOAS), central, correcoes)
        self.assertEqual({pid: g["total"] for pid, g in grupos.items()}, {11: 2, 12: 1})

    def test_ausencia_de_pedidos_e_falha_parcial_sao_diferentes(self):
        pessoas = modelo.liderados(PESSOAS)
        self.assertEqual(modelo.pendencias_por_pessoa(pessoas, {}, {})[11]["total"], 0)
        parcial = modelo.pendencias_por_pessoa(pessoas, None, {"correcoes": [{"colaborador_id": 11, "status": "pendente"}]})
        self.assertIsNone(parcial[11]["total"])
        self.assertEqual(len(parcial[11]["correcoes"]), 1)
        self.assertIsNone(parcial[11]["ferias"])

    def test_busca_e_situacao_nao_ampliam_escopo(self):
        pessoas = modelo.liderados(PESSOAS)
        self.assertEqual([p["id"] for p in modelo.filtrar_pessoas(pessoas, " LIDERADA ")], [11])
        self.assertEqual([p["id"] for p in modelo.filtrar_pessoas(pessoas, situacao="FERIAS")], [12])
        self.assertEqual(modelo.filtrar_pessoas(pessoas, "Outro superior"), [])


class Carregamento(unittest.TestCase):
    def setUp(self):
        self.estado = {}
        self.chamadas = []
        self.patches = [patch.object(dados.st, "session_state", self.estado),
                        patch.object(dados, "folha_pessoas", return_value={"pessoas": PESSOAS}),
                        patch.object(dados, "ferias_equipe", return_value={"ferias": []}),
                        patch.object(api_client.requests, "request", side_effect=AssertionError("Teste sem rede"))]
        for nome in ("organograma", "calendario", "central_de_tarefas", "correcoes_ponto"):
            self.patches.append(patch.object(dados, nome, return_value={}))
        self.patches.append(patch.object(dados, "folha_mes", side_effect=self.mes))
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def mes(self, token, ano, mes):
        self.chamadas.append((ano, mes))
        return {}

    def test_duas_consultas_mensais_e_cache(self):
        resultado = dados.carregar("sessao-ficticia", HOJE)
        self.assertEqual(self.chamadas, [(2026, 3), (2026, 4)])
        self.assertEqual(len(resultado["pessoas"]), 2)
        dados.carregar("sessao-ficticia", HOJE)
        self.assertEqual(len(self.chamadas), 2)

    def test_troca_de_conta_invalida_cache_e_selecao(self):
        dados.carregar("sessao-ficticia-a", HOJE)
        self.estado["me_liderado"] = 11
        dados.carregar("sessao-ficticia-b", HOJE)
        self.assertEqual(len(self.chamadas), 4)
        self.assertNotIn("me_liderado", self.estado)

    def test_sem_liderados_nao_faz_consultas_complementares(self):
        dados.folha_pessoas.return_value = {"pessoas": [PESSOAS[0]]}
        self.assertEqual(dados.carregar("sessao-ficticia", HOJE)["pessoas"], [])
        self.assertEqual(self.chamadas, [])
        dados.organograma.assert_not_called()

    def test_falha_principal_preserva_erro_para_pagina(self):
        dados.folha_pessoas.side_effect = ApiError("erro técnico fictício", 403)
        with self.assertRaises(ApiError):
            dados.carregar("sessao-ficticia", HOJE)

    def test_falha_isolada_e_recuperacao_sem_cachear_zero(self):
        dados.central_de_tarefas.side_effect = ApiError("erro técnico fictício", 500)
        resultado = dados.carregar("sessao-ficticia", HOJE)
        self.assertIsNone(resultado["central"])
        self.assertEqual(resultado["erros"], {"central": 500})
        self.assertIsNotNone(resultado["meses"][(2026, 4)])
        dados.central_de_tarefas.side_effect = None
        self.assertEqual(dados.carregar("sessao-ficticia", HOJE)["central"], {})

    def test_401_interrompe_consultas_restantes(self):
        dados.organograma.side_effect = ApiError("Sessão encerrada", 401)
        with self.assertRaises(ApiError):
            dados.carregar("sessao-ficticia", HOJE)
        dados.central_de_tarefas.assert_not_called()
        self.assertEqual(self.chamadas, [])

    def test_falha_em_um_mes_preserva_outro_mes_e_ferias(self):
        def carregar_mes(token, ano, mes):
            if mes == 3:
                raise ApiError("Detalhe técnico fictício", 429)
            return {"ferias": [{"colaborador_id": 12, "status": "Aprovada",
                                "data_inicio": "2026-03-25", "data_fim": "2026-04-05"}]}
        dados.folha_mes.side_effect = carregar_mes
        resultado = dados.carregar("sessao-ficticia", HOJE)
        self.assertIsNone(resultado["meses"][(2026, 3)])
        self.assertEqual(resultado["erros"], {"mes-2026-3": 429})
        self.assertEqual(len(modelo.ferias_atuais(12, resultado["meses"][(2026, 4)], HOJE)), 1)

    def test_cache_expira_em_vinte_segundos(self):
        with patch.object(dados.time, "time", return_value=100):
            dados.carregar("sessao-ficticia", HOJE)
        with patch.object(dados.time, "time", return_value=119):
            dados.carregar("sessao-ficticia", HOJE)
        self.assertEqual(len(self.chamadas), 2)
        with patch.object(dados.time, "time", return_value=120):
            dados.carregar("sessao-ficticia", HOJE)
        self.assertEqual(len(self.chamadas), 4)

    def test_logout_descarta_dados_e_selecao_da_equipe(self):
        from sessao import limpar_sessao

        dados.carregar("sessao-ficticia", HOJE)
        self.estado.update(me_liderado=11, me_busca="Liderada", me_situacao="Ativo", token="sessao-ficticia")
        limpar_sessao()
        self.assertNotIn(dados.CACHE, self.estado)
        self.assertFalse(any(chave in self.estado for chave in ("me_liderado", "me_busca", "me_situacao", "token")))

    def test_ferias_consultam_janela_exata_de_90_dias(self):
        dados.carregar("sessao-ficticia", HOJE)
        dados.ferias_equipe.assert_called_once_with("sessao-ficticia", "2026-04-01", "2026-06-29")


class PeriodosEEstados(unittest.TestCase):
    def test_ferias_filtram_pessoa_periodo_status_e_datas_invalidas(self):
        def ferias(pid=11, de="2026-04-01", ate="2026-04-10", status="Aprovada"):
            return dict(colaborador_id=pid, data_inicio=de, data_fim=ate, status=status)
        itens = [ferias(), ferias(de="2026-06-29", ate="2026-07-10", status="Pendente"),
                 ferias(13), ferias(10), ferias(status="Rejeitada"), ferias(status="Concluida"),
                 ferias(de="2026-06-30", ate="2026-07-10"), ferias(de="2026-03-01", ate="2026-03-31"),
                 ferias(de="inválida"), ferias(de="2026-04-11", ate="2026-04-01")]
        self.assertEqual(len(modelo.ferias_do_periodo(modelo.liderados(PESSOAS), {"ferias": itens}, HOJE)), 2)
        self.assertIsNone(modelo.ferias_do_periodo(PESSOAS, None, HOJE))

    def test_ponto_sem_dados_nao_e_completo(self):
        self.assertEqual(modelo.situacao_ponto(None), ("Não disponível", "neu"))
        self.assertEqual(modelo.situacao_ponto({"incompletos": 0, "dias": []}), ("—", "neu"))
        self.assertIsNone(modelo.ponto_da_semana(PESSOAS[1], {(2026, 3): {}, (2026, 4): {}}, [], HOJE))

    def test_indicadores_contam_pessoas_e_nao_dias_ou_periodos(self):
        pessoas = modelo.liderados(PESSOAS)
        pontos = {11: {"incompletos": 3}, 12: {"incompletos": 0}}
        grupos = modelo.pendencias_por_pessoa(pessoas, {}, {})
        ferias = [dict(colaborador_id=12, status="Aprovada", data_inicio="2026-04-01", data_fim="2026-04-02")] * 2
        self.assertEqual([i[1] for i in modelo.indicadores(pessoas, pontos, grupos, ferias, HOJE)], ["2", "0", "1", "1"])
        pontos[12] = None
        grupos[12]["total"] = None
        self.assertEqual([i[1] for i in modelo.indicadores(pessoas, pontos, grupos, None, HOJE)], ["2", "—", "—", "—"])


class ApiFicticia:
    """Contrato usado pelos AppTests e pela prévia visual; nenhuma chamada HTTP real."""

    def __init__(self):
        self.pessoas = copy.deepcopy(PESSOAS)
        self.pessoas[0]["departamento_id"] = 2
        self.erros = {}
        self.chamadas = []
        self.ferias = [{"id": 100, "colaborador_id": 11, "data_inicio": "2026-04-11", "data_fim": "2026-04-20", "status": "Pendente"}]
        self.central = {"fila_ferias_pendentes": [dict(self.ferias[0])], "fila_ausencias_pendentes": []}
        self.correcoes = [{"id": 200, "colaborador_id": 12, "status": "pendente", "data": "2026-03-31"}]

    def responder(self, method, path, token, canonical, payload=None):
        rota = path.split("?")[0]
        self.chamadas.append((method, path))
        if rota in self.erros:
            erro = self.erros[rota]
            if erro.status_code == 401:
                dados.st.session_state.sessao_expirada = True
            raise erro
        if method != "GET":
            raise AssertionError("A prévia não permite gravações")
        if rota == "folha_ponto/pessoas":
            return {"pessoas": self.pessoas, "ve_todos": False}
        if rota == "organograma":
            return {"departamentos": [{"id": 2, "nome": "Recursos Humanos"}],
                    "cargos": [{"id": 1, "nome": "Analista de RH", "nivel_hierarquico_id": 2}],
                    "niveis": [{"id": 2, "nome": "L2"}], "colaboradores": self.pessoas}
        if rota == "calendario":
            return {"feriados": [], "ferias": [], "ausencias": []}
        if rota == "central_de_tarefas":
            return self.central
        if rota == "correcoes_ponto":
            return {"correcoes": self.correcoes}
        if rota == "ferias_equipe":
            return {"ferias": self.ferias}
        if rota == "folha_ponto/mes":
            from urllib.parse import parse_qs
            mes = int(parse_qs(path.split("?", 1)[1])["mes"][0])
            return {"registros": [], "marcacoes": [], "tratamentos": [], "ausencias": [], "ferias": []} if mes != 3 else {
                "registros": [], "marcacoes": [
                    {"id": pid * 10 + i, "colaborador_id": pid, "data": "2026-03-31",
                     "data_hora_marcacao": int(datetime(2026, 3, 31, hora, tzinfo=timezone.utc).timestamp() * 1000)}
                    for pid in (11, 12) for i, hora in enumerate((11, 20) if pid == 11 else (11,))],
                "tratamentos": [], "ausencias": [{"colaborador_id": 11, "tipo": "Licenca", "status": "Aprovada",
                                                    "data_inicio": "2026-03-30", "data_fim": "2026-03-30"}], "ferias": []}
        if rota == "minhas_notificacoes":
            return {"notificacoes": [], "total_nao_lidas": 0}
        if rota in ("auth/me", "meu_banco_horas", "colaboradores/aniversariantes", "meus_comunicados"):
            return {}
        raise AssertionError(f"Consulta não simulada: {method} {path}")


class TelaENavegacao(unittest.TestCase):
    def setUp(self):
        self.api = ApiFicticia()
        for p in (patch.object(api_client, "_request", side_effect=self.api.responder),
                  patch.object(api_client.requests, "request", side_effect=AssertionError("Teste sem rede")),
                  patch("pagina_minha_equipe.hoje_brasilia", return_value=HOJE)):
            p.start()
            self.addCleanup(p.stop)

    def app(self, perfil="GESTOR", **estado):
        at = AppTest.from_file(str(RAIZ / "frontend/app.py"), default_timeout=30)
        for chave, valor in dict(token="sessao-ficticia", usuario={"id": 999, "nome": "Gestor de teste", "perfil": perfil},
                                 sessao_validada=True, menu_grupos={"RH": True, "Equipe": True, "Admin": True}, tem_equipe=False, ir_minha_equipe=True, **estado).items():
            at.session_state[chave] = valor
        at.run()
        self.assertFalse(list(at.exception))
        at._page_hash = next((h for h, info in at._registered_pages.items() if info.get("url_pathname") == "minha-equipe"), at._page_hash)
        return at

    def texto(self, at):
        bruto = " ".join(str(e.value) for e in at.get("html"))
        bruto = re.sub(r"<style.*?</style>", "", bruto, flags=re.S)
        return html.unescape(re.sub(r"<[^>]+>", " ", bruto))

    def test_gestor_pagina_indicadores_e_escopo_sem_dados_sensiveis(self):
        self.api.pessoas[1].update(cpf="CPF_NAO_EXIBIR", dados_bancarios="BANCO_NAO_EXIBIR", documento="DOC_NAO_EXIBIR")
        at = self.app()
        texto = self.texto(at)
        self.assertIn("Recursos Humanos · 2 liderados", texto)
        for nome in ("Liderada A", "Liderado B", "Pedidos para decidir", "Ponto incompleto esta semana", "O que o gestor vê"):
            self.assertIn(nome, texto)
        for proibido in ("Outro superior", "Sem superior", "Desligado", "CPF_NAO_EXIBIR", "BANCO_NAO_EXIBIR", "DOC_NAO_EXIBIR"):
            self.assertNotIn(proibido, texto)
        self.assertEqual({b.key for b in at.button if str(b.key).startswith("me_ver_")}, {"me_ver_11", "me_ver_12"})
        self.assertFalse(list(at.toast))

    def test_busca_filtro_e_vazio_preservam_indicadores_da_equipe(self):
        at = self.app()
        at.text_input(key="me_busca").set_value("Liderada A").run()
        self.assertEqual({b.key for b in at.button if str(b.key).startswith("me_ver_")}, {"me_ver_11"})
        at.text_input(key="me_busca").set_value("")
        at.selectbox(key="me_situacao").select("Ferias").run()
        self.assertEqual({b.key for b in at.button if str(b.key).startswith("me_ver_")}, {"me_ver_12"})
        at.text_input(key="me_busca").set_value("não existe").run()
        self.assertIn("Nenhum liderado encontrado", self.texto(at))
        self.assertIn("2 liderados", self.texto(at))

    def test_sem_liderados_e_sem_ficha(self):
        self.api.pessoas = [self.api.pessoas[0]]
        at = self.app()
        self.assertIn("Você ainda não tem equipe", self.texto(at))
        self.assertFalse(any(str(b.key).startswith("me_ver_") for b in at.button))
        self.assertFalse(any("ferias_equipe" in p for _, p in self.api.chamadas))
        self.api.erros["folha_ponto/pessoas"] = ApiError("Sem ficha", 404)
        self.assertIn("Sua conta ainda não está ligada", self.texto(self.app()))

    def test_sem_ferias_nem_pendencias(self):
        self.api.ferias = []
        self.api.central = {"fila_ferias_pendentes": [], "fila_ausencias_pendentes": []}
        self.api.correcoes = []
        at = self.app()
        self.assertIn("Sem férias marcadas", self.texto(at))
        self.assertNotIn("Não disponível", self.texto(at))
        self.assertFalse(list(at.exception))

    def test_falhas_parciais_preservam_pessoas_e_nao_viram_zero(self):
        for rota in ("central_de_tarefas", "folha_ponto/mes", "ferias_equipe"):
            self.api.erros[rota] = ApiError("Erro técnico que não deve aparecer", 500)
        at = self.app()
        texto = self.texto(at)
        self.assertIn("Algumas informações não estão disponíveis", texto)
        self.assertIn("Liderada A", texto)
        self.assertIn("Não disponível", texto)
        self.assertNotIn("Erro técnico", texto)
        self.assertNotIn("Completo", texto)

    def test_perfis_fora_do_gestor_sem_consultar_dados(self):
        for perfil in ("RH", "ADMIN", "COLABORADOR"):
            with self.subTest(perfil=perfil):
                self.api.chamadas.clear()
                at = self.app(perfil)
                self.assertIn("Você não tem permissão", self.texto(at))
                self.assertNotIn("nav_Minha equipe", {b.key for b in at.button})
                self.assertFalse(any(p == "folha_ponto/pessoas" for _, p in self.api.chamadas))

    def test_403_429_e_sessao_encerrada(self):
        for codigo, mensagem in ((403, "permissão"), (429, "Espere alguns segundos")):
            self.api.erros["folha_ponto/pessoas"] = ApiError("Falha fictícia", codigo)
            self.assertIn(mensagem, self.texto(self.app()))
        self.api.erros["folha_ponto/pessoas"] = ApiError("Sessão encerrada", 401)
        at = self.app()
        self.assertNotIn("token", at.session_state)

    def test_ver_abre_central_e_menu_volta_para_minha_equipe(self):
        at = self.app()
        at.button(key="me_ver_11").click().run()
        self.assertFalse(list(at.exception))
        self.assertIn("Pedidos da sua equipe para decidir", self.texto(at))
        at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "central-de-pendencias")
        at.button(key="nav_Minha equipe").click().run()
        self.assertIn("Recursos Humanos · 2 liderados", self.texto(at))
        self.assertFalse(list(at.toast))


def previa() -> None:
    """Somente dados fictícios; chamada pela entrada temporária de --servir-previa."""
    import runpy
    import streamlit as st
    import pagina_minha_equipe

    api = ApiFicticia()
    api_client._request = api.responder
    pagina_minha_equipe.hoje_brasilia = lambda: HOJE
    if "token" not in st.session_state:
        st.session_state.update(token="sessao-ficticia", usuario={"id": 999, "nome": "Gestor de teste", "perfil": "GESTOR"},
                                sessao_validada=True, menu_grupos={"RH": True, "Equipe": True, "Admin": True}, tem_equipe=False, ir_minha_equipe=True, tema="claro")
    runpy.run_path(str(RAIZ / "frontend/app.py"), run_name="__main__")


def servir_previa() -> None:
    """Serve o app real com API fictícia; a entrada temporária preserva frontend/static (fontes)."""
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=RAIZ / "frontend",
                                     prefix="_previa_me_", suffix=".py", delete=False) as arquivo:
        arquivo.write('import sys\nfrom pathlib import Path\n'
                      'sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))\n'
                      'from testar_minha_equipe import previa\nprevia()\n')
        entrada = Path(arquivo.name)
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(entrada), "--server.headless", "true",
                        "--server.address", "127.0.0.1", "--server.port", "8515"], cwd=RAIZ, check=True)
    finally:
        entrada.unlink(missing_ok=True)


def navegador() -> None:
    """Verifica a prévia local com Chrome headless; Playwright é opcional, só para esta verificação."""
    from playwright.sync_api import sync_playwright, expect

    pasta = RAIZ / "docs/evidencias/frontend-minha-equipe"
    pasta.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 990}, device_scale_factor=1)
        page.goto("http://127.0.0.1:8515/minha-equipe")
        tabela = page.locator(".st-key-rh_tabela")
        expect(tabela).to_contain_text("Liderada A")
        expect(tabela).to_contain_text("Liderado B")
        expect(tabela).not_to_contain_text("Gestor de teste")
        expect(tabela).not_to_contain_text("Desligado")
        expect(page.get_by_test_id("stApp")).to_have_attribute("data-test-script-state", "notRunning")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(pasta / "minha-equipe.png"), full_page=True)
        print("OK: tela Gestor, escopo, fontes e captura visual")
        busca = page.get_by_role("textbox", name="Buscar liderado")
        busca.fill("Liderada A")
        busca.press("Enter")
        expect(tabela.get_by_role("button", name="Ver →")).to_have_count(1)
        expect(tabela).not_to_contain_text("Liderado B")
        busca.fill("")
        busca.press("Enter")
        expect(tabela.get_by_role("button", name="Ver →")).to_have_count(2)
        page.get_by_role("combobox", name="Situação").click()
        page.get_by_role("option", name="Situação: Ferias", exact=True).click()
        expect(tabela.get_by_role("button", name="Ver →")).to_have_count(1)
        expect(tabela).to_contain_text("Liderado B")
        print("OK: busca e filtro no navegador")
        tabela.get_by_role("button", name="Ver →").click()
        expect(page.locator(".crh-hero-titulo")).to_contain_text("Central de Pendências")
        page.get_by_role("button", name="Minha equipe", exact=True).click()
        expect(tabela).to_contain_text("Liderado B")
        expect(page.get_by_text("A tela Minha equipe ainda está em construção.", exact=True)).to_have_count(0)
        print("OK: Ver → Central → menu Minha equipe")
        page.get_by_role("combobox", name="Situação").click()
        page.get_by_role("option", name="Situação: Todos", exact=True).click()
        page.get_by_role("button", name="Gestor de teste", exact=False).click()
        page.get_by_text("Escuro", exact=True).click()
        from theme import ESC_CARTAO
        rgb = ", ".join(str(int(ESC_CARTAO[i:i + 2], 16)) for i in (1, 3, 5))
        expect(page.locator(".crh-me-card").first).to_have_css("background-color", f"rgb({rgb})")
        expect(page.get_by_test_id("stApp")).to_have_attribute("data-test-script-state", "notRunning")
        expect(page.locator(".st-key-me_cabecalho .crh-hero-titulo")).to_contain_text("Minha equipe")
        expect(page.get_by_role("button", name="Gestor de teste", exact=False)).to_be_visible()
        page.locator(".st-key-me_cabecalho .crh-hero-titulo").click()
        page.screenshot(path=str(pasta / "minha-equipe-escuro.png"), full_page=True)
        print("OK: tema escuro sem perda de conteúdo")
        browser.close()


if __name__ == "__main__":
    if "--previa" in sys.argv:
        previa()
    elif "--servir-previa" in sys.argv:
        servir_previa()
    elif "--navegador" in sys.argv:
        navegador()
    else:
        unittest.main(verbosity=2)
