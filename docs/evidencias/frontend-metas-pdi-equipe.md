# Metas e PDI da equipe — F16

## Atualização de 22/11/2026: F16 completo (decisões D1 a D5)

Com as decisões do dono do produto (`openspec/changes/concluir-metas-pdi-equipe/design.md`, D1 a D5), o F16 deixou de ser parcial. O histórico da versão parcial, com tudo travado, está mais abaixo.

**Backend publicado no Xano.** Antes de publicar, a paridade com o Xano foi conferida; o dry-run mostrou só `ADD_FIELD` e o valor novo do enum.

- **`minha_equipe/metas_pdi` GET (novo):** só os liderados diretos, com título, prazo, progresso e situação. Mais as 1:1 do gestor, os ciclos em andamento e as pessoas para quem ele pode criar meta.
- **`metas` POST:** o gestor só cria para os liderados diretos e para o próprio departamento. Fica na auditoria, avisa no sino e manda e-mail.
- **`pdi` POST:** a mesma regra da meta, com auditoria e aviso no sino.
- **`metas/{id}/checkin` POST:** aceita o líder direto. Fica em nome dele e na auditoria, e o dono é avisado no sino.
- **`reunioes_individuais` POST:**
  - só com liderado direto;
  - com hora e situação ("agendada" ou "realizada");
  - fica na auditoria;
  - avisa no sino e manda e-mail ao agendar.
- **`reunioes_individuais/{id}/situacao` POST (novo):** marca como realizada (com anotações) ou cancelada (com motivo). Só quem agendou e só a partir de "agendada". Cancelar manda e-mail.
- **Tabelas:**
  - `reuniao_individual` ganhou `hora`, `situacao`, `situacao_em` e `motivo_cancelamento`;
  - `notificacao_interna` ganhou o tipo `acompanhamento_equipe`.
- **Testes:**
  - as expressões novas rodaram numa função temporária, apagada depois: hora válida e inválida, data formatada, ficha ausente e gestor de departamento nulo;
  - `checar_endpoints` passa com 308 endpoints.

**Tela:**
- `pagina_metas_equipe.py`:
  - tabela de metas (atrasadas primeiro, a linha atrasada em âmbar, concluídas no fim);
  - filtro de pessoa;
  - abas PDI e Reuniões 1:1;
  - cinco modais: Nova meta, Check-in, Nova ação de PDI, Agendar 1:1 e Realizada ou cancelada.
- Regras puras em `metas_equipe_modelo.py`.
- **Trajetória:** o liderado vê as próprias 1:1, com o combinado ou o motivo do cancelamento.
- **Sino:** os avisos levam à Trajetória.

**Figma:** os caminhos novos "Reunião 1:1" e "Nova ação de PDI" estão na seção F16. No escuro, a auditoria de contraste não deixou nenhum texto abaixo de 3:1.

| Tema | Reunião 1:1 | Nova ação de PDI |
|---|---|---|
| Claro | `644:886` | `644:1522` |
| Escuro | `644:2840` | `644:3455` |

**Verificação:**
- `tools/testar_metas_equipe.py`: 32 de 32;
- `tools/testar_trajetoria.py`: 49 de 49;
- Chrome em 1440 px (temas claro e escuro, os cinco modais) e em 390 px, sem rolagem lateral.

| Print | Arquivo |
|---|---|
| Tela clara | `frontend-metas-pdi-equipe/metas-equipe-claro.png` |
| Tela escura | `frontend-metas-pdi-equipe/metas-equipe-escuro.png` |
| Nova meta | `frontend-metas-pdi-equipe/f16-modal-nova-meta.png` |
| Check-in do líder | `frontend-metas-pdi-equipe/f16-modal-checkin.png` |
| Aba Reuniões 1:1 | `frontend-metas-pdi-equipe/f16-aba-reunioes.png` |
| Agendar 1:1 | `frontend-metas-pdi-equipe/f16-modal-agendar.png` |
| Realizada ou cancelada | `frontend-metas-pdi-equipe/f16-modal-situacao.png` |
| Nova ação de PDI | `frontend-metas-pdi-equipe/f16-modal-pdi.png` |
| Celular, 390 px | `frontend-metas-pdi-equipe/f16-390.png` |

**Desvios do Figma:**
- O "Início" da meta saiu do modal, porque `meta_avaliacao` não tem esse campo.
- O peso da meta nova é 1, igual para todas.
- No celular, o cabeçalho da tabela some; cada linha já traz meta, pessoa, prazo, progresso e situação.

**Revisão independente do diff:** nada grave; nenhuma brecha de autorização e nenhum XSS. O que ela apontou foi corrigido e publicado:
- a Trajetória mostra quem fez o último check-in, quando foi o líder (D3);
- o PDI de uma pessoa do departamento fica com ela como responsável;
- o modal avisa quando a pessoa não é liderada direta e por isso não aparece na tela;
- pessoa desligada e departamento inativo não contam como liderança;
- o PDI exige ciclo em andamento e responsável que seja a própria pessoa ou quem cria;
- o "hoje" da tela usa o horário de Brasília;
- as 1:1 da Trajetória ficam guardadas por 60 segundos.

O trecho novo da Trajetória rodou numa função temporária, já apagada: autor diferente, a própria pessoa e usuário inexistente.

Fica registrado, sem mudança: o RH e o Admin agendam 1:1 com qualquer pessoa, como já era antes. A D4 trata do gestor.

**Falta:** os testes por HTTP no Xano real, com o login de um gestor e de um liderado direto dele. Devem conferir o que passa e o que dá 403 em cada endpoint.

---

## Histórico: F16 parcial (21/10/2026)

Verificação local em 21/10/2026, branch `feature/metas-equipe`. Dados exclusivamente sintéticos nos testes. Nenhum acesso ou alteração no Xano, credencial real, commit ou publicação.

## Referência e comparação visual

Figma: [tela clara 248:1427](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=248-1427), [tela escura 315:3642](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=315-3642). Consultadas via MCP antes da implementação.

| Tema | Comparação lado a lado | Captura Streamlit |
|---|---|---|
| Claro | [Figma × implementação](frontend-metas-pdi-equipe/comparacao-claro.png) | [Tela clara](frontend-metas-pdi-equipe/metas-equipe-claro.png) |
| Escuro | [Figma × implementação](frontend-metas-pdi-equipe/comparacao-escuro.png) | [Tela escura](frontend-metas-pdi-equipe/metas-equipe-escuro.png) |

Diferenças intencionais: os dados ilustrativos do Figma são substituídos por indisponibilidade; ações dependentes de backend ficam desabilitadas. O filtro de pessoa também está desabilitado, sem usar pessoas do ciclo anual para simular cobertura do F16. Não há formulário de nova meta/check-in ou agendamento. Tabela sem linhas, barras ou percentuais fictícios; cartões sem horários/status inventados. A tabela usa o contêiner com borda e textos do tema, sem copiar CSS. A seção anual foi acrescentada abaixo com título próprio; não consta no F16. Menu existente preservado, incluindo páginas que não aparecem no frame, e rótulo de navegação “Metas da equipe”.

## Cenários

Transporte de API integralmente simulado; qualquer chamada não prevista falha o teste. As operações descritas como GET/POST abaixo são verificadas no transporte falso, sem requisição HTTP ao Xano.

| Cenário | Operação/ação | Esperado | Obtido |
|---|---|---|---|
| Gestor abre o menu | Navegação real do app | F16 parcial e ciclo anual separados | OK — AppTest e Chrome |
| Ciclo anual | GET meu_ciclo_metas e formularios_meta | Seleção, busca e três situações mantidas | OK |
| Leitura/feedback | GET formulário e POST feedback anual | Ler etapas e atualizar formulário após feedback | OK — somente endpoint anual |
| Feedback recusado | POST feedback retorna 403 | Mostrar erro e preservar texto, sem sucesso | OK |
| RH/Admin | Modal compartilhado na aba Formulários | Ler respostas; não conceder feedback sem autorização retornada | OK |
| Cache atual | Mesmo usuário/token, dentro de 20 s | Reutilizar resposta | OK |
| Troca de sessão | Outro usuário ou token | Descartar cache, campos e formulário aberto; reconsultar | OK — incluindo AppTest com modal aberto |
| Logout | limpar_sessao | Remover cm_*, mf_*, mp_* e identidade; preservar tema | OK |
| Sem ciclo/pessoas | Respostas anuais vazias | Mensagem anual correta e F16 indisponível preservado | OK |
| Falha parcial | 503 nos ciclos; 403/429 na lista | Erro visível, sem cachear falha nem apagar F16 | OK |
| Fontes bloqueadas | Alternar abas e verificar ações | Nenhum plano_carreira, criação de meta, check-in de liderado ou PDI próprio | OK |
| Privacidade | Campos extras e HTML em dados sintéticos | Não exibir CPF, salário, conta ou documento; escapar nome | OK |
| Reuniões | Aba/cartão | Sem horário ou situação “Agendada”; ação indisponível | OK |
| Dois temas | Streamlit/Chrome e AppTest | Conteúdo legível e controles bloqueados em ambos | OK |

## Testes executados

- `tools/testar_metas_equipe.py`: 20 testes locais.
- Ciclo anual: 55/55; Trajetória: 44/44; Minha equipe: 31; Avaliações da equipe: 32; Indicadores da equipe: 37; login F01: 52/52; Delegações: 30; notificações: 21/21.
- Equivalente local das 41 suítes/verificadores Python do workflow `validar.yml`, incluindo a nova suíte. Sem instalar dependências ou sobrescrever secrets/configurações.
- Sintaxe de frontend/tools, OpenSpec strict e `git diff --check`.
- Streamlit real com transporte sintético, Chrome/Playwright: menu Início → Metas da equipe, busca sem correspondência/restauração, modal anual, ações desabilitadas e alternância claro/escuro.

Os AppTests emitem avisos conhecidos `missing ScriptRunContext` na preparação do estado fora do runtime; não são falhas. No encerramento do servidor local ocorreu aviso de conexão cancelada do asyncio no Windows; a navegação e as capturas já haviam passado.

## Limites e não verificados

F16 integral não concluído: falta contrato de listagem mínima de metas/PDI da equipe, autorização departamental segura de criação, autorização de check-in para liderança e agendamento compatível com o desenho. Nenhuma alteração de backend foi feita. Não foi criado modelo novo de percentuais/prazos porque não há dados F16 seguros para transformar.

HTTP real, notificação transacional por e-mail e escrita real de feedback anual: **NÃO VERIFICADOS nesta execução**, que não altera Xano. Permissões reais continuam responsabilidade dos contratos existentes; os testes locais não comprovam implantação ou autorização HTTP.

Para reproduzir a verificação visual opcional, em terminais separados:

```powershell
python tools/testar_metas_equipe.py --servir-previa
python tools/testar_metas_equipe.py --navegador
```

A prévia usa exclusivamente API sintética em `127.0.0.1:8516`; o arquivo temporário de entrada é removido ao encerrar normalmente. Os PNGs `figma-claro.png` e `figma-escuro.png` são referências estáticas do protótipo, sem URLs temporárias incorporadas ao produto.
