import csv
import datetime
import os

import pandas as pd
import loguru
from celery import shared_task
from django.contrib.auth.models import User
from loguru import logger
from app_collector.models import Clients, Mailings, ClientsFiles
from collector.settings import BASE_DIR
from users.models import Profile, DyatelSettings, Transaction
from whatsapp_api_client_python import API
from whatsapp_api_client_python.response import Response

# В ивент лупе нельзя кидать запросы к БД, поэтому собираем всю инфу об отправке в этот словарик
# и после из него берём инфу для записи в таблицу рассылок.
# В словаре такой формат: {user_id: {send_status: str, send_datetime: datetime}}
SEND_RESULT = dict()


async def send_messages_async(app, contact, message, user_id, files_string):
    from pyrogram.types import InputMediaDocument

    files_lst = files_string.split('|')
    async with app:
        try:
            if len(files_lst) == 1:  # Один файл с подписью
                send_rslt = await app.send_document(
                    chat_id=str(contact),
                    document=files_lst[0],
                    caption=str(message)
                )
            elif len(files_lst) > 1:  # Файлы, как медиа группа с подписью
                send_rslt = await app.send_media_group(
                    chat_id=str(contact),
                    media=[InputMediaDocument(
                        media=i_file,
                        caption=message if i_indx == len(files_lst) - 1 else None)
                        for i_indx, i_file in enumerate(files_lst)]
                )
                send_rslt = send_rslt[-1]
            else:  # Отправка текстового сообщения
                send_rslt = await app.send_message(str(contact), str(message))

        except Exception as error:
            logger.warning(f'Отправка сообщения TG пользователю {contact} НЕ УДАЛОСЬ.\nОтвет телеграма:\n{error}')
            SEND_RESULT[user_id]['send_status'] = 'cncld'
            SEND_RESULT[user_id]['send_datetime'] = None
            SEND_RESULT[user_id]['send_info'] = f'⛔️Telegram вернул ошибку: {error}'
            return
        SEND_RESULT[user_id]['send_status'] = 'cmplt'
        SEND_RESULT[user_id]['send_datetime'] = send_rslt.date
        SEND_RESULT[user_id]['send_info'] = '👌Успешно отправлено'


@shared_task
def sending_messages_tlg(user_id):
    """
    Отложенная задача по рассылке сообщений клиентам пользователя в телеграм.
    """
    # ВАЖНО! импортировать именно локально. Какого-то хрена иначе ошибки летят с eventloop
    from pyrogram import Client
    logger.info(f'Старт отложенной задачи по TELEGRAM рассылке для пользователя с ID == {user_id}')

    # Получаем из БД нужные данные
    user_obj = User.objects.get(id=user_id)
    profile_obj = Profile.objects.get(user=user_obj)
    dflt_mlng_txt = profile_obj.dflt_mlng_txt
    company_name = profile_obj.company_name
    clients_lst = Clients.objects.filter(user=user_obj)
    tariff = DyatelSettings.objects.get(key='tariff').value.replace(' ', '')

    # Определяем клиент pyrogram
    app = Client(f'{BASE_DIR}/media/session_files/{user_id}_session')

    success_send_count = 0
    for i_client in clients_lst:
        SEND_RESULT[user_id] = dict()

        # Получим файлы для данного клиента
        files_lst = ClientsFiles.objects.filter(client=i_client)
        files_string = '|'.join([i_file.file.name for i_file in files_lst])

        message = dflt_mlng_txt if not i_client.custom_mlng_txt else i_client.custom_mlng_txt
        # Форматируем текст сообщения
        message = message.replace('{amount}', str(i_client.amount_of_pmnt))
        message = message.replace('{date}', i_client.pmnt_date.strftime('%-d.%m.%Y %H:%M'))
        message = message.replace('{client}', i_client.client_name)
        message = message.replace('{my_comp}', company_name)

        app.run(send_messages_async(app=app, contact=i_client.telephone_or_username,
                                    message=message, user_id=user_id, files_string=files_string))

        send_status = SEND_RESULT[user_id].get('send_status')
        send_datetime = SEND_RESULT[user_id].get('send_datetime')
        mailing_obj = Mailings.objects.filter(client=i_client).first()
        mailing_obj.sending_status = send_status
        mailing_obj.send_info = SEND_RESULT[user_id].get('send_info')
        if send_datetime:
            mailing_obj.sent_datetime = send_datetime
        mailing_obj.save()

        # При успешной отправке, отнимаем бабки от суммы резерва
        if send_status == 'cmplt':
            profile_obj.reserved_for_mailing = float(profile_obj.reserved_for_mailing) - float(tariff)
            profile_obj.save()
            success_send_count += 1

    # Возвращаем на баланс, если что-то осталось в зарезервированной сумме
    profile_obj.balance = float(profile_obj.balance) + float(profile_obj.reserved_for_mailing)
    profile_obj.save()
    # Записываем транзакцию о возврате остатка после рассылки
    Transaction.objects.create(
        user=user_obj,
        transaction_type='replenishment',
        amount=float(profile_obj.reserved_for_mailing),
        description=f'Возврат остатка от зарезервированных для рассылки средств '
                    f'({float(profile_obj.reserved_for_mailing)} руб.). Тариф за рассылку: {tariff} руб., '
                    f'кол-во успешных отправок: {success_send_count}, всего клиентов для рассылки: {len(clients_lst)}'
    )
    logger.success(f'ОКОНЧАНИЕ отложенной задачи по рассылки для пользователя с ID == {user_id}')


@shared_task
def sending_messages_whtsp(user_id):
    """
    Отложенная задача по рассылке сообщений клиентам юзера через WhatsApp.
    """
    logger.info(f'Старт отложенной задачи по WHATSAPP рассылке для пользователя с ID == {user_id}')

    # Достаём из БД данные для рассылки
    user_obj = User.objects.get(id=user_id)
    profile_obj = Profile.objects.get(user=user_obj)
    dflt_mlng_txt = profile_obj.dflt_mlng_txt
    company_name = profile_obj.company_name
    clients_lst = Clients.objects.filter(user=user_obj)
    tariff = DyatelSettings.objects.get(key='tariff').value.replace(' ', '')

    success_send_count = 0
    for i_client in clients_lst:  # Итерируемся по списку клиентов
        mailing_obj = Mailings.objects.filter(client=i_client).first()

        message = dflt_mlng_txt if not i_client.custom_mlng_txt else i_client.custom_mlng_txt
        # Форматируем текст сообщения
        message = message.replace('{amount}', str(i_client.amount_of_pmnt))
        message = message.replace('{date}', i_client.pmnt_date.strftime('%-d.%m.%Y %H:%M'))
        message = message.replace('{client}', i_client.client_name)
        message = message.replace('{my_comp}', company_name)

        # Отправляем сообщение в ватсап
        green_api = API.GreenApi(profile_obj.green_api_id_instance, profile_obj.green_api_token_instance)
        auth_status_rslt: Response = green_api.sending.sendMessage(
            f'{i_client.telephone_or_username.replace("+", "")}@c.us',
            message
        )
        # Получим файлы для данного клиента
        files_lst = ClientsFiles.objects.filter(client=i_client)
        send_files_rslt = []
        if len(files_lst) > 0:  # Если для клиента есть файлы
            for j_file in files_lst:
                # Отправляем файл в ватсап
                send_file_status: Response = green_api.sending.sendFileByUpload(
                    chatId=f'{i_client.telephone_or_username.replace("+", "")}@c.us',
                    path=f"{BASE_DIR}/media/{j_file.file.name}",
                    fileName=j_file.file_name
                )
                # Проверяем результат отправки
                if send_file_status.code == 200:
                    logger.success(f'\t\tФайл успешно отправлен')
                    send_files_rslt.append(True)
                else:
                    logger.warning(f'\t\tФайл не отправлен')
                    send_files_rslt.append(False)

        else:  # Если файлов для клиента нет
            send_files_rslt = [True]  # Добавляем True для заглушки

        # Проверка результатов отправки и запись их в БД
        if auth_status_rslt.code == 200 and all(send_files_rslt):
            logger.success(f'\tУспешная отправка сообщения в WhatsApp. Контакт: {i_client.telephone_or_username}')
            mailing_obj.sending_status = 'cmplt'
            mailing_obj.send_info = f'👌Успешно отправлено | ' \
                                    f'ID сообщения WhatsApp: {auth_status_rslt.data.get("idMessage")}'
            mailing_obj.sent_datetime = datetime.datetime.now()
            success_send_count += 1
            # Отнимаем бабки за отправку от зарезервированных средств
            profile_obj.reserved_for_mailing = float(profile_obj.reserved_for_mailing) - float(tariff)
            profile_obj.save()

        else:
            logger.warning(f'\tНеудачная отправка сообщения в WhatsApp. Контакт: {i_client.telephone_or_username}\n'
                           f'Контакт: {i_client.telephone_or_username} | Текст сообщения: {message}')
            mailing_obj.sending_status = 'cncld'
            mailing_obj.send_info = f'⛔️Сообщение не отправлено. ' \
                                    f'Возможно Вы не можете писать контакту: {i_client.telephone_or_username}'
            mailing_obj.sent_datetime = None
        mailing_obj.save()

    # Возвращаем на баланс, если что-то осталось в зарезервированной сумме
    profile_obj.balance = float(profile_obj.balance) + float(profile_obj.reserved_for_mailing)
    profile_obj.save()
    # Записываем транзакцию о возврате остатка после рассылки
    Transaction.objects.create(
        user=user_obj,
        transaction_type='replenishment',
        amount=float(profile_obj.reserved_for_mailing),
        description=f'Возврат остатка от зарезервированных для рассылки средств '
                    f'({float(profile_obj.reserved_for_mailing)} руб.). Тариф за рассылку: {tariff} руб., '
                    f'кол-во успешных отправок: {success_send_count}, всего клиентов для рассылки: {len(clients_lst)}'
    )
    logger.success(f'ОКОНЧАНИЕ отложенной задачи по WhatsApp рассылке для пользователя с ID == {user_id}')


@shared_task
def file_processing_with_clients(file_path, user_pk):
    """
    Задачка celery по обработке файла с клиентами.
    """
    logger.info(f'Старт задачи по обработке файла с клиентами')

    # Преобразуем файл из excel в csv и сохраняем на диск. Файл в excel затем удаляем.
    excel_file = pd.read_excel(file_path)
    csv_path = f'{os.path.splitext(file_path)[0]}.csv'
    excel_file.to_csv(csv_path, index=False)
    os.remove(file_path)

    user_obj = User.objects.get(pk=user_pk)

    with open(csv_path, 'r') as csvfile:
        readable_file = csv.reader(csvfile)
        next(readable_file)  # Пропускаем строку с заголовками
        for i_row in readable_file:
            try:
                Clients.objects.update_or_create(
                    telephone_or_username=i_row[1],
                    defaults={
                        "user": user_obj,
                        "client_name": i_row[0],
                        "telephone_or_username": i_row[1],
                        "amount_of_pmnt": i_row[2],
                        "pmnt_date": i_row[3],
                    }
                )
                logger.success(f'Строка записана!')
            except Exception as error:
                loguru.logger.warning(f'Не удалось записать строку: {i_row[0], i_row[1], i_row[2], i_row[3]}\n'
                                      f'Текст ошибки: {error}')
    # Удаляем csv файл после обработки
    os.remove(csv_path)
    logger.info(f'Окончание задачи по обработки файла с клиентами')
