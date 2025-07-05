# Datalake Serverless para Análise de Dados de Streaming do Mercado de Ações

Este projeto demonstra a construção de um datalake serverless na AWS para ingestão, processamento e análise de dados de streaming em tempo real do mercado de ações, utilizando dados da API da Finnhub.

## Visão Geral

O objetivo deste projeto é criar uma arquitetura de dados escalável e sem servidor, capaz de processar um grande volume de transações de ações em tempo real. Os dados são coletados da Finnhub, enviados para o Amazon Kinesis Data Streams, processados por uma função AWS Lambda e, em seguida, armazenados no Amazon DynamoDB para análise e consulta.

## Arquitetura

A arquitetura do projeto é composta pelos seguintes serviços da AWS:

1.  **Amazon Kinesis Data Streams:** Atua como o ponto de entrada para os dados de streaming. O script `producer.py` envia os dados de transações de ações da Finnhub para um Kinesis Stream.
2.  **AWS Lambda:** Uma função Lambda é acionada por novos registros no Kinesis Stream. A função processa os dados, realizando transformações ou enriquecimentos necessários.
3.  **Amazon DynamoDB:** O Lambda armazena os dados processados em uma tabela do DynamoDB, que serve como nosso datalake para armazenamento de dados quentes e consultas de baixa latência.
4.  **AWS IAM (Identity and Access Management):** As permissões para os serviços (Kinesis, Lambda, DynamoDB) são gerenciadas através de roles e policies do IAM para garantir a segurança e o princípio do menor privilégio.

**Fluxo de Dados:**

`Finnhub WebSocket API` -> `producer.py` -> `Amazon Kinesis Data Streams` -> `AWS Lambda` -> `Amazon DynamoDB`

## Tecnologias Utilizadas

*   **Python:** Linguagem de programação principal para os scripts de produtor e para a função Lambda.
*   **Boto3:** AWS SDK para Python, para interagir com os serviços da AWS.
*   **Finnhub API:** Fonte de dados de mercado de ações em tempo real.
*   **AWS CLI:** Para gerenciamento e deploy dos recursos na AWS.
*   **Poetry:** Para gerenciamento de dependências do Python.

## Componentes do Projeto

*   `producer.py`: Script Python que se conecta à API WebSocket da Finnhub, recebe os dados das transações e os envia para o Kinesis Data Stream.
*   `consumer.py`: Script Python que representa a lógica do consumidor (que será implementada na função Lambda) para processar os dados do Kinesis.
*   `pyproject.toml` / `poetry.lock`: Arquivos de configuração de dependências do Poetry.

## Como Configurar e Executar

### Pré-requisitos

*   Conta na AWS com permissões para criar e gerenciar Kinesis, Lambda, DynamoDB e IAM.
*   Python 3.8+ instalado.
*   Poetry instalado.
*   AWS CLI configurado com suas credenciais.
*   Uma chave de API da [Finnhub](https://finnhub.io/).

### Passos

1.  **Clonar o repositório:**
    ```bash
    git clone <url-do-repositorio>
    cd <nome-do-repositorio>
    ```

2.  **Instalar dependências:**
    ```bash
    poetry install
    ```

3.  **Configurar Variáveis de Ambiente:**
    Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
    ```
    FINNHUB_API_KEY="SUA_CHAVE_API_FINNHUB"
    SECRET_KEY="SUA_CHAVE_SECRETA_SE_NECESSARIO"
    ```

4.  **Configuração dos Recursos na AWS:**
    Esta seção detalha os passos para configurar todos os recursos necessários na AWS.

    **a. Configuração do AWS CLI**
    Se você ainda não configurou o AWS CLI, abra seu terminal e execute o comando. Ele pedirá seu `AWS Access Key ID`, `AWS Secret Access Key`, `Default region name` (ex: `us-east-1`) e `Default output format` (ex: `json`).
    ```bash
    aws configure
    ```

    **b. Criação do Kinesis Data Stream**
    1.  Acesse o console do **Amazon Kinesis**.
    2.  No menu lateral, clique em **Data Streams**.
    3.  Clique em **Criar fluxo de dados**.
    4.  **Nome do fluxo de dados:** Dê um nome ao seu stream (ex: `datalake-stream`). Este nome deve ser o mesmo que a variável `KINESIS_STREAM_NAME` no seu script `producer.py`.
    5.  **Modo de capacidade:** Para este projeto, **Sob demanda** é uma boa escolha para começar.
    6.  Clique em **Criar fluxo de dados**.

    **c. Criação da Tabela no DynamoDB**
    1.  Acesse o console do **Amazon DynamoDB**.
    2.  Clique em **Criar tabela**.
    3.  **Nome da tabela:** Escolha um nome (ex: `stock_trades`).
    4.  **Chave de partição:** Defina como `s` (símbolo da ação).
    5.  **Chave de classificação:** Defina como `t` (timestamp da transação).
    6.  Deixe as outras configurações como padrão e clique em **Criar tabela**.

    **d. Configuração de Permissões no IAM**
    Vamos criar uma política e uma função (role) para que a função Lambda possa acessar o Kinesis e o DynamoDB.
    1.  Acesse o console do **AWS IAM**.
    2.  **Criar Política:**
        *   Vá para **Políticas** e clique em **Criar política**.
        *   Use o editor **JSON** e cole o seguinte código, substituindo `<sua-regiao>`, `<seu-id-de-conta>` e os nomes dos seus recursos:
          ```json
          {
              "Version": "2012-10-17",
              "Statement": [
                  {
                      "Sid": "KinesisStreamRead",
                      "Effect": "Allow",
                      "Action": [
                          "kinesis:GetRecord",
                          "kinesis:GetRecords",
                          "kinesis:GetShardIterator",
                          "kinesis:DescribeStream",
                          "kinesis:ListStreams"
                      ],
                      "Resource": "arn:aws:kinesis:<sua-regiao>:<seu-id-de-conta>:stream/datalake-stream"
                  },
                  {
                      "Sid": "DynamoDBWrite",
                      "Effect": "Allow",
                      "Action": [
                          "dynamodb:PutItem",
                          "dynamodb:UpdateItem"
                      ],
                      "Resource": "arn:aws:dynamodb:<sua-regiao>:<seu-id-de-conta>:table/stock_trades"
                  },
                  {
                      "Sid": "CloudWatchLogs",
                      "Effect": "Allow",
                      "Action": [
                          "logs:CreateLogGroup",
                          "logs:CreateLogStream",
                          "logs:PutLogEvents"
                      ],
                      "Resource": "arn:aws:logs:*:*:*"
                  }
              ]
          }
          ```
        *   Clique em **Avançar**, dê um nome à política (ex: `LambdaKinesisDynamoDBPolicy`) e clique em **Criar política**.
    3.  **Criar Função (Role):**
        *   Vá para **Funções** e clique em **Criar função**.
        *   Selecione **Serviço da AWS** e, em "Caso de uso", escolha **Lambda**.
        *   Clique em **Avançar**.
        *   Procure e selecione a política que você acabou de criar (`LambdaKinesisDynamoDBPolicy`).
        *   Clique em **Avançar**, dê um nome à função (ex: `LambdaKinesisToDynamoRole`) e clique em **Criar função**.

    **e. Criação da Função Lambda**
    1.  Acesse o console do **AWS Lambda**.
    2.  Clique em **Criar função**.
    3.  Selecione **Criar do zero**.
    4.  **Nome da função:** Dê um nome (ex: `KinesisToDynamoDBProcessor`).
    5.  **Runtime:** Escolha **Python 3.9** (ou uma versão compatível).
    6.  **Arquitetura:** `x86_64`.
    7.  **Permissões:** Expanda "Alterar função de execução padrão" e selecione **Usar uma função de execução existente**. Escolha a função que você criou (`LambdaKinesisToDynamoRole`).
    8.  Clique em **Criar função**.
    9.  **Adicionar Gatilho:**
        *   Na página da sua função, clique em **Adicionar gatilho**.
        *   Selecione **Kinesis** na lista.
        *   Escolha seu stream (`datalake-stream`).
        *   Deixe as outras opções como padrão e clique em **Adicionar**.
    10. **Configurar o Código:**
        *   Na aba **Código**, cole o conteúdo do seu arquivo `consumer.py`.
        *   Clique em **Deploy** para salvar as alterações.

5.  **Executar o Produtor:**
    Atualize o nome do `KINESIS_STREAM_NAME` no arquivo `producer.py` e execute-o:
    ```bash
    poetry run python producer.py
    ```

O terminal começará a exibir os dados sendo recebidos do Finnhub e enviados para o Kinesis. Você poderá então verificar os logs da função Lambda e os dados sendo inseridos na tabela do DynamoDB.
