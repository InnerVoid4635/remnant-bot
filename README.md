# 🤖 Remnant Bot

Bot para Discord desenvolvido em Python com suporte a comandos de prefixo (`*`) e slash commands (`/`).

---

## ⚙️ Tecnologias

- [Python](https://www.python.org/) — linguagem principal
- [discord.py](https://discordpy.readthedocs.io/) — framework do bot
- [aiosqlite](https://aiosqlite.omnilib.dev/) — banco de dados assíncrono
- [python-dotenv](https://pypi.org/project/python-dotenv/) — variáveis de ambiente
- [aioconsole](https://pypi.org/project/aioconsole/) — terminal interativo assíncrono

---

## 📦 Funcionalidades

### 🛡️ Moderação (`admin`)
- `*clear` / `/clear` — apaga mensagens do canal
- `*kick` / `/kick` — expulsa um membro do servidor
- `*ban` / `/ban` — bane um membro do servidor

### 👑 Dono (`owner`)
- `*reloadall [True]` — recarrega todos os módulos (True sincroniza slash commands)

### 📢 Embeds (`embed_builder`)
- `*embed` / `/embed` — cria e envia um embed personalizado para um canal
- `/embed` — abre modal interativo com opção de salvar como template
- `*embed #canal | Título | Descrição | Cor` — cria embed via prefixo
- `*template [nome] [#canal]` — lista ou carrega um template salvo
- `*template_delete nome` — deleta um template salvo
- Templates salvos em `templates/` como arquivos `.json`

### 🔍 Informações (`info`)
- `*scan` / `/scan [membro]` — exibe perfil detalhado de um usuário
- `*avatar` / `/avatar [membro]` — mostra o avatar ampliado de um membro
- `*server` / `/server` — exibe informações do servidor

### 🛠️ Geral (`geral`)
- `*ping` / `/ping` — latência e uptime do bot
- `*help` / `/help` — lista todos os comandos disponíveis
- `/info` — estatísticas técnicas do bot

### 📋 Logs do Servidor (`logs`)
- Canal de log configurável por servidor via `*setlog #canal`
- `*setlog #canal` — define o canal de log do servidor (admin)
- `*unsetlog` — remove o canal de log do servidor (admin)
- Registra mensagens apagadas, edições, bans e saídas de membros
- Todos os logs são enviados também via DM para o dono do bot
- Configuração persistida em `log_channels.json` por servidor

### 📡 Eventos (`events`)
- Notifica o dono via DM quando o bot é adicionado a um novo servidor
- Registra todos os comandos executados no banco de dados SQLite

### 📊 Verbose (`verbose`)
- Sistema de logging local com 4 arquivos separados em `logs/`
- `commands.log` — todos os comandos executados
- `events.log` — eventos do servidor (ban, kick, saída, embeds)
- `errors.log` — erros e exceções
- `system.log` — inicialização, reload, banco de dados

### 💻 Terminal Interativo
- `status` — uptime, servidores e latência
- `reload` — recarrega todos os módulos
- `stop` — desliga o bot
- `clear` — limpa o terminal

---

## 🗂️ Estrutura do Projeto

```
📁 meu bot/
├── bot.py               # Inicialização, terminal interativo e configuração principal
├── verbose.py           # Sistema de logging local
├── .env                 # Variáveis de ambiente (não versionar)
├── bot.db               # Banco de dados SQLite
├── log_channels.json    # Canais de log por servidor (não versionar)
├── templates/           # Templates de embeds em JSON
├── logs/                # Arquivos de log gerados pelo verbose (não versionar)
└── cogs/
    ├── admin/
    │   ├── admin.py
    │   └── embed_builder.py
    ├── system/
    │   ├── events.py
    │   ├── logs.py
    │   └── owner.py
    └── utility/
        ├── geral.py
        └── info.py
```

---

## 🚀 Como Rodar

**1. Clone o repositório**
```bash
git clone https://github.com/InnerVoid4635/remnant-bot.git
cd remnant-bot
```

**2. Instale as dependências**
```bash
pip install -r requirements.txt
```

**3. Configure o `.env`**
```env
TOKEN=seu_token_aqui
```

**4. Inicie o bot**
```bash
python bot.py
```

**5. Defina o canal de log em cada servidor**
```
*setlog #canal-de-logs
```

---

## 📝 Changelog

### v4.0.0
- `reloadall` movido para `owner.py` — protegido com `is_owner()`
- Canal de log agora é configurável por servidor via `*setlog` e `*unsetlog`
- Logs enviados via DM para o dono do bot em tempo real
- Adicionado `on_guild_join` — notifica o dono quando o bot entra em novo servidor
- Terminal interativo com `aioconsole` (`status`, `reload`, `stop`, `clear`)
- Embeds de log melhorados com avatar, thumbnail e informações do servidor
- `LOG_CHANNEL_ID` removido do `.env` — substituído por `log_channels.json`

### v3.0.0
- Migração para `hybrid_command` em todos os módulos — elimina duplicata prefixo/slash
- Adicionado `verbose.py` com logging local em 4 arquivos separados
- Sistema de templates JSON para embeds
- `/embed` agora abre modal com opção de salvar como template
- Correção do bug de mensagens duplicadas no Discord

### v2.0.0
- Migração completa para `aiosqlite` (banco assíncrono)
- Adicionados slash commands em todos os módulos
- Reorganização das pastas de cogs em `admin/`, `system/` e `utility/`
- Adicionado `embed_builder` com suporte a modal interativo
- Remoção do `database.py` legado

### v1.0.0
- Estrutura inicial do bot
- Comandos de prefixo: `clear`, `kick`, `ban`
- Log básico de comandos com `sqlite3`