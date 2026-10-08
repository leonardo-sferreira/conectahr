# Evidências de LGPD

Registros de verificação das tarefas de adequação à LGPD. **Regras:** sem nome, CPF, e-mail, senha ou token; contas de teste só pelo papel; ids de registro são de dados de teste.

## Exercício de incidente: token de acesso vazado

**Identificador:** `EX-2026-001` (simulação, não é incidente real). **Data:** 08/10/2026. **Plano seguido:** [plano-de-incidentes.md](../lgpd/plano-de-incidentes.md). **Conta usada:** conta de teste de perfil Colaborador (usuário 15).

### Cenário

O token de uma sessão da conta de teste vazou. Uma segunda sessão, a do titular legítimo, continua em uso.

### Percurso pelo plano

| Etapa do plano | O que foi feito | Resultado |
|---|---|---|
| **Situação** | O "atacante" usou o token vazado | `auth/me` e `meu_perfil_colaborador` responderam 200 (sessão 46) |
| **Detecção** (seção 2) | O Admin consultou `GET auditoria` filtrando pela conta | 18 eventos `login_sucesso`; os dois últimos com **10 segundos de diferença**, o sinal de dois acessos quase simultâneos |
| **Avaliação** (seção 3) | Classificação do risco | **Baixo**: conta de teste, dados fictícios, nenhum dado sensível, financeiro ou de menor, uma pessoa. Sem comunicação à ANPD; decisão registrada |
| **Contenção** (seção 4) | O titular revogou a sessão suspeita com o próprio token | `auth/sessoes/46/encerrar` → 200 |
| **Verificação** | O token vazado foi usado de novo | `auth/me` → 401 "Sessao encerrada ou expirada."; `meu_perfil_colaborador` → 401 |
| | O token do titular | Continuou válido (200) |
| **Registro** (seção 6) | Evento na auditoria | 1 evento `encerrar_sessao` para a sessão 46 |

### Registro interno (modelo da seção 6)

| Campo | Conteúdo |
|---|---|
| Identificador | EX-2026-001 |
| Datas | Ocorrência, descoberta, contenção e encerramento: 08/10/2026 (exercício) |
| Quem detectou e como | Administrador, pela consulta à auditoria |
| Descrição | Token de sessão da conta de teste usado em paralelo à sessão do titular |
| Dados e titulares afetados | Nenhum dado real; uma conta de teste |
| Nível de risco | Baixo (simulação) |
| Contenção | Revogação da sessão pelo titular; efeito imediato nos endpoints |
| Comunicação | ANPD: não (sem risco real). Titulares: não |
| Causa e prevenção | Simulada. Em incidente real: investigar como o token vazou e trocar a senha da conta |

### O que o exercício mostrou

1. **A contenção funciona e é imediata**, porque todo endpoint autenticado confere a sessão do token. Esse era justamente o ponto fraco antes da guarda de acesso: o token valia por 1 hora mesmo depois do logout.
2. **A consulta à auditoria exige token válido de RH ou Admin** (vale 1 hora). Em uma resposta real, a pessoa que investiga precisa estar logada.
3. **A auditoria devolve os eventos mais recentes primeiro**, sem paginação; numa investigação longa, use os filtros de usuário e ação.

### Verificação

Este arquivo não contém e-mail, token, CPF nem nome real.
