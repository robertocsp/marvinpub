# -*- coding: utf-8 -*-
"""
This bot listens to port 5003 for incoming connections from Facebook.
"""
import unicodedata
import datetime
import random
import keys.keys as my_keys
import my_cache.cache as my_cache
from utils.aescipher import AESCipher
from string import Template
from flask import Flask, request, send_from_directory, Response
from celery import chain
from celery.exceptions import SoftTimeLimitExceeded
from contextlib import contextmanager
from django.core import signing
from itertools import product
from string import ascii_lowercase
try:
    from urllib.parse import parse_qs, urlencode, quote_plus
except ImportError:
    from urlparse import parse_qs
    from urllib import urlencode, quote_plus
from my_celery.tasks import get_object, send_quickreply_message, enviar_pedido, envia_resposta, send_generic_message, \
    touch_cliente, send_text_message, salva_se_nao_existir, notificacao_dashboard, get_cardapio, \
    send_image_url_message, troca_mesa_dashboard, teste_tarefa, error_handler, send_button_message, \
    link_psid_marviin, check_login_valid, log_out_marviin
from deliverylog import app_log

my_cache.cache_entry_prefix = 'delivery'
my_cache.EXPIRACAO_CACHE_CONVERSA = 60 * 20  # 30 minutos
flask_app = Flask(__name__)

app_log.debug('celery_app:::' + send_generic_message.name)

saudacao = ['ola', 'oi', 'bom dia', 'boa tarde', 'boa noite']
agradecimentos = ['obrigado', 'obrigada', 'valeu', 'vlw', 'flw']
POSTBACK_MAP = {
    'menu_novo_pedido': u'Novo pedido',
    'pedir_cardapio': u'Visualizar cardápio',
    'menu_trocar_mesa': u'Definir endereço',
    'finalizar_pedido': u'Conferir e Enviar',
    'pedir_mais': u'+ itens ao pedido',
    'menu_rever_pedido': u'Atualizar pedido',
    'menu_get_started': u'Menu principal',
    'editar_item_': u'Editar item',
    'remover_item_': u'Remover item',
    'vermais_offset_': u'Ver mais itens',
    'log_out': u'Log out',
}
# ULTIMO PASSO = 34


def get_elements_menu(conversa):
    menu = []
    possui_itens_pedido = (len(conversa['itens_pedido']) > 0)
    pedido_andamento = (conversa['datahora_inicio_pedido'] is not None)
    try:
        logged_in = conversa['auth_code'] is not None and signing.loads(conversa['auth_code'],
                                                                        key=my_keys.SECRET_KEY,
                                                                        max_age=600) is not None
    except signing.BadSignature:
        logged_in = False
    if possui_itens_pedido and pedido_andamento:
        menu.append(
            {
                'title': u'Confira e envie seu pedido',
                'image_url': 'https://sistema.marviin.com.br/static/marviin/img/enviar_pedido.jpg',
                'subtitle': u'Confira e envie seu pedido para iniciarmos seu preparo.',
                'buttons': [
                    {
                        'type': 'postback',
                        'title': u'Conferir e Enviar',
                        'payload': 'finalizar_pedido'
                    }
                ]
            })
    if pedido_andamento:
        menu.append(
            {
                'title': u'Adicione itens ao pedido',
                'image_url': 'https://sistema.marviin.com.br/static/marviin/img/adicionar_itens.jpg',
                'subtitle': u'Adicione itens ao pedido que você já começou a montar.',
                'buttons': [
                    {
                        'type': 'postback',
                        'title': u'Pedir mais coisas',
                        'payload': 'pedir_mais'
                    }
                ]
            })
    if possui_itens_pedido and pedido_andamento:
        menu.append(
            {
                'title': u'Atualize seu pedido',
                'image_url': 'https://sistema.marviin.com.br/static/marviin/img/atualizar_pedido.jpg',
                'subtitle': u'Atualize os itens já adicionados ao seu pedido.',
                'buttons': [
                    {
                        'type': 'postback',
                        'title': u'Atualizar pedido',
                        'payload': 'menu_rever_pedido'
                    }
                ]
            })
    menu.append(
        {
            'title': u'Realize um novo pedido',
            'image_url': 'https://sistema.marviin.com.br/static/marviin/img/novo-pedido.jpg',
            'subtitle': u'Monte um novo pedido por aqui, é bem fácil.',
            'buttons': [
                {
                    'type': 'postback',
                    'title': u'Novo pedido',
                    'payload': 'menu_novo_pedido'
                }
            ]
        })
    menu.append(
        {
            'title': u'Visualize o cardápio',
            'image_url': 'https://sistema.marviin.com.br/static/marviin/img/pedir-cardapio.jpg',
            'subtitle': u'Visualize nosso cardápio para auxiliá-lo(a) na montagem de seu pedido.',
            'buttons': [
                {
                    'type': 'postback',
                    'title': u'Visualizar cardápio',
                    'payload': 'pedir_cardapio'
                }
            ]
        })
    if logged_in:
        menu.append(
            {
                'title': u'Log out',
                'subtitle': u'Desconecte de sua conta Marviin.',
                'buttons': [
                    {
                        'type': 'postback',
                        'title': u'Log out',
                        'payload': 'log_out'
                    }
                ]
            })
    '''
    menu.append(
        {
            'content_type': 'text',
            'title': u'Ajuda',
            'payload': 'menu_ajuda'
        })
    '''
    return menu


def get_quickreply_cardapio_digital(conversa):
    menu = []
    possui_itens_pedido = (len(conversa['itens_pedido']) > 0)
    pedido_andamento = (conversa['datahora_inicio_pedido'] is not None)
    try:
        logged_in = conversa['auth_code'] is not None and signing.loads(conversa['auth_code'],
                                                                        key=my_keys.SECRET_KEY,
                                                                        max_age=600) is not None
    except signing.BadSignature:
        logged_in = False
    if possui_itens_pedido and pedido_andamento:
        menu.append(
            {
                'content_type': 'text',
                'title': u'Conferir e Enviar',
                'payload': 'finalizar_pedido'
            })
    if pedido_andamento:
        menu.append(
            {
                'content_type': 'text',
                'title': u'Pedir mais coisas',
                'payload': 'pedir_mais'
            })
    if possui_itens_pedido and pedido_andamento:
        menu.append(
            {
                'content_type': 'text',
                'title': u'Atualizar pedido',
                'payload': 'menu_rever_pedido'
            })
    menu.append(
        {
            'content_type': 'text',
            'title': u'Novo pedido',
            'payload': 'menu_novo_pedido'
        })
    menu.append(
        {
            'content_type': 'text',
            'title': u'Voltar ao menu',
            'payload': 'voltar_menu'
        })
    if logged_in:
        menu.append(
            {
                'content_type': 'text',
                'title': u'Log out',
                'payload': 'log_out'
            })
    return menu


def get_quickreply_pedido(conversa):
    try:
        logged_in = conversa['auth_code'] is not None and signing.loads(conversa['auth_code'],
                                                                        key=my_keys.SECRET_KEY,
                                                                        max_age=600) is not None
    except signing.BadSignature:
        logged_in = False
    menu = [
        {
            'content_type': 'text',
            'title': u'Conferir e Enviar',
            'payload': 'finalizar_pedido'
        },
        {
            'content_type': 'text',
            'title': u'Pedir mais coisas',
            'payload': 'pedir_mais'
        },
        {
            'content_type': 'text',
            'title': u'Atualizar pedido',
            'payload': 'menu_rever_pedido'
        },
        {
            'content_type': 'text',
            'title': u'Voltar ao menu',
            'payload': 'voltar_menu'
        }
    ]
    if logged_in:
        menu.append(
            {
                'content_type': 'text',
                'title': u'Log out',
                'payload': 'log_out'
            })
    return menu


def get_quickreply_pedido2(conversa):
    try:
        logged_in = conversa['auth_code'] is not None and signing.loads(conversa['auth_code'],
                                                                        key=my_keys.SECRET_KEY,
                                                                        max_age=600) is not None
    except signing.BadSignature:
        logged_in = False
    menu = [
        {
            'content_type': 'text',
            'title': u'Pedir mais coisas',
            'payload': 'pedir_mais'
        },
        {
            'content_type': 'text',
            'title': u'Atualizar pedido',
            'payload': 'menu_rever_pedido'
        },
        {
            'content_type': 'text',
            'title': u'Conferir e Enviar',
            'payload': 'finalizar_pedido'
        },
        {
            'content_type': 'text',
            'title': u'Começar novo pedido',
            'payload': 'menu_novo_pedido2'
        },
        {
            'content_type': 'text',
            'title': u'Voltar ao menu',
            'payload': 'voltar_menu'
        }
    ]
    if logged_in:
        menu.append(
            {
                'content_type': 'text',
                'title': u'Log out',
                'payload': 'log_out'
            })
    return menu


def get_quickreply_endereco(conversa):
    try:
        logged_in = conversa['auth_code'] is not None and signing.loads(conversa['auth_code'],
                                                                        key=my_keys.SECRET_KEY,
                                                                        max_age=600) is not None
    except signing.BadSignature:
        logged_in = False
    menu = [
        {
            'content_type': 'text',
            'title': u'Pedir mais coisas',
            'payload': 'pedir_mais'
        },
        {
            'content_type': 'text',
            'title': u'Atualizar pedido',
            'payload': 'menu_rever_pedido'
        },
        {
            'content_type': 'text',
            'title': u'Visualizar cardápio',
            'payload': 'pedir_cardapio'
        },
        {
            'content_type': 'text',
            'title': u'Começar novo pedido',
            'payload': 'menu_novo_pedido2'
        },
        {
            'content_type': 'text',
            'title': u'Voltar ao menu',
            'payload': 'voltar_menu'
        }
    ]
    if logged_in:
        menu.append(
            {
                'content_type': 'text',
                'title': u'Log out',
                'payload': 'log_out'
            })
    return menu


def get_quickreply_finalizar_pedido(conversa):
    try:
        logged_in = conversa['auth_code'] is not None and signing.loads(conversa['auth_code'],
                                                                        key=my_keys.SECRET_KEY,
                                                                        max_age=600) is not None
    except signing.BadSignature:
        logged_in = False
    menu = [
        {
            'content_type': 'text',
            'title': u'Enviar pedido',
            'payload': 'finalizar_enviar'
        },
        {
            'content_type': 'text',
            'title': u'Pedir mais coisas',
            'payload': 'pedir_mais'
        },
        {
            'content_type': 'text',
            'title': u'Atualizar pedido',
            'payload': 'menu_rever_pedido'
        },
        {
            'content_type': 'text',
            'title': u'Começar novo pedido',
            'payload': 'menu_novo_pedido2'
        },
        {
            'content_type': 'text',
            'title': u'Voltar ao menu',
            'payload': 'voltar_menu'
        }
    ]
    if logged_in:
        menu.append(
            {
                'content_type': 'text',
                'title': u'Log out',
                'payload': 'log_out'
            })
    return menu


def get_quickreply_atualizar_pedido(conversa):
    try:
        logged_in = conversa['auth_code'] is not None and signing.loads(conversa['auth_code'],
                                                                        key=my_keys.SECRET_KEY,
                                                                        max_age=600) is not None
    except signing.BadSignature:
        logged_in = False
    menu = [
        {
            'content_type': 'text',
            'title': u'Voltar',
            'payload': 'menu_rever_pedido'
        },
        {
            'content_type': 'text',
            'title': u'Voltar ao menu',
            'payload': 'voltar_menu'
        }
    ]
    if logged_in:
        menu.append(
            {
                'content_type': 'text',
                'title': u'Log out',
                'payload': 'log_out'
            })
    return menu


def get_quickreply_voltar_menu(conversa):
    try:
        logged_in = conversa['auth_code'] is not None and signing.loads(conversa['auth_code'],
                                                                        key=my_keys.SECRET_KEY,
                                                                        max_age=600) is not None
    except signing.BadSignature:
        logged_in = False
    menu = [
        {
            'content_type': 'text',
            'title': u'Voltar ao menu',
            'payload': 'voltar_menu'
        }
    ]
    if logged_in:
        menu.append(
            {
                'content_type': 'text',
                'title': u'Log out',
                'payload': 'log_out'
            })
    return menu


def get_quickreply_conversa_suspensa():
    return [
        {
            'content_type': 'text',
            'title': u'Finalizar contato',
            'payload': 'sair_suspensao'
        }
    ]


def get_quickreply_sim_nao(conversa):
    try:
        logged_in = conversa['auth_code'] is not None and signing.loads(conversa['auth_code'],
                                                                        key=my_keys.SECRET_KEY,
                                                                        max_age=600) is not None
    except signing.BadSignature:
        logged_in = False
    menu = [
        {
            'content_type': 'text',
            'title': u'Sim',
            'payload': 'sim'
        },
        {
            'content_type': 'text',
            'title': u'Não',
            'payload': 'nao'
        },
        {
            'content_type': 'text',
            'title': u'Voltar ao menu',
            'payload': 'voltar_menu'
        }
    ]
    if logged_in:
        menu.append(
            {
                'content_type': 'text',
                'title': u'Log out',
                'payload': 'log_out'
            })
    return menu


# TODO QUICKREPLY DE PGTO
def get_quickreply_pgto1():
    pass


def get_button_login(psid):
    # VER https://developers.facebook.com/docs/messenger-platform/messenger-extension
    return [
        {
            'type': 'account_link',
            'url': 'https://sistema.marviin.com.br/fb_login'
        }
    ]


def get_button_webview_endereco(psid):
    key32 = "{: <32}".format(my_keys.SECRET_KEY[:32]).encode("utf-8")
    cipher = AESCipher(key=key32)
    my_cache.cache_client.set(psid + 'web_sec', 'oto', time=my_cache.EXPIRACAO_CACHE_CONVERSA)
    return [
        {
            'type': 'postback',
            'title': 'Usar padrão',
            'payload': 'endereco_padrao'
        },
        {
            'type': 'web_url',
            'url': 'https://sistema.marviin.com.br/fb_endereco?r=' +
                   ''.join(random.choice('0123456789') for x in range(3)),
            'title': 'Escolher outro',
            'webview_height_ratio': 'tall',
            'messenger_extensions': True,
            'fallback_url': 'https://sistema.marviin.com.br/fb_endereco/' + cipher.encrypt(psid),
        }
    ]


def get_mensagem(id_mensagem, **args):
    mensagens = {
        'ola':        Template(u'Olá $arg1, como posso ajudá-lo(a)?'),
        'getstarted': Template(u'Legal, $arg1, vamos começar. Navegue lateralmente pelas opções abaixo, e veja como '
                               u'posso ajudá-lo(a).'),
        'menu':       Template(u'Digite a palavra menu para saber em como posso ajudá-lo(a). '
                               u'Você poderá digitá-la novamente a qualquer momento.'),
        'mesa':       Template(u'Por favor, digite seu endereço.'),
        'pedido':     Template(u'Excelente, digite aqui o que deseja, quanto mais detalhado melhor! ;)'),
        'pedido1':    Template(u'Exemplo: 1 pizza família mozarela e 1 coca 2L'),
        'pedido2':    Template(u'Desculpe, mas não encontrei um pedido sendo montado. Pedirei que comece um novo, por '
                               u'favor. Obrigado.'),
        'anotado':    Template(u'Anotado.\n$arg1, deseja mais alguma coisa ou posso enviar seu pedido?'),
        'anotado1':   Template(u'Pedido atualizado.\nDeseja mais alguma coisa ou posso enviar seu pedido?'),
        'qtde':       Template(u'$arg1\nPerdoe-me, mas não consegui identificar a quantidade do(s) seguinte(s) '
                               u'item(ns) acima.'),
        'qtde1':      Template(u'Peço, por favor, que reenvie sua última mensagem corrigindo-os.'),
        'enviar':     Template(u'Maravilha, já já seu pedido estará aí.\nPosso ajudá-lo(a) em algo mais?'),
        'agradeco':   Template(u'Eu que agradeço.'),
        'robo':       Template(u'Desculpe, mas não entendi o que deseja. \nComo posso auxiliá-lo(a)?'),
        'anotado2':   Template(u'Por favor, escolha uma das opções que lhe apresento abaixo.'),
        'mesa3':      Template(u'Certo, providenciarei que seu pedido seja enviado para este endereço.'),
        'mesa4':      Template(u'Endereço anterior igual ao atual.'),
        'mesa5':      Template(u'$arg1, correto?'),
        'sim_nao':    Template(u'Escolha uma das opções abaixo, por favor.'),
        'pedido3':    Template(u'Por favor, pode digitar. :)'),
        'pedido4':    Template(u'$arg1, já existe um pedido sendo montado. Deseja continuar este pedido ou começar um '
                               u'novo?'),
        'rever2':     Template(u'Pedido se encontra vazio de itens. Como posso auxiliá-lo(a)?'),
        'auxilio':    Template(u'Em que posso ajudá-lo(a)?'),
        'auxilio1':   Template(u'Em que posso ajudá-lo(a) agora?'),
        'auxilio2':   Template(u'Anotado. Como posso ajudá-lo(a) agora?'),
        'desenv':     Template(u'Função em desenvolvimento...'),
        'finalizar':  Template(u'Segue, acima, seu pedido para conferência. Confirma o envio?'),
        'cardapio':   Template(u'Já levaremos o cardápio para você. Em que posso ajudá-lo(a) agora?'),
        'cardapio2':  Template(u'Deseja a versão digital ou quer que lhe traga o impresso?'),
        'cardapio3':  Template(u'Segue, acima, imagem do cardápio.'),
        'cardapio4':  Template(u'Seguem, acima, 2 imagens do cardápio.'),
        'cardapio5':  Template(u'Desculpe, ficarei devendo a versão digital, mas já pedi para trazerem o cardápio '
                               u'impresso para você. Em que posso ajudá-lo(a) agora?'),
        'garcom':     Template(u'Perfeito, logo logo ele(a) estará aí. Como posso ajudá-lo(a) agora?'),
        'suspensao':  Template(u'Sua resposta foi enviada.\nPara finaizar o contato clique abaixo.'),
        'conta':      Template(u'Ok, já avisei para trazerem sua conta.\nMuito obrigado(a), espero que sua experiência '
                               u'tenha sido a melhor possível.\nVolte sempre!'),
        'conta2':     Template(u'Desculpe, mas não tenho anotado seu endereço. Você poderia me informar, por favor.'),
        'pgto1':      Template(u'Escolha sua forma de pagamento'),
        'login':      Template(u'Para sua segurança, peço que faça o login na sua conta Marviin.'),
        'login2':     Template(u'Não foi possível efetuar o login, por favor, tente novamente.'),
        'endereco':   Template(u'Por favor, me informe seu endereço de entrega.'),
        'logout':     Template(u'Logout realizado com sucesso. Como posso auxiliá-lo(a)?'),
    }
    return mensagens[id_mensagem].substitute(args)


def define_mesa(mesa, conversa):
    if conversa['mesa'] is None:
        conversa['mesa'] = []
        conversa['mesa'].append('')
    elif len(conversa['mesa']) == 2:
        conversa['mesa'][1] = conversa['mesa'][0]
    elif len(conversa['mesa']) == 1:
        conversa['mesa'].append(conversa['mesa'][0])
    conversa['mesa'][0] = mesa
    return True


def anota_pedido(message, conversa, i_edicao=None):
    pedido = estrutura_pedido(message)
    app_log.debug('=========================>>>>> 3 ' + repr(conversa['itens_pedido']))
    if i_edicao is not None:
        del conversa['itens_pedido'][int(i_edicao)]
    conversa['itens_pedido'] += pedido
    app_log.debug('=========================>>>>> 4 ' + repr(conversa['itens_pedido']))
    return True


def estrutura_pedido(message):
    pedido = []
    app_log.debug('=========================>>>>> 1 ' + repr(pedido))
    itens_pedido = message.splitlines()
    for item_linha in itens_pedido:
        itens = item_linha.split(';')
        for item in itens:
            if len(item.strip()) == 0:
                continue
            app_log.debug('=========================>>>>> 2 ' + item)
            item_pedido = item.strip().split(' ', 1)
            quantidade = [int(qtde) for qtde in [item_pedido[0]] if qtde.isdigit()]
            if len(quantidade) == 0 or (quantidade[0] > 0 and len(item_pedido) == 1):
                pedido.append({
                    'descricao': item,
                    'quantidade': 1
                })
            elif quantidade[0] > 0:
                pedido.append({
                    'descricao': item_pedido[1],
                    'quantidade': quantidade[0]
                })
    return pedido


def resposta_dashboard(message=None, payload=None, sender_id=None, loja_id=None, conversa=None):
    if unicodedata.normalize('NFKD', message).encode('ASCII', 'ignore').lower() == u'menu' or \
                    payload == 'sair_suspensao':
        retomar_passo(sender_id, loja_id, conversa)
    else:
        send_quickreply_message.delay(sender_id, loja_id, get_mensagem('suspensao'),
                                      get_quickreply_conversa_suspensa())
        envia_resposta.delay(conversa, loja_id, sender_id, message)


def set_variaveis(conversa, nao_entendidas=(True, 0), itens_pedido=(True, None),
                  datetime_pedido=(True, None)):
    if datetime_pedido[0]:
        conversa['datahora_inicio_pedido'] = datetime_pedido[1]
    if nao_entendidas[0]:
        conversa['nao_entendidas'] = nao_entendidas[1]
    if itens_pedido[0]:
        conversa['itens_pedido'] = [] if not itens_pedido[1] else itens_pedido[1]


def checa_duplicidade(sender_id, loja_id, timestamp, conversa):
    duplicado = False
    if conversa['entry'] is None:
        conversa['entry'] = {}
    elif conversa['entry']['sender_id'] == sender_id and \
            conversa['entry']['loja_id'] == loja_id and \
            conversa['entry']['timestamp'] == timestamp:
        duplicado = True
    conversa['entry']['sender_id'] = sender_id
    conversa['entry']['loja_id'] = loja_id
    conversa['entry']['timestamp'] = timestamp
    return duplicado


@flask_app.route('/', defaults={'path': ''})
@flask_app.route('/.well-known/acme-challenge/<path:path>')
def ping(path):
    return send_from_directory('.well-known/acme-challenge', path, as_attachment=False,
                               mimetype='text/plain')


@flask_app.route("/teste_tarefa", methods=['GET', 'POST'])
def teste_tarefa_route():
    app_log.debug('>>> inicio requisicao ::')
    teste_tarefa.apply_async((), link_error=error_handler.s())
    resp = Response('success', status=200, mimetype='text/plain')
    resp.status_code = 200
    app_log.debug('>>> fim requisicao ::')
    return resp


@contextmanager
def sender_lock(sender_id):
    app_log.debug('lock acquire:: ' + sender_id)
    lock = my_cache.cache_client.add(my_cache.cache_entry_prefix + sender_id + 'lock', True,
                                     time=my_cache.EXPIRACAO_CACHE_LOCK)
    app_log.debug('lock:: ' + repr(lock) + ' :: ' + sender_id)
    yield lock
    if lock:
        my_cache.cache_client.delete(my_cache.cache_entry_prefix + sender_id + 'lock')
        app_log.debug('lock released:: ' + sender_id)
    else:
        app_log.debug('no lock ' + sender_id)


def atualiza_cardapio(loja_id, cardapio):
    app_log.debug('atualiza_cardapio:: ' + repr(cardapio))
    if cardapio is None:
        my_cache.cache_client.delete(my_cache.cache_entry_prefix + loja_id + 'cardapio')
    else:
        my_cache.cache_client.set(my_cache.cache_entry_prefix + loja_id + 'cardapio', cardapio,
                                  time=my_cache.EXPIRACAO_CACHE_LOJA)


@flask_app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == my_keys.CHAVE_BOT_WEBHOOK:
            return request.args.get("hub.challenge")
        return
    if request.method == 'POST':
        app_log.debug(u'INICIO POST :: ')
        output = request.json
        app_log.debug(output)
        entry = output['entry'][0]
        if 'messaging' not in entry:
            resp = Response('success', status=200, mimetype='text/plain')
            resp.status_code = 200
            return resp
        event = entry['messaging']
        for x in event:
            if x.get('message') and x['message'].get('is_echo'):
                resp = Response(u'mensagem de echo', status=200, mimetype='text/plain')
                resp.status_code = 200
                return resp
            sender_id = None
            loja_id = None
            if x.get('sender') and x['sender']['id'] and x.get('recipient') and x['recipient']['id']:
                sender_id = str(x['sender']['id'])
                loja_id = str(x['recipient']['id'])
                app_log.debug('sender_id:: ' + sender_id)
                app_log.debug('loja_id:: ' + loja_id)
            if sender_id is None or loja_id is None:
                resp = Response(u'sender e/ou recipient não encontrado', status=200, mimetype='text/plain')
                resp.status_code = 200
                return resp
            else:
                with sender_lock(sender_id) as lock:
                    if lock:
                        app_log.debug('lock acquired:: ' + sender_id)
                        touch_cliente.delay(sender_id)
                        conversa = my_cache.cache_client.get(my_cache.cache_entry_prefix + sender_id)
                        app_log.debug('alguma conversa no cache:: ' + repr(conversa))
                        if conversa is not None:
                            my_cache.cache_client.set(my_cache.cache_entry_prefix + sender_id, conversa,
                                                      time=my_cache.EXPIRACAO_CACHE_CONVERSA)
                            app_log.debug('conversa:: ' + repr(conversa))
                        else:
                            user = pega_usuario(sender_id, loja_id)
                            if not user:
                                resp = Response(u'não foi possível recuperar o usuário do facebook', status=200,
                                                mimetype='text/plain')
                                resp.status_code = 200
                                return resp
                            conversa = {
                                'passo': 0,
                                'passo_sim': None,
                                'passo_nao': None,
                                'usuario': user,
                                'mesa': None,
                                'aux': None,
                                'pgto': None,
                                'itens_pedido': [],
                                'nao_entendidas': 0,
                                'datahora_inicio_pedido': None,
                                'suspensa': 0,
                                'uid': None,
                                'entry': None,
                                'auth_code': None,
                            }
                            app_log.debug('usuario:: ' + repr(user))
                        if x.get('message') or x.get('postback') or x.get('account_linking'):
                            if checa_duplicidade(sender_id, loja_id, x['timestamp'], conversa):
                                resp = Response(u'chamada duplicada', status=200,
                                                mimetype='text/plain')
                                resp.status_code = 200
                                return resp
                            if x.get('message') and x['message'].get('text') and not x['message'].get('quick_reply'):
                                message = x['message']['text'].strip()
                                app_log.debug('message: '+message)
                                if conversa['suspensa'] > 0:
                                    resposta_dashboard(message=message, sender_id=sender_id, loja_id=loja_id,
                                                       conversa=conversa)
                                elif unicodedata.normalize('NFKD', message).encode('ASCII', 'ignore').lower() \
                                        in saudacao:
                                    conversa['passo'] = 0
                                    passo_ola(message, sender_id, loja_id, conversa)
                                elif u'inicio' in unicodedata.normalize('NFKD', message) \
                                        .encode('ASCII', 'ignore').lower():
                                    passo_inicio(sender_id, loja_id, conversa)
                                elif u'menu' in unicodedata.normalize('NFKD', message)\
                                        .encode('ASCII', 'ignore').lower():
                                    conversa['passo'] = 1
                                    passo_menu(message, sender_id, loja_id, conversa)
                                elif u'pedido' in unicodedata.normalize('NFKD', message)\
                                        .encode('ASCII', 'ignore').lower():
                                    # passo 14 definido dentro do método
                                    passo_novo_pedido(message, sender_id, loja_id, conversa)
                                elif unicodedata.normalize('NFKD', message).encode('ASCII', 'ignore').lower() \
                                        in agradecimentos:
                                    conversa['passo'] = 11
                                    passo_agradecimento(message, sender_id, loja_id, conversa)
                                else:
                                    define_passo(message, sender_id, loja_id, conversa, conversa['passo'])
                            elif ((x.get('message') and x['message'].get('quick_reply') and
                                   x['message']['quick_reply'].get('payload')) or
                                  (x.get('postback') and x['postback'].get('payload'))):
                                if x.get('message'):
                                    payload = x['message']['quick_reply']['payload']
                                    message = x['message']['text']
                                else:
                                    payload = x['postback'].get('payload')
                                    message = next(v for k, v in POSTBACK_MAP.items() if payload.startswith(k))
                                app_log.debug(payload)
                                conversa['suspensa'] = 0
                                define_payload(message, sender_id, loja_id, conversa, payload)
                            elif x.get('account_linking'):
                                link = False
                                if x['account_linking'].get('authorization_code'):
                                    link = link_psid_marviin.delay(sender_id,
                                                                   x['account_linking'].get('authorization_code')).get()
                                    if link:
                                        conversa['passo'] = 34
                                        conversa['auth_code'] = x['account_linking'].get('authorization_code')
                                        passo_finalizar_pedido_autorizado(None, sender_id, loja_id, conversa)
                                if link is False:
                                    send_text_message.delay(sender_id, loja_id, get_mensagem('login2'))
                        elif x.get('dashboard'):
                            conversa['suspensa'] += 1
                            conversa['uid'] = x['dashboard']['uid']
                            send_text_message.delay(sender_id, loja_id, x['dashboard']['message'], icon=u'\U0001f464')
                        elif x.get('webview') and x['webview'].get('postload'):
                            if x['webview'].get('postload') == 'endereco_selecionado':
                                conversa['passo'] = 18
                                passo_forma_pgto(None, sender_id, loja_id, conversa)
                        my_cache.cache_client.set(my_cache.cache_entry_prefix + sender_id, conversa,
                                                  time=my_cache.EXPIRACAO_CACHE_CONVERSA)
        resp = Response('success', status=200, mimetype='text/plain')
        resp.status_code = 200
        return resp


def define_payload(message, sender_id, loja_id, conversa, payload):
    if payload == 'menu_novo_pedido' or payload == 'menu_novo_pedido2':
        if payload == 'menu_novo_pedido2':
            set_variaveis(conversa)
        # passos 14 definido dentro do método
        passo_novo_pedido(message, sender_id, loja_id, conversa)
    elif payload == 'menu_trocar_mesa':
        define_sim_nao(conversa, 3, define_passo, 15, define_payload, 'menu_trocar_mesa')
        passo_trocar_mesa_2(message, sender_id, loja_id, conversa)
    elif payload == 'menu_rever_pedido':
        conversa['passo'] = 16
        passo_rever_pedido_2(message, sender_id, loja_id, conversa)
    elif payload.startswith('editar_item_'):
        conversa['passo'] = 28
        passo_editar_item(message, sender_id, loja_id, conversa, payload[len('editar_item_'):])
    elif payload.startswith('remover_item_'):
        # passos 29 e 31 definidos dentro do método
        passo_remover_item(message, sender_id, loja_id, conversa, payload[len('remover_item_'):])
    elif payload.startswith('vermais_offset_'):
        conversa['passo'] = 30
        conversa['aux'] = int(payload[len('vermais_offset_'):])
        passo_rever_pedido_2(message, sender_id, loja_id, conversa, offset=conversa['aux'])
    elif payload == 'pedir_conta':
        # passos 24 e 25 definidos dentro do método
        passo_pedir_conta(message, sender_id, loja_id, conversa)
    elif payload == 'pedir_mais':
        conversa['passo'] = 17
        passo_pedir_mais(message, sender_id, loja_id, conversa)
    elif payload == 'finalizar_pedido':
        passo_finalizar_pedido(message, sender_id, loja_id, conversa)
    elif payload == 'finalizar_enviar':
        conversa['passo'] = 0
        passo_finalizar_enviar(message, sender_id, loja_id, conversa)
    elif payload == 'pedir_cardapio':
        # passos 3, 19, 20, 26 e 27 utilizados nesta ação
        passo_pedir_cardapio(message, sender_id, loja_id, conversa)
    elif payload == 'chamar_garcom':
        # passos 22 e 23 definidos dentro do método
        passo_chamar_garcom(message, sender_id, loja_id, conversa)
    elif payload == 'voltar_menu':
        conversa['passo'] = 1
        conversa['aux'] = None
        conversa['passo_sim'] = None
        conversa['passo_nao'] = None
        passo_menu(message, sender_id, loja_id, conversa)
    elif payload == 'sim':
        conversa['passo_sim'][0](message, sender_id, loja_id, conversa, conversa['passo_sim'][1])
        conversa['passo_sim'] = None
        conversa['passo_nao'] = None
    elif payload == 'nao':
        conversa['passo_nao'][0](message, sender_id, loja_id, conversa, conversa['passo_nao'][1])
    elif payload == 'cardapio_impresso':
        passo_cardapio_impresso(message, sender_id, loja_id, conversa)
    elif payload == 'cardapio_digital':
        passo_cardapio_digital(message, sender_id, loja_id, conversa)
    elif payload == 'menu_get_started':
        passo_inicio(sender_id, loja_id, conversa)
    elif payload == 'log_out':
        auth_code = conversa['auth_code']
        conversa['passo'] = 0
        if auth_code is not None:
            conversa['auth_code'] = None
            chain(log_out_marviin.si(sender_id, auth_code),
                  send_text_message.si(sender_id, loja_id, get_mensagem('logout')),
                  send_generic_message.si(sender_id, loja_id, get_elements_menu(conversa)))()
        else:
            chain(send_text_message.si(sender_id, loja_id, get_mensagem('logout')),
                  send_generic_message.si(sender_id, loja_id, get_elements_menu(conversa)))()


def passo_inicio(sender_id, loja_id, conversa):
    conversa['passo'] = 0
    bot1 = get_mensagem('getstarted', arg1=conversa['usuario']['first_name'])
    chain(send_text_message.si(sender_id, loja_id, bot1),
          send_generic_message.si(sender_id, loja_id, get_elements_menu(conversa)))()


def define_sim_nao(conversa, passo, passo_sim_func, passo_sim_var, passo_nao_func, passo_nao_var):
    conversa['passo'] = passo
    conversa['passo_sim'] = []
    conversa['passo_sim'].append(passo_sim_func)
    conversa['passo_sim'].append(passo_sim_var)
    conversa['passo_nao'] = []
    conversa['passo_nao'].append(passo_nao_func)
    conversa['passo_nao'].append(passo_nao_var)


def define_passo(message, sender_id, loja_id, conversa, passo):  # de que passo veio a requisicao
    conversa['passo'] = passo
    if passo == 3:
        conversa['passo'] = 26
        conversa['aux'] = message
        passo_confirma_mesa(message, sender_id, loja_id, conversa)
    elif passo == 15:
        conversa['passo'] = 2
        passo_trocar_mesa(message, sender_id, loja_id, conversa)
    elif passo == 13:
        # passos 6 definido dentro do método
        passo_um(message, sender_id, loja_id, conversa)
    elif passo == 6 or passo == 9 or passo == 14 or passo == 17:
        # passos 8 e 9 definidos dentro do método
        passo_dois(message, sender_id, loja_id, conversa)
    elif passo == 8:
        conversa['passo'] = 10
        passo_tres(message, sender_id, loja_id, conversa)
    elif passo == 18:
        passo_forma_pgto(None, sender_id, loja_id, conversa)
        # if u'nao' in unicodedata.normalize('NFKD', message).encode('ASCII', 'ignore').lower():
        #     conversa['passo'] = 21
        #     passo_menu(message, sender_id, loja_id, conversa)
        # elif u'sim' in unicodedata.normalize('NFKD', message).encode('ASCII', 'ignore').lower() or \
        #      u'pode' in unicodedata.normalize('NFKD', message).encode('ASCII', 'ignore').lower() or \
        #      u'confirm' in unicodedata.normalize('NFKD', message).encode('ASCII', 'ignore').lower():
        #     conversa['passo'] = 0
        #     passo_finalizar_enviar(message, sender_id, loja_id, conversa)
        # elif u'editar' in unicodedata.normalize('NFKD', message).encode('ASCII', 'ignore').lower():
        #     conversa['passo'] = 16
        #     passo_rever_pedido_2(message, sender_id, loja_id, conversa)
    elif passo == 19:
        define_mesa(conversa['aux'], conversa)
        conversa['aux'] = None
        passo_cardapio_impresso(message, sender_id, loja_id, conversa)
    elif passo == 22:
        passo_mesa_dependencia(message, sender_id, loja_id, conversa, 'garcom', 23)
    elif passo == 25:
        passo_mesa_dependencia(message, sender_id, loja_id, conversa, 'conta', 24)
    elif passo == 26 or passo == 29:
        normalizada = unicodedata.normalize('NFKD', message).encode('ASCII', 'ignore').lower()
        if u'sim' == normalizada:
            conversa['passo_sim'][0](message, sender_id, loja_id, conversa, conversa['passo_sim'][1])
            conversa['passo_sim'] = None
            conversa['passo_nao'] = None
        elif u'nao' == normalizada:
            conversa['passo_nao'][0](message, sender_id, loja_id, conversa, conversa['passo_nao'][1])
        else:
            bot = get_mensagem('sim_nao')
            send_quickreply_message.delay(sender_id, loja_id, bot, get_quickreply_sim_nao(conversa))
    elif passo == 28 or passo == 31:
        if pre_requisito_pedido(sender_id, loja_id, conversa):
            if passo == 28:
                anota_pedido(message, conversa, i_edicao=conversa['aux'])
            else:
                del conversa['itens_pedido'][int(conversa['aux'])]
            conversa['passo'] = 16
            set_variaveis(conversa,
                          itens_pedido=(False, None),
                          datetime_pedido=(False, None))
            passo_rever_pedido_2(message, sender_id, loja_id, conversa, eh_msg_sucesso=True)
    elif passo == 32:
        define_mesa(conversa['aux'], conversa)
        conversa['aux'] = None
        passo_finalizar_pedido(message, sender_id, loja_id, conversa)
    else:
        conversa['passo'] = 12
        passo_nao_entendido(message, sender_id, loja_id, conversa)


def pega_usuario(sender_id, loja_id):
    retries = 0
    user = None
    while retries < 1:
        try:
            app_log.debug('pega_usuario 1:: ')
            user = get_object.delay(sender_id, loja_id).get()
            salva_se_nao_existir.delay(sender_id, loja_id, user)
            app_log.debug('pega_usuario 2:: ')
            break
        except SoftTimeLimitExceeded:
            retries += 1
            app_log.debug('pega_usuario 3:: ')
        except Exception as e:
            retries += 1
            app_log.debug('pega_usuario 4:: '+repr(e))
    app_log.debug('pega_usuario 5:: ')
    return user


def retomar_passo(sender_id, loja_id, conversa):
    if conversa['passo'] == 0 or conversa['passo'] == 1 or conversa['passo'] == 2 or conversa['passo'] == 5 \
            or conversa['passo'] == 20 or conversa['passo'] == 21 or conversa['passo'] == 23 or conversa['passo'] == 24:
        passo_menu(None, sender_id, loja_id, conversa)
    elif conversa['passo'] == 3:
        mensagem_mesa(conversa, loja_id, sender_id)
    elif conversa['passo'] == 15:
        passo_trocar_mesa_2(None, sender_id, loja_id, conversa)
    elif conversa['passo'] == 16:
        passo_rever_pedido_2(None, sender_id, loja_id, conversa)
    elif conversa['passo'] == 13:
        passo_novo_pedido(None, sender_id, loja_id, conversa)
    elif conversa['passo'] == 6 or conversa['passo'] == 9 or conversa['passo'] == 14 or conversa['passo'] == 17:
        mensagem_pedido(sender_id, loja_id, conversa)
    elif conversa['passo'] == 8:
        bot = get_mensagem('anotado', arg1=conversa['usuario']['first_name'])
        send_quickreply_message.delay(sender_id, loja_id, bot, get_quickreply_pedido(conversa))
    elif conversa['passo'] == 10:
        passo_tres(None, sender_id, loja_id, conversa)
    elif conversa['passo'] == 18:
        passo_finalizar_pedido(None, sender_id, loja_id, conversa)
    elif conversa['passo'] == 19:
        passo_pedir_cardapio(None, sender_id, loja_id, conversa)
    elif conversa['passo'] == 25:
        passo_pedir_conta(None, sender_id, loja_id, conversa)
    elif conversa['passo'] == 27:
        passo_cardapio(None, sender_id, loja_id, conversa)
    elif conversa['passo'] == 28:
        passo_editar_item(None, sender_id, loja_id, conversa, conversa['aux'])
    elif conversa['passo'] == 29:
        passo_remover_item(None, sender_id, loja_id, conversa, conversa['aux'])
    elif conversa['passo'] == 30:
        passo_rever_pedido_2(None, sender_id, loja_id, conversa, offset=conversa['aux'])
    elif conversa['passo'] == 33:
        passo_finalizar_pedido(None, sender_id, loja_id, conversa)
    elif conversa['passo'] == 34:
        passo_finalizar_pedido_autorizado(None, sender_id, loja_id, conversa)
    conversa['suspensa'] = 0


def existe_pedido_andamento(sender_id, loja_id, conversa):
    if conversa['datahora_inicio_pedido'] is not None and len(conversa['itens_pedido']) > 0:
        bot = get_mensagem('pedido4', arg1=conversa['usuario']['first_name'])
        send_quickreply_message.delay(sender_id, loja_id, bot, get_quickreply_pedido2(conversa))
        return True
    return False


def passo_editar_item(message, sender_id, loja_id, conversa, i):
    if pre_requisito_pedido(sender_id, loja_id, conversa):
        conversa['aux'] = i
        item = repr(conversa['itens_pedido'][int(i)]['quantidade']) + ' ' + \
               conversa['itens_pedido'][int(i)]['descricao']
        bot = u'Digite seu pedido'
        chain(send_text_message.si(sender_id, loja_id, item, icon=None),
              send_quickreply_message.si(sender_id, loja_id, bot, get_quickreply_atualizar_pedido(conversa)))()


def passo_remover_item(message, sender_id, loja_id, conversa, i):
    if pre_requisito_pedido(sender_id, loja_id, conversa):
        conversa['aux'] = i
        item = repr(conversa['itens_pedido'][int(i)]['quantidade']) + ' ' + \
               conversa['itens_pedido'][int(i)]['descricao']
        bot = u'Remove o item acima?'
        define_sim_nao(conversa, 29, define_passo, 31, define_payload, 'menu_rever_pedido')
        chain(send_text_message.si(sender_id, loja_id, item, icon=None),
              send_quickreply_message.si(sender_id, loja_id, bot, get_quickreply_sim_nao(conversa)))()


def pre_requisito_pedido(sender_id, loja_id, conversa):
    if conversa['datahora_inicio_pedido'] is None:
        conversa['passo'] = 0
        chain(send_text_message.si(sender_id, loja_id, get_mensagem('pedido2')),
              send_generic_message.si(sender_id, loja_id, get_elements_menu(conversa)))()
        return False
    return True


def passo_cardapio_impresso(message, sender_id, loja_id, conversa, texto_id=None):
    if conversa['mesa'] is None:
        define_sim_nao(conversa, 3, define_passo, 19, define_payload, 'cardapio_impresso')
        mensagem_mesa(conversa, loja_id, sender_id)
    else:
        conversa['passo'] = 20
        mensagem_sucesso(sender_id, loja_id, conversa, (texto_id if texto_id else 'cardapio'))


def passo_cardapio_digital(message, sender_id, loja_id, conversa):
    cardapios = my_cache.cache_client.get(my_cache.cache_entry_prefix + loja_id + 'cardapio')
    conversa['passo'] = 0
    tarefas = []
    for cardapio in cardapios:
        app_log.debug('cardapio digital:: ' + repr(cardapio))
        tarefas.append(send_image_url_message.si(sender_id, loja_id, cardapio))
    if len(cardapios) == 1:
        bot = get_mensagem('cardapio3')
    else:
        bot = get_mensagem('cardapio4')
    tarefas.append(send_quickreply_message.si(sender_id, loja_id, bot, get_quickreply_cardapio_digital(conversa)))
    chain(tarefas)()


def passo_cardapio(message, sender_id, loja_id, conversa):
    app_log.debug('passo_cardapio 1:: ')
    try:
        cardapio = get_cardapio.delay(loja_id).get()
        app_log.debug('passo_cardapio 2:: ' + repr(cardapio))
        atualiza_cardapio(loja_id, cardapio)
        if cardapio is None:
            app_log.debug('passo_cardapio 3:: ')
            # TODO definir o que fazer quando não tiver um cardápio cadastrado.
            # passo_cardapio_impresso(message, sender_id, loja_id, conversa)
        else:
            conversa['passo'] = 27
            passo_cardapio_digital(message, sender_id, loja_id, conversa)
    except SoftTimeLimitExceeded:
        app_log.debug('passo_cardapio 4:: ')
        passo_cardapio_impresso(message, sender_id, loja_id, conversa, texto_id='cardapio5')
    except Exception as e:
        app_log.debug('passo_cardapio 5:: ' + repr(e))
        passo_cardapio_impresso(message, sender_id, loja_id, conversa, texto_id='cardapio5')


def passo_confirma_mesa(message, sender_id, loja_id, conversa):
    bot = get_mensagem('mesa5', arg1=message)
    send_quickreply_message.delay(sender_id, loja_id, bot, get_quickreply_sim_nao(conversa))


def passo_pedir_conta(message, sender_id, loja_id, conversa):
    set_variaveis(conversa,
                  itens_pedido=(False, None),
                  datetime_pedido=(False, None))
    if conversa['mesa'] is not None:
        conversa['passo'] = 24
        mensagem_sucesso(sender_id, loja_id, conversa, 'conta')
    else:
        define_sim_nao(conversa, 3, define_passo, 25, define_payload, 'pedir_conta')
        bot = get_mensagem('conta2')
        send_quickreply_message.delay(sender_id, loja_id, bot, get_quickreply_voltar_menu(conversa))


def passo_chamar_garcom(message, sender_id, loja_id, conversa):
    set_variaveis(conversa,
                  itens_pedido=(False, None),
                  datetime_pedido=(False, None))
    if conversa['mesa'] is None:
        define_sim_nao(conversa, 3, define_passo, 22, define_payload, 'chamar_garcom')
        mensagem_mesa(conversa, loja_id, sender_id)
    else:
        conversa['passo'] = 23
        mensagem_sucesso(sender_id, loja_id, conversa, 'garcom')


def passo_pedir_cardapio(message, sender_id, loja_id, conversa):
    set_variaveis(conversa,
                  itens_pedido=(False, None),
                  datetime_pedido=(False, None))
    passo_cardapio(message, sender_id, loja_id, conversa)


def mensagem_sucesso(sender_id, loja_id, conversa, mensagem):
    notificacao_dashboard.apply_async((sender_id, loja_id, conversa, mensagem))
    bot = get_mensagem(mensagem)
    chain(send_text_message.si(sender_id, loja_id, bot), send_generic_message.si(sender_id, loja_id,
                                                                                 get_elements_menu(conversa)))()


def passo_mesa_dependencia(message, sender_id, loja_id, conversa, mensagem, passo):
    conversa['passo'] = passo
    define_mesa(conversa['aux'], conversa)
    conversa['aux'] = None
    set_variaveis(conversa,
                  itens_pedido=(False, None),
                  datetime_pedido=(False, None))
    mensagem_sucesso(sender_id, loja_id, conversa, mensagem)


def passo_finalizar_enviar(message, sender_id, loja_id, conversa):
    if pre_requisito_pedido(sender_id, loja_id, conversa):
        enviar_pedido.delay(sender_id, loja_id, conversa)
        set_variaveis(conversa)
        chain(send_text_message.si(sender_id, loja_id, get_mensagem('enviar')),
              send_generic_message.si(sender_id, loja_id, get_elements_menu(conversa)))()


def passo_finalizar_pedido(message, sender_id, loja_id, conversa):
    if pre_requisito_pedido(sender_id, loja_id, conversa):
        if len(conversa['itens_pedido']) > 0:
            # VERIFICA SE NECESSITA DE LOGIN OU SE AUTORIZACAO AINDA EH VALIDA
            login_valid = check_login_valid.delay(sender_id).get()
            if login_valid is False:
                conversa['passo'] = 33
                send_button_message.delay(sender_id, loja_id, get_mensagem('login'), get_button_login(sender_id))
            else:
                conversa['passo'] = 34
                passo_finalizar_pedido_autorizado(message, sender_id, loja_id, conversa)
        else:
            bot = get_mensagem('rever2')
            chain(send_text_message.si(sender_id, loja_id, bot), send_generic_message.si(sender_id, loja_id,
                                                                                         get_elements_menu(conversa)))()


def passo_finalizar_pedido_autorizado(message, sender_id, loja_id, conversa):
    if pre_requisito_pedido(sender_id, loja_id, conversa):
        if len(conversa['itens_pedido']) > 0:
            # PEGA ENDERECO VIA WEBVIEW
            chain(send_button_message.si(sender_id, loja_id, get_mensagem('endereco'),
                                         get_button_webview_endereco(sender_id)),
                  send_quickreply_message.si(sender_id, loja_id, 'Ou, se preferir:',
                                             get_quickreply_endereco(conversa)))()
            '''
            passo_endereco(message, sender_id, loja_id, conversa)
            if conversa['mesa'] is None:
                define_sim_nao(conversa, 3, define_passo, 32, define_payload, 'finalizar_pedido')
                mensagem_mesa(conversa, loja_id, sender_id)
                # TODO IMPLEMENTAR FORMA DE PGTO
            elif conversa['pgto'] is None:
                send_quickreply_message.delay(sender_id, loja_id, get_mensagem('pgto1'), get_quickreply_pgto1())
            else:
                conversa['passo'] = 18
                pedidos = None
                for i, item in enumerate(conversa['itens_pedido']):
                    if pedidos:
                        pedidos += '\n'
                    else:
                        pedidos = ''
                    pedidos += repr(item['quantidade']) + ' ' + item['descricao']
                bot1 = pedidos
                bot2 = get_mensagem('finalizar')
                chain(send_text_message.si(sender_id, loja_id, bot1),
                      send_quickreply_message.si(sender_id, loja_id, bot2, get_quickreply_finalizar_pedido(conversa),
                                                 icon=None))()
                '''
        else:
            bot = get_mensagem('rever2')
            chain(send_text_message.si(sender_id, loja_id, bot), send_generic_message.si(sender_id, loja_id,
                                                                                         get_elements_menu(conversa)))()


def passo_forma_pgto(message, sender_id, loja_id, conversa):
    send_text_message.delay(sender_id, loja_id, 'TODO forma de pgto.')


def passo_pedir_mais(message, sender_id, loja_id, conversa):
    if pre_requisito_pedido(sender_id, loja_id, conversa):
        set_variaveis(conversa,
                      itens_pedido=(False, None),
                      datetime_pedido=(False, None))
        bot = get_mensagem('pedido3')
        send_quickreply_message.delay(sender_id, loja_id, bot, get_quickreply_voltar_menu(conversa))


def add_item_pedido_menu(menu, i, item, offset=0):
    if offset == 0:
        descricao_item = item if len(item) <= 80 else item[:77] + '...'
        menu.append(
            {
                'title': descricao_item,
                'subtitle': u'Edite ou remova este item.',
                'buttons': [
                    {
                        'type': 'postback',
                        'title': u'Editar',
                        'payload': 'editar_item_' + repr(i)
                    },
                    {
                        'type': 'postback',
                        'title': u'Remover',
                        'payload': 'remover_item_' + repr(i)
                    }
                ]
            })
    else:
        menu.append(
            {
                'title': u'Mais itens',
                'subtitle': u'Clique aqui para mostrar mais itens.',
                'buttons': [
                    {
                        'type': 'postback',
                        'title': u'Ver mais',
                        'payload': 'vermais_offset_' + repr(offset)
                    }
                ]
            })


def passo_rever_pedido_2(message, sender_id, loja_id, conversa, offset=0, eh_msg_sucesso=False):
    if pre_requisito_pedido(sender_id, loja_id, conversa):
        if len(conversa['itens_pedido']) > 0:
            menu = []
            limit = 10
            for i, item in enumerate(conversa['itens_pedido'][(0+offset):(limit+offset)]):
                add_item_pedido_menu(menu, (i+offset), repr(item['quantidade']) + ' ' + item['descricao'],
                                     offset=0 if (i/(limit-1) == 0) or len(conversa['itens_pedido']) == (limit+offset)
                                     else ((limit-1)+offset))
            set_variaveis(conversa,
                          itens_pedido=(False, None),
                          datetime_pedido=(False, None))
            if eh_msg_sucesso:
                bot = u'Alteração realizada com sucesso.'
            else:
                bot = 'Clique abaixo para voltar.'
            chain(send_generic_message.si(sender_id, loja_id, menu),
                  send_quickreply_message.si(sender_id, loja_id, bot, get_quickreply_voltar_menu(conversa)))()
        else:
            bot = get_mensagem('rever2')
            chain(send_text_message.si(sender_id, loja_id, bot),
                  send_generic_message.si(sender_id, loja_id, get_elements_menu(conversa)))()


def passo_trocar_mesa_2(message, sender_id, loja_id, conversa):
    set_variaveis(conversa,
                  itens_pedido=(False, None),
                  datetime_pedido=(False, None))
    mensagem_mesa(conversa, loja_id, sender_id)


def passo_novo_pedido(message, sender_id, loja_id, conversa):
    if not existe_pedido_andamento(sender_id, loja_id, conversa):
        set_variaveis(conversa, datetime_pedido=(True, datetime.datetime.utcnow()))
        conversa['passo'] = 14
        mensagem_pedido(sender_id, loja_id, conversa)


def mensagem_mesa(conversa, loja_id, sender_id):
    bot = get_mensagem('mesa')
    send_quickreply_message.delay(sender_id, loja_id, bot, get_quickreply_voltar_menu(conversa))


def passo_nao_entendido(message, sender_id, loja_id, conversa):
    bot = get_mensagem('robo')
    chain(send_text_message.si(sender_id, loja_id, bot), send_generic_message.si(sender_id, loja_id,
                                                                                 get_elements_menu(conversa)))()


def passo_agradecimento(message, sender_id, loja_id, conversa):
    bot = get_mensagem('agradeco')
    chain(send_text_message.si(sender_id, loja_id, bot), send_generic_message.si(sender_id, loja_id,
                                                                                 get_elements_menu(conversa)))()


def passo_tres(message, sender_id, loja_id, conversa):
    if pre_requisito_pedido(sender_id, loja_id, conversa):
        conversa['nao_entendidas'] += 1
        bot = get_mensagem('anotado2')
        send_quickreply_message.delay(sender_id, loja_id, bot, get_quickreply_pedido(conversa))


def passo_dois(message, sender_id, loja_id, conversa):
    if pre_requisito_pedido(sender_id, loja_id, conversa):
        anota_pedido(message, conversa)
        conversa['passo'] = 8
        set_variaveis(conversa,
                      itens_pedido=(False, None),
                      datetime_pedido=(False, None))
        bot = get_mensagem('anotado', arg1=conversa['usuario']['first_name'])
        send_quickreply_message.delay(sender_id, loja_id, bot, get_quickreply_pedido(conversa))


def passo_um(message, sender_id, loja_id, conversa):
    # send_image_message(sender_id, loja_id, 'cardapio01.jpg', 'image/jpeg')
    if pre_requisito_pedido(sender_id, loja_id, conversa):
        define_mesa(conversa['aux'], conversa)
        conversa['aux'] = None
        conversa['passo'] = 6
        set_variaveis(conversa,
                      itens_pedido=(False, None),
                      datetime_pedido=(False, None))
        mensagem_pedido(sender_id, loja_id, conversa)


def mensagem_pedido(sender_id, loja_id, conversa):
    bot = get_mensagem('pedido')
    bot1 = get_mensagem('pedido1')
    chain(send_text_message.si(sender_id, loja_id, bot),
          send_quickreply_message.si(sender_id, loja_id, bot1, get_quickreply_voltar_menu(conversa), icon=None))()


def passo_trocar_mesa(message, sender_id, loja_id, conversa):
    define_mesa(conversa['aux'], conversa)
    conversa['aux'] = None
    if len(conversa['mesa']) == 2 and conversa['mesa'][0] == conversa['mesa'][1]:
        bot = get_mensagem('mesa4')
        chain(send_text_message.si(sender_id, loja_id, bot),
              send_generic_message.si(sender_id, loja_id, get_elements_menu(conversa)))()
        return
    troca_mesa_dashboard.delay(sender_id, loja_id, conversa)
    set_variaveis(conversa,
                  itens_pedido=(False, None),
                  datetime_pedido=(False, None))
    bot = get_mensagem('mesa3', arg1=conversa['mesa'][0])
    chain(send_text_message.si(sender_id, loja_id, bot),
          send_generic_message.si(sender_id, loja_id, get_elements_menu(conversa)))()


def passo_menu(message, sender_id, loja_id, conversa):
    send_generic_message.delay(sender_id, loja_id, get_elements_menu(conversa))


def passo_ola(message, sender_id, loja_id, conversa):
    bot1 = get_mensagem('ola', arg1=conversa['usuario']['first_name'])
    chain(send_text_message.si(sender_id, loja_id, bot1),
          send_generic_message.si(sender_id, loja_id, get_elements_menu(conversa)))()


if __name__ == "__main__":
    context = ('fullchain.pem', 'privkey.pem')
    flask_app.run(host='0.0.0.0', port=5003, ssl_context=context, threaded=True, debug=True)
