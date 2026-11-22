# Design

## Decisões

- **D1. Só o YouTube no vídeo:**
  - `validar_video` recusa o link do Drive com a orientação de usar o YouTube.
  - O backend exige `video_fonte = youtube` quando há vídeo. O padrão da fonte passa a ser `youtube`.
- **D2. Registro antigo:**
  - O enum `video_fonte` continua com `drive`, sem mudança de schema.
  - Na tela da pessoa, um vídeo `drive` mostra o aviso e não chama nenhuma API do Google.
  - No modal do RH, editar esse treinamento pede trocar o link antes de salvar.
- **D3. Player:** o componente continua com o caminho `<video>` genérico, sem uso. Mexer no JavaScript sem teste automático seria um risco maior que o benefício.
- **D4. Google continua como operador:** os links do Drive e do Slides, o YouTube e as miniaturas são abertos pelo navegador de quem usa. Só sai a API do Drive (`www.googleapis.com/drive/v3`).
