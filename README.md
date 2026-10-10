# Bot de Reação Automática para Discord

Bot em Python (discord.py) que reage automaticamente com um emoji a cada mensagem enviada em canais configurados. Cada servidor escolhe o canal e o emoji, e tudo fica salvo em um arquivo JSON.

## Recursos

- Configuração por servidor e por canal
- Emoji escolhido por quem configura (padrão ou customizado)
- Comandos slash (`/`)
- Persistência em `config.json`
- Apenas membros com a permissão **Gerenciar Servidor** podem configurar

## Comandos

| Comando | Descrição |
|---|---|
| `/autoreact canal:<#canal> emoji:<emoji>` | Define o emoji que o bot usará para reagir no canal |
| `/autoreact_remover canal:<#canal>` | Remove a reação automática do canal |

Exemplo: `/autoreact canal:#geral emoji:🔥`

## Requisitos

- Python 3.8 ou superior
- Um bot criado no [Discord Developer Portal](https://discord.com/developers/applications)

## Instalação

1. Clone ou baixe o projeto e entre na pasta:

   ```bash
   cd nome-da-pasta
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python -m venv venv
   ```

   - Windows (PowerShell): `venv\Scripts\Activate.ps1`
   - Windows (CMD): `venv\Scripts\activate.bat`
   - Linux/Mac: `source venv/bin/activate`

3. Instale as dependências:

   ```bash
   pip install -U discord.py
   ```

## Configuração do bot

1. No Developer Portal, abra seu app, vá na aba **Bot** e copie o **token**.
2. Ainda na aba **Bot**, ative o **Message Content Intent**.
3. Defina o token como variável de ambiente:

   - Linux/Mac: `export DISCORD_TOKEN="seu_token"`
   - Windows (PowerShell): `$env:DISCORD_TOKEN="seu_token"`
   - Windows (permanente): `setx DISCORD_TOKEN "seu_token"`

4. Convide o bot ao servidor em **OAuth2 → URL Generator**:
   - Escopos: `bot` e `applications.commands`
   - Permissões: **Add Reactions** e **Read Message History**

> Nunca compartilhe o token nem o envie para o GitHub.

## Executando

```bash
python bot.py
```

Quando aparecer `Logado como NomeDoBot`, o bot está online. Os comandos slash podem levar alguns instantes para aparecer no Discord na primeira execução.

## Como os dados são salvos

As configurações ficam em `config.json`, criado automaticamente, neste formato:

```json
{
    "ID_DO_SERVIDOR": {
        "ID_DO_CANAL": "🔥"
    }
}
```

Emojis customizados são salvos no formato `<:nome:id>`.

## Estrutura do projeto

```
.
├── bot.py          # código do bot
├── config.json     # configurações (gerado automaticamente)
├── README.md
└── venv/           # ambiente virtual (não versionar)
```

## Solução de problemas

- **Comandos não aparecem:** confirme que o bot foi convidado com o escopo `applications.commands` e aguarde alguns minutos.
- **Bot não reage:** verifique se ele tem permissão de **Add Reactions** no canal e se o **Message Content Intent** está ativo.
- **Emoji customizado não funciona:** o emoji precisa ser de um servidor em que o bot está presente.
- **Erro de token:** confira se a variável `DISCORD_TOKEN` está definida no mesmo terminal em que você roda o bot.

## Dica para Git

Crie um `.gitignore` com:

```
venv/
config.json
__pycache__/
```
