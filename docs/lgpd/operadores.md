# Operadores e transferência internacional de dados

**Referência:** LGPD, arts. 33 a 39 (transferência internacional e operadores); Resolução CD/ANPD nº 19/2024.
**Situação:** levantamento técnico de 08/10/2026. **Regiões, contratos de tratamento de dados e mecanismos de transferência estão "a confirmar"** onde o projeto ainda não tem a informação: este documento não afirma o que não foi conferido.

**Operador** é o serviço de terceiros que trata dados pessoais em nome da empresa. **Transferência internacional** acontece quando os dados vão para um serviço que os processa ou guarda fora do Brasil; nesse caso, é preciso um mecanismo previsto na LGPD e na Resolução 19/2024 (decisão de adequação, cláusulas-padrão contratuais, ou outro).

Os códigos F01, F02… são as finalidades do [registro de operações](registro-de-operacoes.md).

## Serviços que recebem dados pessoais

| Serviço | Para quê | Dados que recebe | Finalidades | Região | Termos de tratamento de dados | Mecanismo de transferência internacional |
|---|---|---|---|---|---|---|
| **Xano** (backend) | Banco de dados e regras de negócio (o sistema não guarda arquivo: o upload foi retirado, tarefa 4.27) | **Todos** os dados do sistema, inclusive sensíveis (saúde) | F01 a F19 | Criptografia em repouso: **sim**, AES-256 no nível do armazenamento, segundo a documentação oficial do Xano (consultada em 08/10/2026; não confirmada no painel). Região: o painel do plano gratuito não mostra; pelo endereço IP da instância `x8ki-letl-twmt`, o servidor é da **Google Cloud em Council Bluffs, Iowa (EUA)** (inferência de 09/10/2026, a confirmar com o fornecedor) | **A confirmar**: se existe um acordo de tratamento de dados (DPA) aceito pela empresa | **A confirmar** (provável transferência internacional; cláusulas-padrão da Res. 19/2024 se o serviço estiver fora do Brasil) |
| **Brevo** (e-mail transacional) | Envio do código de acesso, da redefinição de senha e dos avisos | Nome, e-mail e o **conteúdo da mensagem** (código e texto do aviso) | F01, F17 | **A confirmar.** A empresa é sediada na França; a região de processamento não foi verificada | **A confirmar** (DPA do fornecedor) | **A confirmar** (verificar decisão de adequação aplicável ou cláusulas-padrão) |
| **Supabase Storage** (arquivos dos documentos; change `anexo-de-arquivos`, 13/10/2026) | Guarda os arquivos que a pessoa anexa em Documentos (PDF ou foto), num bucket **privado** `documentos`. Desde 23/10/2026, também a **foto de perfil** opcional, no bucket privado `fotos-perfil` (change `foto-de-perfil`), aberta só por URL assinada de 10 minutos | O **arquivo do documento** (RG, CPF, CNH, CTPS, comprovantes, ASO etc.), com nome aleatório (UUID), sem nome nem CPF no caminho. Também os materiais de leitura geral dos benefícios (guias, tabelas), sem dado pessoal, na pasta `beneficios/` (change `apresentacao-de-beneficios`). Recebe do servidor do Streamlit (envio) e do Xano (geração dos links) | F04 e F10 (documentos e ASO) | Projeto a criar na região **São Paulo (`sa-east-1`)**, decisão D7 da change; **a confirmar** no painel depois da criação | **A confirmar**: DPA do Supabase aceito pela empresa | Se o projeto ficar em São Paulo, não há transferência internacional do arquivo; **a confirmar** o que o fornecedor processa fora do Brasil (painel, logs) |
| **Hospedagem do aplicativo Streamlit** | Serve as telas e guarda o token da sessão na memória do servidor do aplicativo | Tudo que aparece nas telas e o token de sessão, em memória, durante o uso | F01 a F19 | **A confirmar.** O repositório não define onde o app é publicado | **A confirmar** | **A confirmar** |
| **YouTube** (vídeos dos treinamentos, segunda opção; change `treinamento-em-video`, 21/10/2026) | Toca os vídeos "não listados" em "Meus treinamentos" e na prévia do RH (player incorporado em `youtube-nocookie.com`) | O **endereço IP e dados do navegador** de quem assiste, e o que a pessoa faz no player. O modo `nocookie` não grava cookie de rastreamento antes do play. O progresso e a conclusão ficam no Xano | F12 | **A confirmar** (Google, provavelmente fora do Brasil) | Termos do YouTube da conta da empresa | **A confirmar** (provável transferência internacional do IP) |
| **Google Drive** (vídeos dos treinamentos; change `treinamento-em-video`, 21/10/2026) | Guarda os vídeos de treinamento, no Drive da empresa, e os entrega ao navegador de quem assiste em "Meus treinamentos" (API do Drive, `www.googleapis.com`) | O **endereço IP e dados do navegador** de quem assiste, e a hora. O vídeo é material de treinamento, **sem dado pessoal**; o progresso e a conclusão ficam no Xano, não no Google | F12 | **A confirmar** (Google, provavelmente fora do Brasil) | **A confirmar**: termos do Google Workspace ou do Google Cloud da empresa | **A confirmar** (provável transferência internacional do IP) |
| ~~Google Fonts~~ (**retirado em 10/10/2026**) | Fornecia as fontes Sora e Manrope, carregadas do navegador (`fonts.googleapis.com`) | Recebia o **endereço IP e dados do navegador** de quem abria o sistema | — | — | — | **Não se aplica mais:** as fontes agora são servidas pelo próprio aplicativo (`frontend/static/fonts`, licença OFL; tarefa 4 da change `concluir-frontend-streamlit`). Conferido no navegador: nenhuma requisição a `googleapis.com` ou `gstatic.com` |
| **GitHub** (código) | Guarda o código, o histórico e as discussões. **O repositório é público** | Nome e e-mail dos autores dos commits (a equipe). **Não deve receber nenhum dado pessoal de colaboradores** | Fora do sistema (desenvolvimento) | Estados Unidos | Termos do GitHub | Aplicável aos dados da equipe; regra do projeto: nada de dado pessoal, senha ou token no repositório |
| **Figma** (design) | Protótipos e design system | Nomes de exemplo e **um e-mail real** que aparece no texto do protótipo | Fora do sistema (design) | Estados Unidos | Termos do Figma | **Trocar os dados do protótipo por exemplos fictícios** (ver pendências) |
| **Assistentes de IA de desenvolvimento** (Claude Code, Codex, Gemini CLI) | Apoio à escrita de código e documentação | O que a equipe colar ou deixar ao alcance deles: código e arquivos do projeto. **Podem receber dado pessoal se alguém colar** | Fora do sistema (desenvolvimento) | Conforme cada provedor | Termos de cada provedor | **Regra do projeto: não fornecer dado pessoal real** a esses assistentes |

## O serviço de arquivos citado no sistema

Os campos `documento.arquivo_url` e `evento_sst.documento_url` aceitam hoje **qualquer endereço**, de **nenhum serviço específico**. A regra (tarefa 4.12, em vigor) aceita só `https` do próprio Xano ou de domínios de uma lista aprovada (`ARQUIVOS_DOMINIOS_APROVADOS`), que **começa vazia**. O Supabase Storage foi aprovado em 13/10/2026 (change `anexo-de-arquivos`): o host do projeto entra nessa lista e os arquivos anexados em Documentos ficam no bucket privado dele, nunca no Xano. A chave do Supabase fica só no ambiente do Xano. Links de compartilhamento de nuvem continuam recusados.

## Lista de verificação: serviços externos citados no código e no README

Resultado da busca por endereços externos em `xano-workspace/`, `frontend/`, `README.md` e `.streamlit/config.toml`:

| Endereço encontrado | O que é | Recebe dado pessoal? | Está na lista? |
|---|---|---|---|
| `api.brevo.com` | API de e-mail do Brevo | Sim | Sim (Brevo) |
| `www.brevo.com` | Link no README | Não | Brevo |
| `xano.com`, `app.xano.com`, instância `*.xano.io` | Plataforma do backend | Sim | Sim (Xano) |
| ~~`fonts.googleapis.com`~~ | Fontes, carregadas do navegador até 10/10/2026 | Não mais: o endereço saiu do código | Retirado (Google Fonts) |
| `streamlit.io` | Link no README (tecnologia) | Não; a **hospedagem** está na lista | Sim (hospedagem) |
| `github.com` | Link e repositório | Dados da equipe | Sim (GitHub) |
| `www.w3.org` | Identificador de formato (SVG), sem acesso à rede | Não | Não se aplica |
| `your-instance.xano.io` | Texto de exemplo na documentação | Não | Não se aplica |
| `brasilapi.com.br` | API pública: feriados nacionais (`ConectaHR/importar_feriados_nacionais`, desde 12/10/2026) e busca de endereço pelo CEP (`frontend/cep.py`, desde 13/10/2026, chamada pelo servidor do Streamlit) | **Não** como dado identificado: a consulta leva só o ano ou só o CEP, sem nome nem outro dado da pessoa | Sim |
| `www.youtube.com/iframe_api`, `www.youtube-nocookie.com` | Player do YouTube para os vídeos dos treinamentos (`frontend/video_player.py`, desde 21/10/2026) | O **IP de quem assiste** (o pedido sai do navegador); nenhum dado de cadastro | Sim (YouTube) |
| `www.googleapis.com/drive/v3` | Vídeos dos treinamentos no Google Drive (`frontend/drive_video.py`, desde 21/10/2026): o navegador toca o vídeo e o servidor do app lê a duração ao salvar | O **IP de quem assiste** (o pedido sai do navegador); nenhum dado de cadastro | Sim (Google Drive) |
| `viacep.com.br` | Busca de endereço pelo CEP quando a BrasilAPI não responde (`frontend/cep.py`, desde 13/10/2026) | **Não** como dado identificado: só o CEP vai na consulta | Sim |

Para repetir a busca: `grep -rhoE "https?://[A-Za-z0-9._-]+" xano-workspace frontend README.md .streamlit/config.toml`.

## Pendências

1. **Confirmar com o fornecedor a região** do Xano (inferida como Iowa, EUA, pelo IP) e tratar a **transferência internacional** de dados para os EUA (cláusulas-padrão ou outra hipótese da Resolução CD/ANPD nº 19/2024). A criptografia em repouso já consta na documentação oficial do fornecedor.
2. **Confirmar, com o fornecedor, o acordo de tratamento de dados** do Xano, do Brevo e da hospedagem do Streamlit.
3. **Definir onde o aplicativo Streamlit é hospedado** e completar a linha correspondente.
4. **Hospedar as fontes localmente** (tarefa 3.50), o que elimina o envio do IP ao Google.
5. **Trocar os exemplos do protótipo do Figma por dados fictícios**, sem e-mail de pessoa real.
6. Revisar este documento sempre que um **novo serviço externo** passar a receber dados: ele entra aqui antes de receber o primeiro dado.
7. **Google Drive e YouTube (vídeos dos treinamentos):** confirmar os termos de tratamento da conta Google da empresa e a região. As cópias do aviso de privacidade no Figma ainda não citam o Google (o documento já cita).
