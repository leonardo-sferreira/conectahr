# Proposal

## Why

Em 07/10/2026 foi feito um mapeamento de conformidade com a LGPD (Lei nº 13.709/2018) sobre o `master`. Ele cobriu a spec, os artefatos OpenSpec, `docs/`, as 49 tabelas, os 178 endpoints do Xano e o frontend Streamlit.

A conclusão foi que o projeto protege bem o **acesso** aos dados (perfil × escopo no backend, campos privados, dados bancários fora do alcance do Gestor), mas não tem a **governança** que a LGPD exige. Hoje a LGPD aparece só como frase genérica no `AGENTS.md`, no `docs/project-overview.md`, no `proposal.md` do `conectarh.gestao` e no `openspec/config.yaml`. As regras da CLT, do eSocial e do MTE foram mapeadas em detalhe; as da LGPD, não.

O mapeamento também achou falhas concretas no código:
- dados bancários completos gravados na auditoria;
- abertura de arquivo sensível sem auditoria;
- motivo de ausência em texto livre, que pode receber diagnóstico;
- links de arquivo sem controle;
- códigos de acesso em texto puro;
- indicadores de grupos tão pequenos que revelam quem faltou ou adoeceu.

As Partes 1 a 3 precisam estar prontas antes da demonstração de dezembro.

## What Changes

**Parte 1: documentação e governança** (só documentos, em `docs/lgpd/`)
- Registro das operações de tratamento, aviso de privacidade, encarregado com contato publicado, plano de resposta a incidentes, relatório de impacto (RIPD), operadores e transferência internacional, e teste de legítimo interesse.
- Requisitos de proteção de dados na spec da capability `conectahr`, com cenários testáveis.
- Regras práticas no `AGENTS.md`.
- No `project-overview.md` e no `config.yaml`, a frase genérica vira link para `docs/lgpd/`.

**Parte 2: ajustes no backend**
- Dados pessoais mascarados na auditoria, começando pelos dados bancários.
- Auditoria da abertura de arquivo de documento, de comprovante de ausência e de documento de SST.
- **BREAKING:** o motivo da ausência passa a ser uma lista fechada. O texto livre não é mais aceito, e os registros existentes são migrados sem perda de histórico.
- `arquivo_url` e `documento_url` só aceitam o armazenamento privado do Xano ou domínios aprovados.
- Códigos de login e de redefinição gravados só como hash.
- Indicadores e exportação omitem grupos abaixo de um mínimo de pessoas (padrão 5).
- Registro de que as tarefas 1.4 a 1.9 da `corrigir-brechas-e-alinhar-documentacao` são pré-requisito de segurança (art. 46).

**Parte 3: direitos do titular**
- `meus_dados GET`: o próprio colaborador baixa seus dados em JSON e CSV, com auditoria.
- Novo tipo `privacidade_lgpd` na central de solicitações, com subtipos, prazo de 15 dias e alerta ao RH.
- `minhas_preferencias_privacidade GET/PATCH`: sair da lista de aniversariantes e do mural público.
- Tela "Privacidade" no Figma e no Streamlit, e link para o aviso na tela Entrar.

**Parte 4: retenção, anonimização e adolescentes** (pós-MVP, se não couber até dezembro)
- Prazos de guarda por categoria, todos "a confirmar com o jurídico".
- Limpeza de sessões e `email_outbox` vencidos na rotina diária.
- `colaboradores/{id}/anonimizar POST` para desligado com prazo de guarda cumprido.
- Regras para adolescentes aprendizes.
- Confirmação de criptografia em repouso.
- Regra de mascaramento para `docs/evidencias/`.

**Non-goals**
- Parecer jurídico formal. Bases legais e prazos ficam marcados "a confirmar com o jurídico".
- Certificações (ISO 27001 e similares).
- Consentimento como base legal para dados trabalhistas. Ele não é adequado na relação de emprego; usamos contrato, obrigação legal ou legítimo interesse.
- Criar campos de raça, sexo, religião, filiação sindical ou biometria.
- Exclusão física de dados. Quando o prazo de guarda termina, os dados pessoais são anonimizados.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `conectahr`: novos requisitos de proteção de dados, que correspondem à seção "12. Proteção de Dados (LGPD)" da spec do `conectarh.gestao`. Cobrem transparência, direitos do titular, dados sensíveis, mascaramento na auditoria, controle de arquivos, retenção e anonimização, incidentes, adolescentes e operadores.

  A capability `conectahr` ainda não existe em `openspec/specs/`. Ela é criada pelos changes `conectarh.gestao` e `implementar-frontend-streamlit` e ampliada pela `corrigir-brechas-e-alinhar-documentacao`, nenhum deles arquivado ainda. Esta change é arquivada **depois** da `corrigir-brechas-e-alinhar-documentacao`.

## Impact

- **Documentação:** nova pasta `docs/lgpd/` com 7 documentos. Também mudam `AGENTS.md`, `README.md` (contato do encarregado), `docs/project-overview.md`, `openspec/config.yaml`, `docs/regras-de-negocio.md` e `docs/evidencias/README.md`.
- **Backend Xano:**
  - endpoints alterados: `meus_dados_bancarios PATCH` e as demais auditorias com dado pessoal, `documentos/{id}/arquivo GET`, os endpoints de ausência e de SST, `auth/login`, `auth/otp/*`, `auth/senha/*`, `indicadores GET`, `indicadores/exportar_csv GET`, `colaboradores/aniversariantes GET`, `mural_reconhecimento GET`, `solicitacoes`, `central_de_tarefas` e `rotinas/processar_diarias`;
  - endpoints novos: `meus_dados GET`, `minhas_preferencias_privacidade GET/PATCH` e `colaboradores/{id}/anonimizar POST`;
  - schema: campos novos, a lista fechada de motivos de ausência e a migração dos registros existentes.
- **Frontend:** tela "Privacidade" (desenhada no Figma antes) e link para o aviso de privacidade na tela Entrar.
- **Processo:** um novo serviço externo, ou um novo campo de dado sensível, passa a exigir a atualização do registro de operações e da lista de operadores.
- **Dependência:** tarefas 1.4 a 1.9 da `corrigir-brechas-e-alinhar-documentacao`.
