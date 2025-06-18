# Agente IA Discord

![Cobertura de Código](https://img.shields.io/badge/coverage-95%25-brightgreen)

Este projeto é um bot do Discord em Python que lê mensagens e arquivos PDF enviados em um canal e gera resumos inteligentes para diferentes públicos (Comercial, Suporte e PM), utilizando IA e prompts customizáveis.

## Principais Features

- **Leitura de arquivos PDF enviados no canal do Discord**
- **Geração de resumo técnico com IA (Hugging Face)**
- **Adaptação automática do resumo para três públicos distintos:**
  - Comercial (foco em benefícios de negócio)
  - Suporte (foco em instruções práticas e dúvidas de usuários)
  - PM (foco em visão estratégica, roadmap e valor de produto)
- **Prompts customizáveis para cada público, editáveis em arquivos separados**
- **Respostas sempre em português do Brasil, mesmo que o texto original esteja em inglês ou misturado**
- **Comandos separados para cada público ou comando único para todos**
- **Configuração segura via arquivo `.env` (tokens nunca são publicados)**

## Estrutura do Projeto

- `main.py`: Script principal para inicialização.
- `discord_bot.py`: Conexão e leitura do canal do Discord.
- `release_handler.py`: Geração dos 3 documentos.
- `prompts/`: Templates de prompt (`cliente.txt`, `comercial.txt`, `suporte.txt`).
- `outputs/`: Pasta para arquivos gerados.
- `.env`: Chaves de API.

## Requisitos
- Python 3.8+
- Instalar dependências: `pip install -r requirements.txt`

## Execução
1. Configure o arquivo `.env` com as chaves necessárias.
2. Execute: `python main.py`

## Como obter o token Hugging Face para sumarização IA

1. Crie uma conta gratuita em: https://huggingface.co/join
2. Após login, acesse: https://huggingface.co/settings/tokens
3. Clique em “New token”, dê um nome (ex: discord-bot) e selecione o tipo “Read”.
4. Clique em “Generate” e copie o token gerado.
5. No arquivo `.env`, adicione a linha:

   HF_API_TOKEN=seu_token_aqui

Pronto! O bot já pode gerar resumos automáticos usando IA gratuita da Hugging Face.

## Configuração do arquivo .env

Crie um arquivo chamado `.env` na raiz do projeto com o seguinte conteúdo (preencha com seus próprios tokens):

```
DISCORD_TOKEN=seu_token_do_discord
OPENAI_API_KEY=seu_token_openai_opcional
DISCORD_CHANNEL_ID=seu_id_do_canal
HF_API_TOKEN=seu_token_huggingface
```

- **DISCORD_TOKEN**: Token do seu bot do Discord.
- **OPENAI_API_KEY**: (opcional) Token da OpenAI, se for usar recursos do OpenAI.
- **DISCORD_CHANNEL_ID**: ID do canal do Discord onde o bot irá atuar.
- **HF_API_TOKEN**: Token da Hugging Face para sumarização/tradução.

**Importante:**
- Nunca publique seu arquivo `.env` ou compartilhe seus tokens publicamente.
- O arquivo `.env` já está protegido pelo `.gitignore` deste projeto.

## Cobertura de Testes

Este projeto utiliza o [pytest](https://docs.pytest.org/) e [pytest-cov](https://pytest-cov.readthedocs.io/) para garantir cobertura de código.

Veja detalhes e instruções em [COVERAGE.md](COVERAGE.md).

## Comandos Inteligentes

- `!leiapdf <arquivo>`: Processa PDF, gera resumo e adapta para cada público.
- `!ultimaversao`: Mostra o resumo da última versão disponível na pasta outputs.
- `!duvida <sua pergunta>`: Permite perguntar sobre a última versão e recebe resposta da IA baseada no conteúdo do documento mais recente.

## Comandos do Discord

- `!leiapdf <nome_arquivo>` — Gera resumo do PDF e adapta para Comercial, Suporte e Produto.
- `!leiatxt <nome_arquivo>` — Gera resumo de um arquivo TXT.
- `!leiaarquivo <nome_arquivo>` — Lê e mostra o conteúdo de qualquer arquivo suportado (PDF/TXT).
- `!ultimaversao` — Mostra o resumo da última versão disponível na pasta outputs.
- `!duvida <sua pergunta>` — Permite perguntar sobre a última versão e recebe resposta da IA baseada no conteúdo do release mais recente.
- `!versao <nome_ou_data>` — Busca e resume uma versão específica pelo nome do arquivo ou parte dele.
- `!gerarpdf <público>` — (Em breve) Gera e envia um PDF com o resumo adaptado para o público escolhido.
- `!faq [<pergunta>]` — (Em breve) Mostra perguntas frequentes ou responde dúvidas comuns.

## Novidades e exemplos de uso

### Geração automática e manual de resumos
- Ao adicionar um PDF na pasta `outputs/`, o bot processa automaticamente e envia resumos adaptados para os canais de Comercial, Suporte e Produto.
- Use `!leiapdf <arquivo>` para processar manualmente qualquer PDF da pasta `outputs/`.

### Geração de PDF customizado
- `!gerarpdf <público>` — Gera e envia um PDF com o resumo adaptado para o público escolhido (comercial, suporte ou produto). O arquivo é salvo em `pdfs_customizados/`.

### Exemplo de uso dos comandos
```
!leiapdf release_teste.pdf
!leiatxt exemplo.txt
!leiaarquivo release_teste.pdf
!ultimaversao
!versao 2025-06
!duvida O que mudou nesta versão?
!gerarpdf comercial
```

## Como funcionará a FAQ inteligente

O comando `!faq` terá dois modos:
- `!faq` — Mostra uma lista de perguntas frequentes (FAQ) cadastradas, extraídas de um arquivo ou base configurável.
- `!faq <pergunta>` — O bot busca a resposta mais relevante na base de FAQs usando IA (busca semântica ou similaridade) e responde no canal. Se não encontrar resposta adequada, pode sugerir perguntar para um humano ou acionar fallback de IA.

**Como cadastrar perguntas frequentes:**
- As FAQs podem ser mantidas em um arquivo como `prompts/faq.txt` (cada pergunta e resposta separadas por linha ou bloco).
- Exemplo de estrutura:
  
  ```
  Q: Como agendar um Pix?
  A: Use o menu de agendamento e selecione a data desejada.

  Q: O que fazer se o saldo for insuficiente?
  A: O sistema notificará e não executará o Pix agendado.
  ```
- O bot pode ler esse arquivo e, ao receber `!faq <pergunta>`, buscar a resposta mais próxima usando IA ou busca por similaridade.

**Vantagens:**
- Respostas rápidas para dúvidas comuns.
- Fácil manutenção e atualização das FAQs.
- Pode ser expandido para buscar em múltiplos arquivos ou integrar com bases externas.

## Funcionalidades automáticas

- **Notificações automáticas:** O bot monitora a pasta outputs/ e avisa no canal sempre que um novo release é adicionado.

## Extensibilidade

- Adicione novos públicos facilmente criando novas estratégias.
- Troque o backend de IA apenas implementando um novo Adapter.
- Suporte a novos formatos de arquivo via Template Method.
