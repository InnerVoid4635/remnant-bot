# 🤖 Remnant Bot

Bot para Discord desenvolvido em Python com suporte a comandos de prefixo (`*`) e slash commands (`/`).

---

## ⚙️ Tecnologias

- [Python](https://www.python.org/) — linguagem principal
- [discord.py](https://discordpy.readthedocs.io/) — framework do bot
- [aiosqlite](https://aiosqlite.omnilib.dev/) — banco de dados assíncrono
- [python-dotenv](https://pypi.org/project/python-dotenv/) — variáveis de ambiente

---

## 📦 Funcionalidades

### 🛡️ Moderação (`admin`)
- `*clear` / `/clear` — apaga mensagens do canal
- `*kick` / `/kick` — expulsa um membro do servidor
- `*ban` / `/ban` — bane um membro do servidor
- `*reloadall [True]` — recarrega todos os módulos (True sincroniza slash commands)

### 📢 Embeds (`embed_builder`)
- `*embed` / `/embed` — cria e envia um embed personalizado para um canal
- `/embed` — abre modal interativo para criar o embed
- `*embed #canal | Título | Descrição | Cor` — cria embed via prefixo
- `*template [nome] [#canal]` — carrega um template salvo (sem nome lista os disponíveis)
- `*template_delete nome` — deleta um template salvo
- Templates são salvos em `templates/` como arquivos `.json`

### 🔍 Informações (`info`)
- `*scan` / `/scan` — exibe perfil detalhado de um usuário
- `*avatar` / `/avatar` — mostra o avatar ampliado de um membro
- `*server` / `/server` — exibe informações do servidor

### 🛠️ Geral (`geral`)
- `*ping` / `/ping` — latência e uptime do bot
- `*help` / `/help` — lista todos os comandos disponíveis
- `/info` — estatísticas técnicas do bot

### 📋 Logs do Servidor (`logs`)
- Registra mensagens apagadas
- Registra edições de mensagens
- Registra bans e saídas de membros
- Envia logs para o canal definido em `LOG_CHANNEL_ID`

### 🗃️ Arquivo (`archive`)
- Salva todas as mensagens do servidor no banco de dados SQLite automaticamente

### 📊 Verbose (`verbose`)
- Sistema de logging local com 4 arquivos separados em `logs/`
- `commands.log` — todos os comandos executados
- `events.log` — eventos do servidor (ban, kick, saída, embeds)
- `errors.log` — erros e exceções
- `system.log` — inicialização, reload, banco de dados

---

## 🗂️ Estrutura do Projeto

```
📁 meu bot/
├── bot.py               # Inicialização e configuração principal
├── verbose.py           # Sistema de logging local
├── .env                 # Variáveis de ambiente (não versionar)
├── bot.db               # Banco de dados SQLite
├── templates/           # Templates de embeds em JSON
├── logs/                # Arquivos de log gerados pelo verbose
└── cogs/
    ├── admin/
    │   ├── admin.py
    │   └── embed_builder.py
    ├── system/
    │   ├── events.py
    │   ├── logs.py
    │   └── archive.py
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
LOG_CHANNEL_ID=id_do_canal_de_logs
```

**4. Inicie o bot**
```bash
python bot.py
```

---

## 📝 Changelog

### v3.0.0
- Migração para `hybrid_command` em todos os módulos — elimina duplicata prefixo/slash
- Adicionado `verbose.py` com logging local em 4 arquivos separados
- Adicionado `archive.py` — salva mensagens no banco de dados automaticamente
- Sistema de templates JSON para embeds (`*template`, `/template`, `*template_delete`)
- `/embed` agora abre modal com opção de salvar como template
- Correção do bug de mensagens duplicadas no Discord
- Adicionadas tabelas `chat_logs` no banco de dados

### v2.0.0
- Migração completa para `aiosqlite` (banco assíncrono)
- Adicionados slash commands em todos os módulos
- Refatoração: events movidos para `cogs/system/events.py`
- Reorganização das pastas de cogs em `admin/`, `system/` e `utility/`
- Adicionado `embed_builder` com suporte a modal interativo
- `reloadall` agora suporta sincronização opcional da árvore (`*reloadall True`)
- Remoção do `database.py` legado

### v1.0.0
- Estrutura inicial do bot
- Comandos de prefixo: `clear`, `kick`, `ban`
- Log básico de comandos com `sqlite3`