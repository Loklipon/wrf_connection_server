import asyncio
import os
import uuid

import django
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.types.contact import Contact
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from asgiref.sync import sync_to_async, async_to_sync
from channels.layers import get_channel_layer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wrf_connection_server.settings')
django.setup()

from organization.models import OrganizationUnit, Organization, Terminal
from bot.models import TelegramBot
from clients.models import ClientPhone, Client

dp = Dispatcher()


async def get_telegram_bot_token():
    telegram_bot = await sync_to_async(TelegramBot.objects.first)()
    return telegram_bot.token


def create_contact_keyboard():
    buttons = [[KeyboardButton(text='Отправить номер', request_contact=True)]]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


def create_settings_keyboard():
    buttons = [[KeyboardButton(text='Настройки')]]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


def create_org_units_keyboard(org_units_names, org_units_name_uuid_dict, terminal_uuid):

    if terminal_uuid:
        org_name = OrganizationUnit.objects.filter(uuid=terminal_uuid).first().name
    else:
        org_name = None

    for i, element in enumerate(org_units_names):
        if org_name and element[0] == org_name:
            element[0] = InlineKeyboardButton(text=f'{org_name} \U00002705',
                                              callback_data=org_units_name_uuid_dict[element[0]])
        else:
            element[0] = InlineKeyboardButton(text=element[0],
                                              callback_data=org_units_name_uuid_dict[element[0]])
    keyboard = InlineKeyboardMarkup(inline_keyboard=org_units_names)
    return keyboard


def create_terminals_keyboard(split_terminals_list, terminals_dict):
    for element_pair in split_terminals_list:
        for i, terminal_name in enumerate(element_pair):
            element_pair[i] = InlineKeyboardButton(text=terminal_name,
                                                   callback_data=terminals_dict[terminal_name])
    keyboard = InlineKeyboardMarkup(inline_keyboard=split_terminals_list)
    return keyboard


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(
        'Для дальнейшей работы необходимо отправить свой номер телефона',
        reply_markup=create_contact_keyboard()
    )


def send_message_to_iiko_front(client_contact, message):
    terminals = Terminal.objects.filter(terminal_group__organization_unit__uuid=client_contact.org_unit_to_send,
                                        channel_name__isnull=False)
    body = {
        'id': str(uuid.uuid4()),
        'type': 'send.message',
        'params': {
            'text': message.text
        },
        'tg_chat_id': message.chat.id,
    }
    for terminal in terminals:
        body['terminal'] = str(terminal.uuid)
        try:
            channel_name = terminal.channel_name
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(
                channel_name,
                body
            )
        except Exception as e:
            print(e)
        finally:
            continue


async def check_contact_authentication(message):
    phone_number = f'+{message.contact.phone_number.replace("+", "")}'
    client_phones = await sync_to_async(ClientPhone.objects.filter)(phone_number=phone_number,
                                                                    telegram_chat_id__isnull=True)
    org_units_list = await sync_to_async(get_organization_units_list)(message)

    if client_phone := await sync_to_async(client_phones.first)():

        client_phone.telegram_chat_id = message.chat.id
        await sync_to_async(client_phone.save)()
        org_units_list = await sync_to_async(get_organization_units_list)(message)

        clients = await sync_to_async(Client.objects.filter)(phone=client_phone)
        client = await sync_to_async(clients.first)()
        if client and not client.send_message:
            await message.answer(f'Вы успешно авторизовались.\n'
                                 f'Вы не можете отправлять сообщения на торговые точки.\n'
                                 f'Обратитесь к вашему администратору.\n'
                                 f'Для дальнейшей работы напишите и отправьте сообщение в этот чат.',
                                 reply_markup=ReplyKeyboardRemove())
            return

        if len(org_units_list) == 1:
            organizations = await sync_to_async(Organization.objects.filter)()
            if organization := await sync_to_async(organizations.first)():
                client_phone.org_unit_to_send = organization.organization_units_dict[org_units_list[0][0]]
                await sync_to_async(client_phone.save)()
            await message.answer(f'Вы успешно авторизовались.\n'
                                 f'Для вас доступна торговая точка {org_units_list[0][0]}.\n'
                                 f'Для отправки сообщения на данную торговую точку напишите и отправьте его',
                                 reply_markup=ReplyKeyboardRemove())
        elif len(org_units_list) == 0:
            await message.answer(f'Вы успешно авторизовались.\n'
                                 f'У вас нет доступных торговых точек.\n'
                                 f'Попросите администратора добавить их.\n'
                                 f'Для дальнейшей работы отправьте любое сообщение в этот чат.',
                                 reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer('Вы успешно авторизовались.\n'
                                 'Для вас доступно несколько торговых точек.\n'
                                 'Для отправки сообщения выберите торговую точку, нажав кнопку "Настройки".',
                                 reply_markup=create_settings_keyboard())
        return

    client_phones_with_tg_contact = await sync_to_async(ClientPhone.objects.filter)(phone_number=phone_number,
                                                                                    telegram_chat_id=message.chat.id)
    client_obj = await sync_to_async(client_phones_with_tg_contact.first)()
    if client_obj:

        if len(org_units_list) == 1:
            await message.answer(f'Вы уже авторизовывались ранее.\n'
                                 f'Для вас доступна торговая точка {org_units_list[0][0]}.\n'
                                 f'Для отправки сообщения на данную торговую точку напишите и отправьте его.',
                                 reply_markup=ReplyKeyboardRemove())
        elif len(org_units_list) == 0:
            await message.answer(f'Вы уже авторизовывались ранее.\n'
                                 f'У вас нет доступных торговых точек.\n'
                                 f'Попросите администратора добавить их.\n'
                                 f'Для дальнейшей работы отправьте любое сообщение в этот чат.',
                                 reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer('Вы уже авторизовывались ранее.\n'
                                 'Для вас доступно несколько торговых точек.\n'
                                 'Для отправки сообщения выберите торговую точку, нажав кнопку "Настройки".',
                                 reply_markup=create_settings_keyboard())
    else:
        await message.answer('Доступ запрещен.\n'
                             'Попросите администратора добавить ваш номер телефона.')


def get_organization_units_list(message):
    org_units = OrganizationUnit.objects.filter(
        client__phone__telegram_chat_id=message.chat.id).values_list('name', flat=True).distinct()
    org_units_list = list(org_units)
    for i, element in enumerate(org_units_list):
        org_units_list[i] = list()
        org_units_list[i].append(element)
    return org_units_list


@dp.message()
async def get_message(message: Message):

    if isinstance(message.contact, Contact):
        await check_contact_authentication(message)
        return

    client_phones = await sync_to_async(ClientPhone.objects.filter)(telegram_chat_id=message.chat.id,
                                                                    client__send_message=True)
    client_phone = await sync_to_async(client_phones.first)()

    if not client_phone:
        await message.answer(f'Вы не можете отправлять сообщения на торговые точки.\n'
                             f'Обратитесь к вашему администратору.\n'
                             f'Для дальнейшей работы отправьте любое сообщение в этот чат.',
                             reply_markup=ReplyKeyboardRemove())
        return

    if message.text == 'Настройки':

        org_units_list = await sync_to_async(get_organization_units_list)(message)
        if len(org_units_list) == 0:
            await message.answer('У вас нет доступных торговых точек.\n'
                                 'Попросите администратора добавить их.\n'
                                 'Для дальнейшей работы отправьте любое сообщение в этот чат.')
            return

        organizations = await sync_to_async(Organization.objects.filter)()
        if organization := await sync_to_async(organizations.first)():

            if len(org_units_list) == 1:
                client_phone.org_unit_to_send = organization.organization_units_dict[org_units_list[0][0]]
                await sync_to_async(client_phone.save)()
                await message.answer(f'Для вас доступна торговая точка {org_units_list[0][0]}.\n'
                                     f'Для отправки сообщения на данную торговую точку напишите и отправьте его',
                                     reply_markup=ReplyKeyboardRemove())
                return

            if client_phone.org_unit_to_send:
                keyboard = await sync_to_async(create_org_units_keyboard)(org_units_list,
                                                                          organization.organization_units_dict,
                                                                          client_phone.org_unit_to_send)
            else:
                keyboard = await sync_to_async(create_org_units_keyboard)(org_units_list,
                                                                          organization.organization_units_dict,
                                                                          None)
            await message.answer('Выберите торговую точку',
                                 reply_markup=keyboard)
            return

    qs = await sync_to_async(ClientPhone.objects.filter)(telegram_chat_id=message.chat.id,
                                                         client__send_message=True,
                                                         org_unit_to_send__isnull=True)
    qs_obj = await sync_to_async(qs.first)()
    if qs_obj:
        org_units_list = await sync_to_async(get_organization_units_list)(message)
        if len(org_units_list) == 1:
            organizations = await sync_to_async(Organization.objects.filter)()
            if organization := await sync_to_async(organizations.first)():
                qs_obj.org_unit_to_send = organization.organization_units_dict[org_units_list[0][0]]
                await sync_to_async(qs_obj.save)()
                await message.answer(f'Для вас доступна торговая точка {org_units_list[0][0]}.\n'
                                     f'Для отправки сообщения на данную торговую точку напишите и отправьте его',
                                     reply_markup=ReplyKeyboardRemove())
                return
        if len(org_units_list) > 1:
            await message.answer('Для вас доступно несколько торговых точек.\n'
                                 'Для отправки сообщения выберите торговую точку, нажав кнопку "Настройки".',
                                 reply_markup=create_settings_keyboard())
            return
        if len(org_units_list) == 0:
            await message.answer('У вас нет доступных торговых точек.\n'
                                 'Попросите администратора добавить их.\n'
                                 'Для дальнейшей работы отправьте любое сообщение в этот чат.')
            return

    terminals = await sync_to_async(
        Terminal.objects.filter)(terminal_group__organization_unit__uuid=client_phone.org_unit_to_send,
                                 plugin_online=True)
    terminal = await sync_to_async(terminals.first)()
    if terminal:
        org_units = await sync_to_async(OrganizationUnit.objects.filter)(uuid=client_phone.org_unit_to_send)
        org_unit = await sync_to_async(org_units.first)()
        org_unit_name = org_unit.name
        await message.answer(f'Ваше сообщение отправлено на торговую точку {org_unit_name}')
        await sync_to_async(send_message_to_iiko_front)(client_phone, message)
    else:
        await message.answer('Не удалось отправить сообщение.\n'
                             'У данной торговой точки нет ни одного терминала онлайн.\n'
                             'Для дальнейшей работы отправьте любое сообщение в этот чат.')
        return


@dp.callback_query()
async def get_terminal(callback: types.CallbackQuery):
    phone_clients = await sync_to_async(ClientPhone.objects.filter)(telegram_chat_id=callback.message.chat.id)
    phone_client = await sync_to_async(phone_clients.first)()
    phone_client.org_unit_to_send = callback.data
    await sync_to_async(phone_client.save)()
    await callback.message.answer('Напишите ваше сообщение')


async def start_bot():
    await dp.start_polling(Bot(token=await get_telegram_bot_token(), parse_mode=ParseMode.HTML))


if __name__ == '__main__':
    asyncio.run(start_bot())
