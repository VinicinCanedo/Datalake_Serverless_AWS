import websocket
import json
import boto3
import time
from dotenv import load_dotenv
import os




# --- Configurações ---
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY") # Chave secreta para autenticação, se necessário
KINESIS_STREAM_NAME = "datalake-stream" # Nome do seu Kinesis Stream
AWS_REGION = "us-east-1" # North Virginia, ajuste conforme necessário

# Ações para as quais queremos receber dados
STOCK_SYMBOLS = ["AAPL", "AMZN", "MSFT", "GOOGL", "TSLA", "NVDA", "META"] # Apple, Amazon, Microsoft, Google, Tesla, Nvidia, Meta (Facebook)

# Inicializa o cliente Kinesis
kinesis_client = boto3.client('kinesis', region_name=AWS_REGION)

# --- Funções de Callback para o WebSocket ---

def on_message(ws, message):
    """
    Função chamada quando uma nova mensagem é recebida do Finnhub.
    Processa a mensagem e a envia para o Kinesis.
    """
    try:
        data = json.loads(message)
        
        # Teste local: Imprime a mensagem completa do Finnhub
        print(f"Dados recebidos do Finnhub: {json.dumps(data, indent=2)}")

        # Verifica se é uma mensagem de trade/atualização de preço e se contém dados
        if data.get('type') == 'trade' and 'data' in data:
            for trade in data['data']:
                # Adiciona um timestamp de ingestão (opcional, mas útil para tracing)
                trade['ingestion_timestamp'] = int(time.time() * 1000)
                
                # Para o Kinesis, o Partition Key é crucial. 
                # Usaremos o símbolo (s) como Partition Key para garantir que trades do mesmo ativo 
                # vão para o mesmo shard (e maintain a ordem, se relevante para a sua aplicação).
                partition_key = trade.get('s', 'unknown_symbol') 
                
                # O registro precisa ser uma string serializada
                record_data = json.dumps(trade)
                
                # Envia o registro para o Kinesis
                response = kinesis_client.put_record(
                    StreamName=KINESIS_STREAM_NAME,
                    Data=record_data,
                    PartitionKey=partition_key
                )
                print(f"  --> Registro enviado para Kinesis: {partition_key} - Resposta: {response['SequenceNumber']}")
        elif data.get('type') == 'ping':
            print("  --> Mensagem PING recebida do Finnhub (conexão ativa)")
        else:
            print(f"  --> Mensagem de outro tipo ou sem dados: {data.get('type')}")

    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON: {message}")
    except Exception as e:
        print(f"Erro ao processar mensagem ou enviar para Kinesis: {e}")
        print(f"Mensagem que causou o erro: {message}")

def on_error(ws, error):
    """Função chamada em caso de erro na conexão WebSocket."""
    print(f"### Erro: {error} ###")

def on_close(ws, close_status_code, close_msg):
    """Função chamada quando a conexão WebSocket é fechada."""
    print(f"### Conexão Fechada ### Status: {close_status_code}, Mensagem: {close_msg}")

def on_open(ws):
    """
    Função chamada quando a conexão WebSocket é aberta.
    Envia as mensagens de inscrição para os símbolos desejados.
    """
    print("### Conexão Aberta ###")
    for symbol in STOCK_SYMBOLS:
        subscribe_message = json.dumps({"type": "subscribe", "symbol": symbol})
        ws.send(subscribe_message)
        print(f"Inscrito em: {symbol}")

# --- Ponto de Entrada Principal ---

if __name__ == "__main__":
    # URL do WebSocket do Finnhub com sua API Key
    websocket_url = f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}"

    print(f"Conectando ao Finnhub em: {websocket_url}")
    print(f"Enviando dados para o Kinesis Stream: {KINESIS_STREAM_NAME} na região {AWS_REGION}")
    print(f"Aguardando dados para os símbolos: {', '.join(STOCK_SYMBOLS)}")

    # websocket.enableTrace(True) # Descomente para ver o log detalhado do websocket

    ws = websocket.WebSocketApp(websocket_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    
    ws.on_open = on_open # Atribui a função on_open
    
    # Executa o loop do WebSocket para manter a conexão aberta e processar mensagens
    # run_forever() tenta reconectar automaticamente em caso de desconexão.
    ws.run_forever()