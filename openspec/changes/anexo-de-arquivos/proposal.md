# Proposal

## Why

Para enviar um documento, a pessoa precisa guardar o arquivo em algum lugar e colar um link https de um domínio aprovado. O usuário apontou (13/10/2026) que isso complica a experiência, principalmente para quem tem menos familiaridade com tecnologia: o esperado é anexar o arquivo ou tirar a foto do documento, e o sistema cuidar do resto. O plano gratuito do Xano não aceita upload de arquivo privado (tarefa 4.27: "Not supported. Please upgrade your Xano instance."), por isso o envio foi feito por link.

## What Changes

- **Anexar arquivo em Documentos:** o modal "Enviar documento" troca o campo "Link do arquivo" por "Arquivo" (PDF, JPG ou PNG, até 10 MB). No celular, o mesmo campo permite tirar a foto na hora.
- **Armazenamento privado no Supabase Storage** (decisão do usuário, 13/10/2026): um bucket privado `documentos`. O arquivo vai do Streamlit direto para o Supabase por um endereço de envio de uso único, gerado pelo Xano. A chave do Supabase fica só no ambiente do Xano.
- **`documentos/envio_arquivo` POST (novo):** gera o endereço de envio e o endereço do arquivo, com nome aleatório (sem dado pessoal no caminho). Auditado.
- **`documentos/{id}/arquivo` GET:** para arquivo guardado no Supabase, devolve um link assinado que vale 5 minutos, com a mesma regra de acesso (dono, RH e Admin) e a mesma auditoria. Links antigos continuam abrindo como hoje.
- **LGPD:** o Supabase entra como operador antes de receber o primeiro arquivo; o risco R1.5 do RIPD volta a ser avaliado.

## Non-goals

- Pagamento (holerite e informe lançados pelo RH) e o comprovante de ausência continuam por link nesta change; podem usar o mesmo envio depois.
- Apagar o arquivo do Supabase quando o documento vence a retenção: fica registrado em `docs/lgpd/retencao.md` como pendência.
- Antivírus ou leitura do conteúdo do arquivo.

## Impact

- Backend: `api/conecta_rh_documentos/documentos/envio_arquivo_POST.xs` (novo), `documentos/id/arquivo_GET.xs`; variáveis de ambiente `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` e `ARQUIVOS_DOMINIOS_APROVADOS` no Xano.
- Frontend: `pagina_documentos.py`, `documentos_modelo.py`, `api_client.py`.
- Figma: modal "Enviar documento" (309:1591, escuro 313:1573) volta a ter o campo "Arquivo".
- Documentação: `AGENTS.md`, `docs/arquitetura.md`, `docs/regras-de-negocio.md`, `docs/lgpd/operadores.md`, `docs/lgpd/ripd.md`, `docs/lgpd/retencao.md`.
