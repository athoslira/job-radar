# Configurar o Telegram

O código já está preparado para centralizar **Dados/BI** e **CX** em um
único bot e um único chat. Você só precisa fornecer duas credenciais.

## 1. Criar o bot

1. Abra [@BotFather](https://t.me/BotFather) no Telegram.
2. Envie `/newbot`.
3. Escolha o nome e o usuário do bot.
4. Copie o token entregue pelo BotFather.

## 2. Descobrir o ID do chat

1. Abra uma conversa com o bot criado.
2. Selecione **Iniciar** ou envie qualquer mensagem.
3. No navegador, abra a URL abaixo, substituindo `SEU_TOKEN`:

   ```text
   https://api.telegram.org/botSEU_TOKEN/getUpdates
   ```

4. Procure por `"chat":{"id":...}` e copie o número de `id`.

## 3. Configurar no GitHub

No repositório, abra **Settings → Secrets and variables → Actions** e crie
estes dois *repository secrets*:

- `TELEGRAM_BOT_TOKEN`: token recebido do BotFather.
- `TELEGRAM_CHAT_ID`: ID numérico obtido no passo anterior.

Depois abra **Actions → JobRadar → Run workflow** para executar o primeiro
ciclo manualmente. As próximas execuções acontecem automaticamente a cada
três horas.

Nunca publique o arquivo `.env` nem cole o token em código ou em mensagens.
O `.gitignore` deste projeto já impede o versionamento acidental do `.env`.
