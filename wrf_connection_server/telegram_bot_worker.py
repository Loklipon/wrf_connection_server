import asyncio
import json
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
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wrf_connection_server.settings')
django.setup()

from organization.models import OrganizationUnit, TerminalGroup, Organization, Terminal
from bot.models import TelegramBot
from clients.models import ClientPhone

dp = Dispatcher()


async def get_telegram_bot_token():
    telegram_bot = await sync_to_async(TelegramBot.objects.first)()
    return telegram_bot.token


def create_contact_keyboard():
    buttons = [[KeyboardButton(text='Отправить номер', request_contact=True)]]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


def create_send_message_keyboard():
    buttons = [[KeyboardButton(text='Отправить сообщение')]]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


def create_org_units_keyboard(org_units_names, org_units_name_uuid_dict):
    for i, element in enumerate(org_units_names):
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


async def send_message_to_iiko_front(client_contact, message):
    terminals = await sync_to_async(Terminal.objects.filter)(
        terminal_group__organization_unit__uuid=client_contact.org_unit_to_send,
        channel_name__isnull=False)
    body = {
        'id': str(uuid.uuid4()),
        'type': 'send.message',
        'params': {
            'text': message.text
        },
        'tg_chat_id': message.chat.id,
    }

    async for terminal in terminals:
        body['terminal'] = str(terminal.uuid)
        try:
            channel_name = terminal.channel_name
            channel_layer = get_channel_layer()
            await channel_layer.send(
                channel_name,
                body
            )
        except Exception as e:
            print(e)
        finally:
            continue

    client_contact.org_unit_to_send = None
    await sync_to_async(client_contact.save)()


async def check_contact_authentication(message):
    phone_number = f'+{message.contact.phone_number.replace("+", "")}'
    client_phones = await sync_to_async(ClientPhone.objects.filter)(phone_number=phone_number,
                                                                    telegram_chat_id__isnull=True)
    if client_phone := await sync_to_async(client_phones.first)():
        await message.answer('Вы успешно авторизовались',
                             reply_markup=create_send_message_keyboard())
        client_phone.telegram_chat_id = message.chat.id
        await sync_to_async(client_phone.save)()
        return

    client_phones_with_tg_contact = await sync_to_async(ClientPhone.objects.filter)(phone_number=phone_number,
                                                                                    telegram_chat_id=message.chat.id)
    if await sync_to_async(client_phones_with_tg_contact.first)():
        await message.answer('Вы уже авторизовались ранее',
                             reply_markup=create_send_message_keyboard())
    else:
        await message.answer('Доступ запрещен')


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

    client_phones = await sync_to_async(ClientPhone.objects.filter)(telegram_chat_id=message.chat.id, client__send_message=True)
    client_phone = await sync_to_async(client_phones.first)()
    if not client_phone:
        await message.answer('Доступ запрещен')
        return

    if message.text == 'Отправить сообщение':

        org_units_list = await sync_to_async(get_organization_units_list)(message)
        if len(org_units_list) == 0:
            await message.answer('У вас нет доступных торговых точек')
            return

        organizations = await sync_to_async(Organization.objects.filter)()
        if organization := await sync_to_async(organizations.first)():

            if len(org_units_list) == 1:
                client_phone.org_unit_to_send = organization.organization_units_dict[org_units_list[0][0]]
                await sync_to_async(client_phone.save)()
                await message.answer('Напишите ваше сообщение')
                return

            keyboard = create_org_units_keyboard(org_units_list, organization.organization_units_dict)
            await message.answer('Выберите, куда вы хотели бы написать',
                                 reply_markup=keyboard)
            return

    client_phones = await sync_to_async(ClientPhone.objects.filter)(telegram_chat_id=message.chat.id,
                                                                    client__send_message=True,
                                                                    org_unit_to_send__isnull=False)
    client_phone = await sync_to_async(client_phones.first)()
    if not client_phone:
        await message.answer('Нет ни одной выбранной торговой точки')
        return

    await send_message_to_iiko_front(client_phone, message)


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
