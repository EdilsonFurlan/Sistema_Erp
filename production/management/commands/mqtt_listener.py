import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from django.utils import timezone
from production.models import Maquina, RegistroProducao
import sys

class Command(BaseCommand):
    help = 'Inicia o listener MQTT para monitoramento de máquinas industrial'

    def handle(self, *args, **options):
        broker_address = "localhost" 
        port = 1883
        
        # Paho MQTT 2.0 fix
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "DjangoListener")
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        
        self.stdout.write(f"Conectando ao Broker MQTT {broker_address}:{port}...")
        
        try:
            client.connect(broker_address, port, 60)
            client.loop_forever()
        except ImportError:
            self.stdout.write(self.style.ERROR("Biblioteca paho-mqtt não encontrada. Instale com: pip install paho-mqtt"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao conectar ao Broker: {e}"))
            self.stdout.write("Certifique-se de que o Mosquitto (ou outro broker) está rodando.")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.stdout.write(self.style.SUCCESS("Conectado ao MQTT com sucesso!"))
            # Subscreve para todos os tópicos que comecem com "maquina/" ou similar
            # Ajuste conforme padrão da fábrica
            client.subscribe("#") 
            self.stdout.write("Escutando todos os tópicos (#) para filtrar por cadastro...")
        else:
            self.stdout.write(self.style.ERROR(f"Falha na conexão MQTT, código: {rc}"))

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = msg.payload.decode("utf-8").strip().upper()
        except:
            return # Payload binário ou inválido
        
        # Ignora mensagens de sistema ($SYS)
        if topic.startswith("$"): return

        self.stdout.write(f"MSG: [{topic}] {payload}")

        try:
            # Busca máquina configurada com este tópico
            # Isso permite flexibilidade total nos tópicos (ex: 'fabrica/setor1/mqt01')
            maquina = Maquina.objects.filter(topico_mqtt=topic).first()
            
            if not maquina:
                # Opcional: auto-discovery ou ignorar
                return

            if payload == "LIGADO" or payload == "ON" or payload == "1":
                self.processar_ligado(maquina)
            elif payload == "DESLIGADO" or payload == "OFF" or payload == "0":
                self.processar_desligado(maquina)
            
            maquina.ultima_atualizacao = timezone.now()
            maquina.save(update_fields=['ultima_atualizacao'])
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro processando mensagem: {e}"))

    def processar_ligado(self, maquina):
        if maquina.status_atual == 'LIGADO':
            return
            
        maquina.status_atual = 'LIGADO'
        maquina.save(update_fields=['status_atual'])
        
        if maquina.op_atual:
            RegistroProducao.objects.create(
                maquina=maquina,
                op=maquina.op_atual,
                inicio=timezone.now()
            )
            self.stdout.write(self.style.SUCCESS(f">> INICIO: {maquina.nome} na OP {maquina.op_atual.id}"))
        else:
            self.stdout.write(self.style.WARNING(f">> ALERTA: {maquina.nome} ligou SEM OP alocada!"))

    def processar_desligado(self, maquina):
        if maquina.status_atual == 'DESLIGADO':
            return

        maquina.status_atual = 'DESLIGADO'
        maquina.save(update_fields=['status_atual'])
        
        # Encerra registro pendente
        # Pega o último não finalizado
        registro = RegistroProducao.objects.filter(
            maquina=maquina, 
            finalizado=False
        ).order_by('-inicio').first()
        
        if registro:
            registro.fim = timezone.now()
            registro.save()
            self.stdout.write(self.style.SUCCESS(f">> PARADA: {maquina.nome}. Tempo: {registro.duracao_segundos}s"))
