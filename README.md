
# 🚀 Datalake Serverless para Análise de Dados de Streaming do Mercado de Ações

> **Resumo:**
> Este projeto demonstra como construir um datalake totalmente serverless na AWS para ingestão, processamento e análise de dados de streaming em tempo real do mercado de ações, utilizando dados da API da Finnhub.

---

## 📊 Visão Geral

O objetivo é criar uma arquitetura escalável, sem servidor, capaz de processar grandes volumes de transações de ações em tempo real. Os dados são coletados da Finnhub, enviados para o Amazon Kinesis Data Streams, processados por uma função AWS Lambda e armazenados no Amazon DynamoDB para análise e consulta.

---

## 🏗️ Arquitetura

| Serviço AWS         | Função no Projeto                                                                 |
|---------------------|----------------------------------------------------------------------------------|
| **Kinesis Data Streams** | Ingestão de dados em tempo real (entrada dos dados do Finnhub)                  |
| **AWS Lambda**          | Processamento dos dados recebidos do Kinesis                                    |
| **DynamoDB**            | Armazenamento dos dados processados para consulta/análise                       |
| **IAM**                 | Gerenciamento de permissões e roles para segurança dos recursos                 |

**Fluxo de Dados:**

```
Finnhub WebSocket API → producer.py → Amazon Kinesis Data Streams → AWS Lambda → Amazon DynamoDB
```

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia      | Descrição                                      |
|-----------------|------------------------------------------------|
| Python          | Linguagem principal dos scripts                 |
| Boto3           | SDK AWS para Python                             |
| Finnhub API     | Fonte dos dados de mercado em tempo real        |
| AWS CLI         | Gerenciamento e deploy dos recursos AWS         |
| Poetry          | Gerenciamento de dependências Python            |

---

## 📁 Componentes do Projeto

| Arquivo/Ferramenta      | Função                                                                 |
|-------------------------|------------------------------------------------------------------------|
| `producer.py`           | Conecta à Finnhub, recebe dados e envia para o Kinesis                  |
| `consumer.py`           | Lógica do consumidor (Lambda) para processar dados do Kinesis           |
| `pyproject.toml`/`poetry.lock` | Gerenciamento de dependências Python                        |

---

## ⚙️ Como Configurar e Executar

### ✅ Pré-requisitos

| Requisito | Descrição |
|-----------|-----------|
| Conta AWS | Permissões para criar/gerenciar Kinesis, Lambda, DynamoDB e IAM |
| Python 3.8+ | Instalado |
| Poetry | Instalado |
| AWS CLI | Configurado |
| Chave Finnhub | [Obtenha aqui](https://finnhub.io/) |

---

### 📝 Passos

1. **Clonar o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd <nome-do-repositorio>
   ```

2. **Instalar dependências:**
   ```bash
   poetry install
   ```

3. **Configurar Variáveis de Ambiente:**
   Crie um arquivo `.env` na raiz do projeto com:
   ```env
   FINNHUB_API_KEY="SUA_CHAVE_API_FINNHUB"
   SECRET_KEY="SUA_CHAVE_SECRETA_SE_NECESSARIO"
   ```

4. **Configuração dos Recursos na AWS:**
   <details>
   <summary><strong>Etapas detalhadas</strong></summary>

   #### a. 🖥️ Configuração do AWS CLI
   Execute no terminal e preencha as informações solicitadas:
   ```bash
   aws configure
   ```

   #### b. 🔄 Criação do Kinesis Data Stream
   1. Acesse o console do **Amazon Kinesis**.
   2. No menu lateral, clique em **Data Streams**.
   3. Clique em **Criar fluxo de dados**.
   4. Nome do fluxo: `datalake-stream` (deve ser igual ao do `producer.py`).
   5. Modo de capacidade: **Sob demanda**.
   6. Clique em **Criar fluxo de dados**.

   #### c. 🗄️ Criação da Tabela no DynamoDB
   1. Console do **Amazon DynamoDB**.
   2. Clique em **Criar tabela**.
   3. Nome: `stock_trades`.
   4. Chave de partição: `s` (símbolo da ação).
   5. Chave de classificação: `t` (timestamp da transação).
   6. Clique em **Criar tabela**.

   #### d. 🔐 Configuração de Permissões no IAM
   | Role/Política | Descrição |
   |---------------|-----------|
   | **AWSLambdaKinesisExecutionRole** | Permite que a Lambda leia dados do Kinesis |
   | **Política customizada DynamoDB** | Permite gravar dados no DynamoDB usando `BatchWriteItem` |

   **Exemplo de política customizada para DynamoDB:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["dynamodb:BatchWriteItem"],
         "Resource": "arn:aws:dynamodb:<sua-regiao>:<seu-id-de-conta>:table/stock_trades"
       }
     ]
   }
   ```

   **Como associar as roles à Lambda:**
   1. No console do **IAM**, crie uma nova role para Lambda.
   2. Anexe a política gerenciada **AWSLambdaKinesisExecutionRole**.
   3. Crie e anexe a política customizada acima para o DynamoDB.

   #### e. ⚡ Criação da Função Lambda
   1. Console do **AWS Lambda**.
   2. Clique em **Criar função** > **Criar do zero**.
   3. Nome: `KinesisToDynamoDBProcessor`.
   4. Runtime: Python 3.9+.
   5. Permissões: Selecione a role criada acima.
   6. Clique em **Criar função**.
   7. Adicione o gatilho do Kinesis (`datalake-stream`).
   8. Cole o código do `consumer.py` e clique em **Deploy**.

   </details>

5. **Executar o Produtor:**
   Atualize o nome do `KINESIS_STREAM_NAME` no `producer.py` e execute:
   ```bash
   poetry run python producer.py
   ```

---

## 📈 Observação

O terminal exibirá os dados recebidos do Finnhub e enviados ao Kinesis. Você pode acompanhar os logs da Lambda e os dados inseridos no DynamoDB pelo console AWS.

---

## 💡 Relevância

Este projeto exemplifica uma arquitetura moderna, escalável e de baixo custo para ingestão e processamento de dados em tempo real, utilizando apenas serviços gerenciados da AWS. É ideal para aplicações que exigem análise imediata de grandes volumes de dados, como no setor financeiro, IoT e monitoramento de sistemas.
