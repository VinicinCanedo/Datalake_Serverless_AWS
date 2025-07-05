# Documentação do Código: `producer.py`

Este documento detalha o funcionamento do script `producer.py`, responsável por coletar dados de transações de ações em tempo real da API da Finnhub e enviá-los para um stream do Amazon Kinesis.

## Visão Geral

O script estabelece uma conexão WebSocket com a Finnhub para receber atualizações de preços de um conjunto predefinido de ações. Cada transação recebida é então formatada como um registro JSON e enviada para o Amazon Kinesis Data Streams, atuando como o produtor de dados em nossa arquitetura de streaming.

---

## Estrutura do Código

O código é dividido nas seguintes seções principais:

1.  **Importações e Configurações**
2.  **Inicialização do Cliente Kinesis**
3.  **Funções de Callback do WebSocket**
4.  **Ponto de Entrada Principal**

---

### 1. Importações e Configurações

Nesta seção, importamos as bibliotecas necessárias e definimos as configurações principais para a execução do script.

```python
import websocket
import json
import boto3
import time
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações ---
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY") # Chave secreta para autenticação, se necessário
KINESIS_STREAM_NAME = "datalake-stream" # Nome do seu Kinesis Stream
AWS_REGION = "us-east-1" # North Virginia, ajuste conforme necessário

# Ações para as quais queremos receber dados
STOCK_SYMBOLS = ["AAPL", "AMZN", "MSFT", "GOOGL", "TSLA", "NVDA", "META"]
```

-   **`import`**: Importamos `websocket` para a conexão em tempo real, `json` para manipulação de dados, `boto3` para interagir com a AWS, `time` para adicionar timestamps, e `os`/`dotenv` para gerenciar variáveis de ambiente (como a chave da API).
-   **`load_dotenv()`**: Carrega as configurações de um arquivo `.env`, o que é uma boa prática para não expor chaves e segredos no código.
-   **`FINNHUB_API_KEY`**: Armazena sua chave de API da Finnhub.
-   **`KINESIS_STREAM_NAME`**: Define o nome do Kinesis Data Stream que receberá os dados.
-   **`AWS_REGION`**: Especifica a região da AWS onde o stream está localizado.
-   **`STOCK_SYMBOLS`**: Uma lista com os símbolos das ações que desejamos monitorar.

---

### 2. Inicialização do Cliente Kinesis

Aqui, criamos uma instância do cliente do Kinesis usando o Boto3, que nos permitirá enviar registros para o stream.

```python
# Inicializa o cliente Kinesis
kinesis_client = boto3.client('kinesis', region_name=AWS_REGION)
```

-   `boto3.client('kinesis', ...)`: Cria um objeto cliente de baixo nível que se comunica com o serviço Kinesis na região especificada.

---

### 3. Funções de Callback do WebSocket

Estas funções definem como o nosso script deve reagir a diferentes eventos da conexão WebSocket.

#### `on_message(ws, message)`

É a função mais importante. Ela é executada toda vez que uma nova mensagem chega da Finnhub.

```python
def on_message(ws, message):
    try:
        data = json.loads(message)
        print(f"Dados recebidos do Finnhub: {json.dumps(data, indent=2)}")

        if data.get('type') == 'trade' and 'data' in data:
            for trade in data['data']:
                trade['ingestion_timestamp'] = int(time.time() * 1000)
                partition_key = trade.get('s', 'unknown_symbol')
                record_data = json.dumps(trade)

                response = kinesis_client.put_record(
                    StreamName=KINESIS_STREAM_NAME,
                    Data=record_data,
                    PartitionKey=partition_key
                )
                print(f"  --> Registro enviado para Kinesis: {partition_key} - Resposta: {response['SequenceNumber']}")
    # ... (tratamento de erros)
```

-   **Processamento**: A mensagem (string) é convertida para um objeto Python (`json.loads`).
-   **Filtro**: O código verifica se a mensagem é do tipo `trade` e se contém dados. Mensagens de `ping` ou outros tipos são ignoradas.
-   **Enriquecimento**: Um timestamp de ingestão (`ingestion_timestamp`) é adicionado a cada transação.
-   **Chave de Partição**: A chave de partição (`partition_key`) é definida como o símbolo da ação (`s`). Isso garante que todas as transações da mesma ação sejam enviadas para o mesmo shard no Kinesis, mantendo a ordem de processamento.
-   **Envio para o Kinesis**: O método `kinesis_client.put_record` é chamado para enviar o dado. `Data` deve ser uma string serializada (por isso usamos `json.dumps`).

#### `on_open(ws)`

Executada assim que a conexão com a Finnhub é estabelecida com sucesso.

```python
def on_open(ws):
    print("### Conexão Aberta ###")
    for symbol in STOCK_SYMBOLS:
        subscribe_message = json.dumps({"type": "subscribe", "symbol": symbol})
        ws.send(subscribe_message)
        print(f"Inscrito em: {symbol}")
```

-   **Inscrição**: A função itera sobre a lista `STOCK_SYMBOLS` e envia uma mensagem de `subscribe` para cada ação, informando à API da Finnhub que queremos receber atualizações para esses símbolos.

#### `on_error(ws, error)` e `on_close(ws, ...)`

Funções para lidar com erros e o fechamento da conexão, respectivamente. Elas simplesmente imprimem mensagens informativas no console.

```python
def on_error(ws, error):
    print(f"### Erro: {error} ###")

def on_close(ws, close_status_code, close_msg):
    print(f"### Conexão Fechada ### ...")
```

---

### 4. Ponto de Entrada Principal

Esta é a seção que efetivamente executa o script.

```python
if __name__ == "__main__":
    websocket_url = f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}"

    print(f"Conectando ao Finnhub em: {websocket_url}")
    # ...

    ws = websocket.WebSocketApp(websocket_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    
    ws.on_open = on_open
    
    ws.run_forever()
```

-   **`if __name__ == "__main__"`**: Garante que o código só será executado quando o script for chamado diretamente.
-   **URL do WebSocket**: Constrói a URL de conexão, incluindo a chave da API.
-   **`websocket.WebSocketApp(...)`**: Cria a instância do aplicativo WebSocket, associando cada evento (on_message, on_error, etc.) à sua respectiva função de callback.
-   **`ws.run_forever()`**: Inicia o loop de eventos do WebSocket. Este método mantém o script em execução, ouvindo continuamente por novas mensagens e reconectando-se automaticamente em caso de falha na conexão.
