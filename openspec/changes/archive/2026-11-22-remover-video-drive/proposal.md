# Remover o vídeo pelo Google Drive dos treinamentos

## Por quê

O vídeo do treinamento pelo Google Drive depende de uma chave de API do Google (`[google] drive_api_key`), que não está configurada no app publicado. Hoje um vídeo do Drive não toca, e a pessoa vê "falta configurar o Google Drive".

Decisão do dono do produto (22/11/2026): tirar só esse caminho. Continuam:
- o vídeo pelo YouTube, sem chave;
- os links do Drive e do Google Slides para PDF e apresentação;
- as miniaturas das capas.

## O que muda

- **Modal do RH:** o vídeo aceita só link do YouTube (não listado). Link do Drive é recusado, com orientação.
- **Backend:** `treinamentos` POST e `treinamentos/{id}` PATCH recusam vídeo de outra fonte que não o YouTube.
- **Treinamento antigo com vídeo do Drive:** não tenta tocar. Para quem assiste, mostra o aviso para o RH trocar pelo link do YouTube.
- **Código e configuração:** sai o `frontend/drive_video.py` e a seção `[google]` dos secrets.
- **Documentação:** deploy, LGPD (operadores e aviso de privacidade), regras de negócio e a documentação técnica e do usuário.

## Impacto

- **Para o RH:** treinamentos com vídeo do Drive, se existirem, precisam ter o link trocado pelo do YouTube para voltar a tocar.
- **Banco:** não muda; o enum `video_fonte` continua aceitando `drive` para os registros antigos.
