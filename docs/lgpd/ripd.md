# Relatório de Impacto à Proteção de Dados Pessoais (RIPD)

**Referência:** LGPD, art. 38. **Situação:** análise técnica de projeto acadêmico, rascunho de 08/10/2026. Classificações e medidas devem ser validadas com o jurídico.

**Tratamentos avaliados** (finalidades do [registro de operações](registro-de-operacoes.md)):

1. **Dados de saúde:** atestados e ausências (F09) e saúde e segurança do trabalho (F10).
2. **Adolescentes aprendizes** (menores de 18 anos): cadastro e documentos (F03, F04) e exposição em aniversariantes e mural (F13, F14).
3. **Controle de jornada** (F07).

Os números `tarefa X.Y` são tarefas de `openspec/changes/concluir-mvp-conectarh/tasks.md`.

## Como os riscos foram classificados

- **Probabilidade:** 1 = baixa, 2 = média, 3 = alta, considerando a exposição atual do sistema.
- **Impacto sobre o titular:** 1 = baixo, 2 = médio, 3 = alto (fraude, discriminação, constrangimento, perda de emprego).
- **Nível** = probabilidade × impacto: 1 a 2 baixo, 3 a 4 médio, 6 a 9 alto.
- A coluna **Situação** diz se a medida já está em produção (**feita**) ou depende de tarefa pendente (**planejada**).

## 1. Dados de saúde (atestados, ASO, laudos)

Dado **sensível** (art. 11). Quem acessa: o próprio colaborador, RH e Admin. O Gestor vê só tipo, período e status.

| Risco | Prob. | Imp. | Nível | Medida | Situação |
|---|---|---|---|---|---|
| **R1.1** O Gestor ou outro perfil lê o atestado ou o motivo da ausência | 1 | 3 | Médio | O Gestor não recebe motivo nem comprovante; escopo por perfil e propriedade; conferir todas as respostas acessíveis ao Gestor (tarefa 3.17) | Parcial: regra no backend **feita**; conferência pendente |
| **R1.2** O campo de motivo da ausência recebe diagnóstico ou CID em texto livre | 3 | 3 | Alto | Lista fechada de motivos, recusa de CID na observação, aviso na tela e atestado só no arquivo privado (tarefa 4.11) | **Planejada** |
| **R1.3** Link público de compartilhamento no lugar do arquivo (`arquivo_url`, `documento_url`) | 2 | 3 | Alto | Aceitar só o armazenamento do Xano ou domínios aprovados (tarefa 4.12) | **Planejada** |
| **R1.4** Abertura indevida de um arquivo sensível sem rastro | 2 | 3 | Alto | Auditoria `acessar_arquivo_documento` em toda abertura (tarefa 4.10) | **Planejada** |
| **R1.5** Os arquivos de imagem (`ausencia.comprovante`, `documento.imagem_frente`) ficarem acessíveis por URL pública | 2 | 3 | Alto | Confirmar se o armazenamento é privado e corrigir (tarefa 4.12) | **A verificar** |
| **R1.6** Indicadores de absenteísmo de equipes pequenas identificam quem faltou ou adoeceu | 2 | 2 | Médio | Mínimo de pessoas por grupo, com supressão complementar (tarefa 4.14) | **Planejada** |
| **R1.7** Conta de RH ou Admin invadida expõe todos os atestados | 2 | 3 | Alto | Guarda de acesso em todos os endpoints, sessão ligada ao token, revogação em massa e bloqueio de autoaprovação (tarefas 3.2 a 3.8); código de acesso protegido (tarefa 4.13) | Parcial: guarda **feita**; hash do código **planejado** |
| **R1.8** Dados de saúde permanecem além do necessário | 2 | 2 | Médio | Prazos de guarda e anonimização (tarefas 4.20 a 4.22) | **Planejada** |

**Risco residual:** médio, até as tarefas 4.10 a 4.14 serem publicadas. Os dados do ASO guardam só o resultado operacional (apto/inapto), nunca prontuário médico.

## 2. Adolescentes aprendizes (menores de 18 anos)

Tratamento que exige o **melhor interesse** do menor (art. 14; ECA Digital). Hoje o sistema **não diferencia** colaboradores menores de idade.

| Risco | Prob. | Imp. | Nível | Medida | Situação |
|---|---|---|---|---|---|
| **R2.1** Contrato do menor ativado sem o documento do responsável legal | 2 | 3 | Alto | Bloquear a ativação sem o documento de responsável legal aprovado (tarefa 4.23) | **Planejada** |
| **R2.2** O menor aparece para todos os colegas em aniversariantes e no mural | 3 | 2 | Alto | Preferências nascem ocultas para menores de 18 anos; botão de sair da lista (tarefas 4.18 e 4.23) | **Planejada** |
| **R2.3** Dado do menor guardado por tempo indeterminado | 2 | 2 | Médio | Prazos e anonimização no desligamento (tarefas 4.20 a 4.22) | **Planejada** |
| **R2.4** O aviso de privacidade não é compreensível para um adolescente | 2 | 2 | Médio | Aviso em linguagem simples (já escrito, ver [aviso-de-privacidade.md](aviso-de-privacidade.md)) e revisão com o responsável legal | **Feita** (texto); revisão pendente |

**Risco residual:** alto até as tarefas 4.18 e 4.23 serem publicadas. Enquanto isso, recomenda-se **não cadastrar aprendizes menores de idade no ambiente real**.

## 3. Controle de jornada (ponto, correções e banco de horas)

Dado comum, mas de **risco alto** porque monitora o trabalhador e pode embasar decisões sobre ele. Base: obrigação legal (CLT, art. 74).

| Risco | Prob. | Imp. | Nível | Medida | Situação |
|---|---|---|---|---|---|
| **R3.1** O ponto é visto como certificado, sem ser | 2 | 2 | Médio | O MVP é **controle interno experimental**, com aviso na interface e backlog de conformidade REP (Portaria 671/2021) | Aviso **planejado** (tarefa 1.8) |
| **R3.2** Correção de ponto aprovada por quem a pediu | 1 | 2 | Baixo | Bloqueio de autoaprovação com auditoria (tarefa 3.8) | **Feita** |
| **R3.3** O Gestor vê o ponto de quem não é da sua equipe | 1 | 2 | Baixo | Escopo por departamento no backend | **Feita** |
| **R3.4** Marcações alteradas sem rastro | 1 | 3 | Médio | Ordem estrita de marcação, correção em fluxo próprio e auditoria | **Feita** |
| **R3.5** Conta de colaborador usada por outra pessoa para marcar o ponto | 2 | 2 | Médio | Código de acesso por e-mail a cada login, sessão ligada ao token, alerta de acesso suspeito | **Feita** |
| **R3.6** Dados de jornada guardados além do prazo legal | 2 | 2 | Médio | Prazos e anonimização (tarefas 4.20 a 4.22) | **Planejada** |

**Risco residual:** baixo a médio.

## Riscos residuais gerais

| Risco | Situação e decisão |
|---|---|
| **Auditoria antiga com dados bancários completos.** Linhas gravadas antes do mascaramento continuam com agência e conta completas | A auditoria só recebe acréscimos e não é reescrita. Acesso restrito a RH e Admin. O mascaramento vale para o que for gravado depois (tarefa 4.9) |
| **Respostas de clima antigas** (`resposta_clima`) continuam no banco, sem ser lidas por nenhum endpoint | Existem 2 linhas, de um mesmo departamento, que parecem de teste. **Decisão pendente do grupo:** aceitar o risco ou anonimizar (por exemplo, anular o departamento), sem excluir |
| **Pesquisa de clima: dedução por complemento e por diferença** nos resultados | Correção planejada (tarefa 3.49): liberar os resultados só com a pesquisa encerrada e suprimir também o total quando um único grupo é omitido |
| **Repositório público** | Todo o código do backend é visível. Nenhum segredo pode ser commitado; o `tools/checar_endpoints.py` reprova swagger ligado ou com token. Evidências em `docs/evidencias/` não podem ter dado pessoal |
| **Dados de teste em ferramentas externas** | O protótipo do Figma contém exemplos de nomes e um e-mail de uma pessoa real; deve ser trocado por dados fictícios (ver [operadores.md](operadores.md)) |
| **Assistentes de IA usados no desenvolvimento** | Não devem receber dados pessoais reais. Uma exportação com registros do banco (`xano workspace pull --records`) traz dados pessoais e não deve ser colada em ferramentas externas |

## Conclusão

Com as medidas **feitas**, o acesso a dados sensíveis já está protegido contra os riscos mais prováveis (conta invadida, token vazado, autoaprovação). Os riscos **altos** que ainda dependem de implementação são: diagnóstico em texto livre (R1.2), link público de arquivo (R1.3), abertura de arquivo sem auditoria (R1.4), exposição de menores (R2.1 e R2.2) e os arquivos de imagem possivelmente públicos (R1.5). Eles têm tarefa própria e devem estar concluídos **antes da demonstração e de qualquer uso com dados reais**.
