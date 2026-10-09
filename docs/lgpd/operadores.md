# Operadores e transferência internacional de dados

**Referência:** LGPD, arts. 33 a 39 (transferência internacional e operadores); Resolução CD/ANPD nº 19/2024.
**Situação:** levantamento técnico de 08/10/2026. **Regiões, contratos de tratamento de dados e mecanismos de transferência estão "a confirmar"** onde o projeto ainda não tem a informação: este documento não afirma o que não foi conferido.

**Operador** é o serviço de terceiros que trata dados pessoais em nome da empresa. **Transferência internacional** acontece quando os dados vão para um serviço que os processa ou guarda fora do Brasil; nesse caso, é preciso um mecanismo previsto na LGPD e na Resolução 19/2024 (decisão de adequação, cláusulas-padrão contratuais, ou outro).

Os códigos F01, F02… são as finalidades do [registro de operações](registro-de-operacoes.md).

## Serviços que recebem dados pessoais

| Serviço | Para quê | Dados que recebe | Finalidades | Região | Termos de tratamento de dados | Mecanismo de transferência internacional |
|---|---|---|---|---|---|---|
| **Xano** (backend) | Banco de dados e regras de negócio (o sistema não guarda arquivo: o upload foi retirado, tarefa 4.27) | **Todos** os dados do sistema, inclusive sensíveis (saúde) | F01 a F19 | Criptografia em repouso: **sim**, AES-256 no nível do armazenamento, segundo a documentação oficial do Xano (consultada em 08/10/2026; não confirmada no painel). Região: **a confirmar** no painel (instância `x8ki-letl-twmt`; passo a passo na tarefa 4.24) | **A confirmar**: se existe um acordo de tratamento de dados (DPA) aceito pela empresa | **A confirmar** (provável transferência internacional; cláusulas-padrão da Res. 19/2024 se o serviço estiver fora do Brasil) |
| **Brevo** (e-mail transacional) | Envio do código de acesso, da redefinição de senha e dos avisos | Nome, e-mail e o **conteúdo da mensagem** (código e texto do aviso) | F01, F17 | **A confirmar.** A empresa é sediada na França; a região de processamento não foi verificada | **A confirmar** (DPA do fornecedor) | **A confirmar** (verificar decisão de adequação aplicável ou cláusulas-padrão) |
| **Hospedagem do aplicativo Streamlit** | Serve as telas e guarda o token da sessão na memória do servidor do aplicativo | Tudo que aparece nas telas e o token de sessão, em memória, durante o uso | F01 a F19 | **A confirmar.** O repositório não define onde o app é publicado | **A confirmar** | **A confirmar** |
| **Google Fonts** | Fornece as fontes Sora e Manrope. O CSS do aplicativo as carrega direto do navegador (`fonts.googleapis.com`) | **Endereço IP e dados do navegador** de quem abre o sistema | F01 (acesso) | Estados Unidos (a empresa é norte-americana); distribuição global | Termos do Google Fonts | **Há transferência internacional sem necessidade.** Recomenda-se **hospedar as fontes localmente** e remover a dependência (tarefa 3.50) |
| **GitHub** (código) | Guarda o código, o histórico e as discussões. **O repositório é público** | Nome e e-mail dos autores dos commits (a equipe). **Não deve receber nenhum dado pessoal de colaboradores** | Fora do sistema (desenvolvimento) | Estados Unidos | Termos do GitHub | Aplicável aos dados da equipe; regra do projeto: nada de dado pessoal, senha ou token no repositório |
| **Figma** (design) | Protótipos e design system | Nomes de exemplo e **um e-mail real** que aparece no texto do protótipo | Fora do sistema (design) | Estados Unidos | Termos do Figma | **Trocar os dados do protótipo por exemplos fictícios** (ver pendências) |
| **Assistentes de IA de desenvolvimento** (Claude Code, Codex, Gemini CLI) | Apoio à escrita de código e documentação | O que a equipe colar ou deixar ao alcance deles: código e arquivos do projeto. **Podem receber dado pessoal se alguém colar** | Fora do sistema (desenvolvimento) | Conforme cada provedor | Termos de cada provedor | **Regra do projeto: não fornecer dado pessoal real** a esses assistentes |

## O serviço de arquivos citado no sistema

Os campos `documento.arquivo_url` e `evento_sst.documento_url` aceitam hoje **qualquer endereço**, de **nenhum serviço específico**. A regra (tarefa 4.12, em vigor) aceita só `https` do próprio Xano ou de domínios de uma lista aprovada (`ARQUIVOS_DOMINIOS_APROVADOS`), que **começa vazia**. Quando um serviço de arquivos for aprovado, ele entra nesta lista antes de receber qualquer dado. O sistema não recebe arquivo (upload retirado no plano gratuito), então nenhum arquivo fica no armazenamento do Xano.

## Lista de verificação: serviços externos citados no código e no README

Resultado da busca por endereços externos em `xano-workspace/`, `frontend/`, `README.md` e `.streamlit/config.toml`:

| Endereço encontrado | O que é | Recebe dado pessoal? | Está na lista? |
|---|---|---|---|
| `api.brevo.com` | API de e-mail do Brevo | Sim | Sim (Brevo) |
| `www.brevo.com` | Link no README | Não | Brevo |
| `xano.com`, `app.xano.com`, instância `*.xano.io` | Plataforma do backend | Sim | Sim (Xano) |
| `fonts.googleapis.com` | Fontes, carregadas do navegador | **Sim (IP)** | Sim (Google Fonts) |
| `streamlit.io` | Link no README (tecnologia) | Não; a **hospedagem** está na lista | Sim (hospedagem) |
| `github.com` | Link e repositório | Dados da equipe | Sim (GitHub) |
| `www.w3.org` | Identificador de formato (SVG), sem acesso à rede | Não | Não se aplica |
| `your-instance.xano.io` | Texto de exemplo na documentação | Não | Não se aplica |

Para repetir a busca: `grep -rhoE "https?://[A-Za-z0-9._-]+" xano-workspace frontend README.md .streamlit/config.toml`.

## Pendências

1. **Confirmar no painel do Xano a região** (tarefa 4.24) e registrar a resposta na linha do Xano acima. A criptografia em repouso já consta na documentação oficial do fornecedor.
2. **Confirmar, com o fornecedor, o acordo de tratamento de dados** do Xano, do Brevo e da hospedagem do Streamlit.
3. **Definir onde o aplicativo Streamlit é hospedado** e completar a linha correspondente.
4. **Hospedar as fontes localmente** (tarefa 3.50), o que elimina o envio do IP ao Google.
5. **Trocar os exemplos do protótipo do Figma por dados fictícios**, sem e-mail de pessoa real.
6. Revisar este documento sempre que um **novo serviço externo** passar a receber dados: ele entra aqui antes de receber o primeiro dado.
