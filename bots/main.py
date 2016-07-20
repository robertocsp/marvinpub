# !/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import telepot
from telepot.delegate import per_chat_id, create_open
import requests
import json
"""
$ python2.7 counter.py <token>
Count number of messages. Start over if silent for 10 seconds.
"""

class MessageCounter(telepot.helper.ChatHandler):

    def __init__(self, seed_tuple, timeout):
        super(MessageCounter, self).__init__(seed_tuple, timeout)
        self._count = 0
        global mensagem
        global contato
        contato = []
        mensagem = []

    def on_chat_message(self, msg):
        print(msg)
        pergunta1 = 'Olá <<fulano>>, você já é um cliente cadastrado, que bom! Vamos ao seu pedido. Veja o nosso cardápio e digite o sabor pizza que deseja. Ah se for 2 sabores, já pode dizer agora mesmo.'
        pergunta2 = 'Qual o tamanho? Média ou Grande?'
        pergunta3 = 'Quantas unidades?'
        pergunta4 = 'Ótimo, Algo para beber e sobremesa?'
        pergunta5 = 'Beleza! Posso encerrar seu pedido?'
        pergunta6 = 'O número do seu pedido é o 7277, valor total é de R$ 65,00. digite a forma de pagamento: (1) crédito, (2) débito, (3) dinheiro.'
        data = {}
        self._count += 1
        if self._count == 1:
            mensagem.append(pergunta1)
            mensagem.append(msg['text'])
            self.sender.sendMessage(pergunta1)
            f = open('cardapio01.jpg', 'rb')  # some file on local disk
            self.sender.sendPhoto(f)
        if self._count == 2:
            mensagem.append(pergunta2)
            mensagem.append(msg['text'])
            self.sender.sendMessage(pergunta2)
        if self._count == 3:
            mensagem.append(pergunta3)
            mensagem.append(msg['text'])
            self.sender.sendMessage(pergunta3)
        if self._count == 4:
            mensagem.append(pergunta4)
            mensagem.append(msg['text'])
            self.sender.sendMessage(pergunta4)
        if self._count == 5:
            mensagem.append(pergunta5)
            mensagem.append(msg['text'])
            self.sender.sendMessage(pergunta5)
        if self._count == 6:
            mensagem.append(pergunta6)
            mensagem.append(msg['text'])
            self.sender.sendMessage(pergunta6)
            # cliente.append(msg['from']['first_name'])
            data['id_loja'] = '1'
            data['origem'] = 'Telegram'
            data['id_cliente'] = msg['from']['id']
            data['nome_cliente'] = msg['from']['first_name'] + ' ' + msg['from']['last_name']
            data['mensagem'] = mensagem
            url = 'http://localhost:8000/marvin/api/rest/pedido'
            payload = {'some': 'data'}
            headers = {'content-type': 'application/json'}
            response = requests.post(url, data=json.dumps(data), headers=headers)
            print(response)

bot = telepot.DelegatorBot('242453983:AAEEsHGJFofzJ85VI8vKRI5QkAsoPTJixJE', [
    (per_chat_id(), create_open(MessageCounter, timeout=120)),
])
bot.message_loop(run_forever=True)



#  242453983:AAEEsHGJFofzJ85VI8vKRI5QkAsoPTJixJE   <- homologa
#  238197035:AAF3XCZ-o8Ru_HeqG58Vd8E_5ZbDii6mgp0   <- producao