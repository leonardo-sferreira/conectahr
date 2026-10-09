# Evidências — teste final por perfil (3.48, 4.26 e 5.1)

Teste por HTTP contra o workspace Xano em 09/10/2026, depois de todas as mudanças da change
`concluir-mvp-conectarh` publicadas. **43 de 43 chamadas** tiveram o resultado esperado.

**Como foi feito:** o login (senha + código recebido por e-mail) foi feito com a conta de teste do
Colaborador e com a conta de Admin. O mesmo usuário de teste foi promovido a Gestor e depois a RH
pelo Admin, e voltou a Colaborador no fim (o gestor do departamento também foi restaurado). Contas pelo
papel, sem e-mail nem token. O plano gratuito do Xano limita a 10 requisições por 20 segundos, então
há uma pausa entre as chamadas.

**Verificador de endpoints:** `python tools/checar_endpoints.py` → 184 endpoints autenticados, 0 com
falha, 0 grupos com problema de swagger. `openspec validate concluir-mvp-conectarh` passa.

## Resultado por chamada

| Perfil | Cenário | Requisição | Esperado | Obtido |
|---|---|---|---|---|
| Colaborador | sessao valida | `GET auth/me` | 200 | 200 |
| Colaborador | central de tarefas | `GET central_de_tarefas` | 200 | 200 |
| Colaborador | exportar meus dados (json) | `GET meus_dados` | 200 | 200 |
| Colaborador | exportar meus dados (csv) | `GET meus_dados` | 200 | 200 |
| Colaborador | ler preferencias de privacidade | `GET minhas_preferencias_privacidade` | 200 | 200 |
| Colaborador | gravar preferencias de privacidade | `PATCH minhas_preferencias_privacidade` | 200 | 200 |
| Colaborador | pedido LGPD | `POST solicitacoes` | 200 | 200 |
| Colaborador | meu ponto | `GET meu_ponto` | 200 | 200 |
| Colaborador | minhas ferias | `GET minhas_ferias` | 200 | 200 |
| Colaborador | mural de reconhecimento | `GET mural_reconhecimento` | 200 | 200 |
| Colaborador | indicadores (negado) | `GET indicadores` | 403 | 403 |
| Colaborador | rotina diaria (negado) | `POST rotinas/processar_diarias` | 403 | 403 |
| Colaborador | status operacional (negado) | `GET status_operacional` | 403 | 403 |
| Colaborador | minha equipe (negado) | `GET minha_equipe` | 403 | 403 |
| Colaborador | auditoria (negado) | `GET auditoria` | 403 | 403 |
| Colaborador | anonimizar (negado) | `POST colaboradores/18/anonimizar` | 403 | 403 |
| Gestor | minha equipe | `GET minha_equipe` | 200 | 200 |
| Gestor | central de tarefas (equipe) | `GET central_de_tarefas` | 200 | 200 |
| Gestor | indicadores (negado) | `GET indicadores` | 403 | 403 |
| Gestor | rotina diaria (negado) | `POST rotinas/processar_diarias` | 403 | 403 |
| Gestor | anonimizar (negado) | `POST colaboradores/18/anonimizar` | 403 | 403 |
| Gestor | decidir correcao de ponto da equipe | `POST correcoes_ponto/8/rejeitar` | 200 | 200 |
| Gestor | decidir de novo a mesma correcao (negado por estado) | `POST correcoes_ponto/8/rejeitar` | 400 | 400 |
| Gestor | decidir ferias de outro departamento ou sem escopo | `POST ferias/9/aprovar` | 400 | 400 |
| RH | listar colaboradores | `GET colaboradores` | 200 | 200 |
| RH | listar solicitacoes | `GET solicitacoes` | 200 | 200 |
| RH | indicadores | `GET indicadores` | 200 | 200 |
| RH | indicadores (csv) | `GET indicadores/exportar_csv` | 200 | 200 |
| RH | documentos com retencao vencida | `GET documentos/retencao_vencida` | 200 | 200 |
| RH | status operacional | `GET status_operacional` | 200 | 200 |
| RH | auditoria | `GET auditoria` | 200 | 200 |
| RH | decidir o proprio pedido LGPD (negado) | `POST solicitacoes/4/atender` | 403 | 403 |
| RH | minha equipe (negado) | `GET minha_equipe` | 403 | 403 |
| Admin | sessao valida | `GET auth/me` | 200 | 200 |
| Admin | usuarios | `GET usuarios` | 200 | 200 |
| Admin | indicadores | `GET indicadores` | 200 | 200 |
| Admin | status operacional | `GET status_operacional` | 200 | 200 |
| Admin | rotina diaria | `POST rotinas/processar_diarias` | 200 | 200 |
| Admin | rotina diaria, segunda execucao zerada | `POST rotinas/processar_diarias` | 200 | 200 |
| Admin | responder pedido LGPD de outra pessoa | `POST solicitacoes/4/atender` | 200 | 200 |
| Admin | abrir link de documento (auditado) | `GET documentos/22/arquivo` | 200 | 200 |
| Admin | documentos com retencao vencida | `GET documentos/retencao_vencida` | 200 | 200 |
| Admin | auditoria da abertura do arquivo | `GET auditoria` | 200 | 200 |

## O que isso cobre

- **Login:** senha + código por e-mail para o Colaborador (que depois muda de perfil) e para o Admin.
- **Leitura e decisão por módulo:** correção de ponto decidida pelo Gestor da equipe; pedido LGPD
  respondido pelo Admin (e negado ao próprio solicitante); rotina diária aplicada e repetida; abertura
  de link de documento com auditoria; indicadores; exportação dos dados do titular; preferências de
  privacidade.
- **Negações por perfil:** o Colaborador não vê indicadores, rotina, status operacional, equipe,
  auditoria nem anonimiza; o Gestor não vê indicadores nem aciona a rotina; o RH não decide o próprio
  pedido nem acessa a equipe do Gestor.

## O que ficou de fora (não verificado)

- Aprovação de férias por substituto com delegação em solicitação **pendente**, e Gestor decidindo as
  próprias férias (ver `rotinas-e-fluxos.md`).
- Abertura de comprovante e de imagens: o upload de arquivo foi retirado (ver `lgpd.md`, 4.27).
- Supressão complementar do resultado da pesquisa de clima com respondentes suficientes.
- Alerta de prazo próximo do pedido LGPD.
