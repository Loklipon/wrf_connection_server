import json

import uuid

from bot.models import TelegramBot
from aiogram import Bot
from channels_jsonrpc import AsyncJsonRpcWebsocketConsumer
from asgiref.sync import sync_to_async, async_to_sync

from clients.models import Client, ClientPhone
from log.models import WsLog
from organization.models import OrganizationUnit, Terminal


class IikoFrontConsumer(AsyncJsonRpcWebsocketConsumer):

    async def disconnect(self, code):
        channel_name = self.channel_name
        terminals = await sync_to_async(Terminal.objects.filter)(channel_name=channel_name)
        if terminal := await sync_to_async(terminals.first)():
            terminal.channel_name = None
            terminal.plugin_online = False
            await sync_to_async(terminal.save)()

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        if bytes_data:
            text_data = bytes_data.decode('UTF-8')
        data = json.loads(text_data)
        text_data = json.dumps(data)
        return await super().receive(text_data=text_data, bytes_data=bytes_data, **kwargs)

    async def send_message(self, data):
        payload = {
            'id': str(uuid.uuid4()),
            'jsonrpc': '2.0',
            'method': 'SendMessage',
            'params': data['params']
        }
        await sync_to_async(WsLog.objects.create)(correlation_id=payload['id'],
                                                  request=json.dumps(payload, ensure_ascii=False).encode('utf8').decode(),
                                                  method='TG -> SERVER -> iikoFront Plugin Message',
                                                  telegram_chat_id=data['tg_chat_id'])
        await self.send_json(payload)

    async def receive_json(self, content):
        if 'method' not in content.keys() and 'id' in content.keys():
            ws_logs = await sync_to_async(WsLog.objects.filter)(correlation_id=content['id'],
                                                                telegram_chat_id__isnull=False)
            if ws_log := await sync_to_async(ws_logs.first)():
                ws_log.response = content
                await sync_to_async(ws_log.save)()
                telegram_bot_data = await sync_to_async(TelegramBot.objects.first)()
                telegram_bot = Bot(token=telegram_bot_data.token)
                await telegram_bot.send_message(
                    chat_id=ws_log.telegram_chat_id,
                    text='Сообщение успешно отправлено')
                return 'OK'
        res = await super(IikoFrontConsumer, self).receive_json(content)
        return res


@IikoFrontConsumer.rpc_method('Authentication')
async def authentication(**kwargs):
    channel_name = kwargs['consumer'].channel_name
    terminals = await sync_to_async(Terminal.objects.filter)(uuid=kwargs['terminalGroupId'])
    if terminal := await sync_to_async(terminals.first)():
        terminal.plugin_online = True
        terminal.channel_name = channel_name
        await sync_to_async(terminal.save)()
        return 'OK'
    return 'ERROR'


@IikoFrontConsumer.rpc_method('Clients')
async def get_clients(**kwargs):
    channel_name = kwargs['consumer'].channel_name
    terminals = await sync_to_async(Terminal.objects.filter)(channel_name=channel_name)
    terminal = await sync_to_async(terminals.first)()
    if not terminal:
        return 'ERROR'
    organization_units = await sync_to_async(OrganizationUnit.objects.filter)(terminal=terminal)
    organization_unit = await sync_to_async(organization_units.first)()
    if not organization_unit:
        return 'ERROR'
    data_clients = kwargs['clients']
    for data_client in data_clients:
        client, _ = await sync_to_async(Client.objects.update_or_create)(
            uuid=data_client['id'],
            defaults={'name': data_client['fio'],
                      'organization_unit': organization_unit})
        phones = data_client['phones']
        for phone in phones:
            await sync_to_async(ClientPhone.objects.update_or_create)(phone_number=phone,
                                                                      defaults={'client': client})
    return 'OK'


def sending_message(channel_name, message):
    if terminal := Terminal.objects.filter(channel_name=channel_name).first():
        client_contacts = ClientPhone.objects.filter(client__get_message=True, telegram_chat_id__isnull=False)
        telegram_bot_token = TelegramBot.objects.first().token
        telegram_bot = Bot(token=telegram_bot_token)
        organization_unit = OrganizationUnit.objects.filter(terminal=terminal).first()
        message_to_send = (f'Касса: {terminal.name} / {organization_unit.name}'
                           f'\n'
                           f'Сообщение: {message}')
        for client_contact in client_contacts:
            async_to_sync(telegram_bot.send_message)(chat_id=client_contact.telegram_chat_id,
                                                     text=message_to_send)


@IikoFrontConsumer.rpc_method('SendMessage')
async def send_message(**kwargs):
    channel_name = kwargs['consumer'].channel_name
    message = kwargs['text']
    await sync_to_async(sending_message)(channel_name, message)
    return 'OK'
