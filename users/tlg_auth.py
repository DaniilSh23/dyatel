from django.contrib.auth.models import User
from collector.settings import TG_API_ID, TG_API_HASH, BASE_DIR, TELEGRAM_CLIENTS_DCT, TELEGRAM_AUTH_RESULTS, LOOP
from users.models import Profile
from loguru import logger


async def send_auth_code(user_id, phone_number):
    """
    Функция для отправки кода подтверждения авторизации на номер, привязанный к телеграм.
    """
    from pyrogram import Client
    from pyrogram.errors import BadRequest
    client = Client(
        f"{user_id}_session",
        api_id=TG_API_ID,
        api_hash=TG_API_HASH,
        phone_number=phone_number,
        workdir=f"{BASE_DIR}/media/session_files/",
    )
    TELEGRAM_CLIENTS_DCT[user_id] = client
    await client.connect()
    # Отправляем код
    try:
        sent_code = await client.send_code(phone_number=phone_number)
        TELEGRAM_AUTH_RESULTS[phone_number] = {'sent_code': sent_code}
        result, description = True, sent_code
    except BadRequest as error:
        result, description = False, error
    except Exception as other_error:
        result, description = False, other_error
    return result, description


def init_tlg_client(user_id, phone_number):
    """
    Создаём объект клиента телеграмма.
    # """
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    result = LOOP.run_until_complete(send_auth_code(user_id=user_id, phone_number=phone_number))
    return result   # (result: bool, description: SentCode | BadRequest)


async def check_confirm_code(user_id, code):
    """
    Функция для проверки кода подтверждения.
    """
    from pyrogram.errors import BadRequest, SessionPasswordNeeded

    client = TELEGRAM_CLIENTS_DCT[user_id]
    sent_code = TELEGRAM_AUTH_RESULTS[client.phone_number]['sent_code']  # Достаём ответ после отправки номера телефона
    phone_code_hash = sent_code.phone_code_hash
    try:
        signed_in = await client.sign_in(client.phone_number, phone_code_hash, code)  # Вернёт объект User
        await client.initialize()
        await client.get_contacts()  # Получаем список собственных контактов
        await client.stop()
        success = True  # Результат запроса
        two_fa_need = False     # Нужен ли пароль 2-ФА
        # Очищаем словари, чтобы он не забивали память
        TELEGRAM_AUTH_RESULTS.pop(client.phone_number)
        TELEGRAM_CLIENTS_DCT.pop(user_id)
        return success, two_fa_need, signed_in
    except SessionPasswordNeeded:
        pass_hint = await client.get_password_hint()
        TELEGRAM_AUTH_RESULTS[client.phone_number] = {'pass_hint': pass_hint}
        success = True
        two_fa_need = True
        return success, two_fa_need, pass_hint
    except BadRequest as error:
        success = False
        two_fa_need = False
        return [success, two_fa_need, error]


def confirm_code(user_id, code):
    """
    Достаём объект клиента pyrogram и проверяем код подтверждения.
    """
    # loop = TELEGRAM_CLIENTS_DCT[user_id].loop
    result = LOOP.run_until_complete(check_confirm_code(user_id=user_id, code=code))
    if result[0] and not result[1]:  # Если успешная авторизация или BadRequest
        # loop.close()
        # Привязываем файл session_string к профилю
        profile_obj = Profile.objects.get(id=user_id)
        profile_obj.tlg_session_file = f'{BASE_DIR}/media/session_files/{user_id}_session.session'
        profile_obj.save()
        # Проверяем работу сессии
        check_session_rslt = checking_the_session(user_id=user_id)
        if not check_session_rslt:  # Если проверка сессии НЕ удалась
            result.append(False)
    return result  # (success: bool, two_fa_need: bool, description: User | pass_hint | error)


async def check_2fa_tlg_password(user_id, two_fa_pass):
    """
    Проверяем пароль 2-ФА, кидаём запрос в телеграм.
    Проверка введённого пароля. Вернёт объект User (как и метод sing_in в случае успеха) или exception BadRequest
    """
    from pyrogram.errors import BadRequest

    client = TELEGRAM_CLIENTS_DCT[user_id]
    try:
        await client.check_password(password=two_fa_pass)
        # Очищаем словари, чтобы они не забивали память
        TELEGRAM_AUTH_RESULTS.pop(client.phone_number)
        TELEGRAM_CLIENTS_DCT.pop(user_id)
        await client.initialize()
        await client.get_contacts()  # Получаем список собственных контактов
        await client.stop()
        return True     # Возвращаем результат проверки пароля
    except BadRequest as error:
        return False


def check_2fa_pass(user_id, two_fa_pass):
    """
    Проверяем пароль 2-ФА.
    """
    # loop = TELEGRAM_CLIENTS_DCT[user_id].loop
    result = LOOP.run_until_complete(check_2fa_tlg_password(user_id=user_id, two_fa_pass=two_fa_pass))
    if result:  # Если удалось авторизоваться
        # loop.close()
        # Привязываем файл session_string к профилю
        user_obj = User.objects.get(id=user_id)
        profile_obj = Profile.objects.get(user=user_obj)
        profile_obj.tlg_session_file = f'{BASE_DIR}/media/session_files/{user_id}_session.session'
        profile_obj.save()
        # Проверяем работу сессии
        check_session_rslt = checking_the_session(user_id=user_id)
        if check_session_rslt:  # Если проверка сессии была успешной
            return [True, True]
        else:   # Если пароль верный, но проверка сессии не удалась
            return [True, False]
    else:   # Если не получилось авторизоваться или проверка сессии не удалась
        return [False]


async def send_test_message(user_id, session_string=None):  # TODO: session_string скорее всего надо убрать
    """
    Отправка тестового сообщения в чат "Избранное" пользователя телеграм.
    """
    from pyrogram import Client

    # async with Client(f"{user_id}_session_string", session_string=session_string) as client:
    async with Client(f'{BASE_DIR}/media/session_files/{user_id}_session') as client:
        try:
            await client.send_message('me', '<b>TEST MESSAGE FROM <u>DYATEL</u>!<b>\nEverything ok👌')
            await client.send_message('me', '🐦')
            this_user = await client.get_users("me")
            print()
            result = (True, this_user.id, this_user.first_name, this_user.last_name)
        except Exception as error:
            logger.warning(f'Ошибка при проверке сессии. Не удалось отправить сообщение для проверки.\n\t{error}')
            result = (False,)

        # # Экспорт сессии в строку
        # session_string = await client.export_session_string()
        # with open(f'{BASE_DIR}/media/session_files/{user_id}_session_string',
        #           mode='w', encoding='utf-8') as session_str_file:
        #     session_str_file.write(session_string)
    return result


def checking_the_session(user_id):
    """
    Проверка работы новой сессии пользователя телеграм.
    """
    # TODO: логика со строкой сессии, скорее всего, будет не актуальна
    # # Вытаскиваем строку сессии из БД
    # user_obj = User.objects.get(id=user_id)
    # session_file_path = Profile.objects.get(user=user_obj).tlg_session_file
    # session_string = str(session_file_path.read(), 'UTF-8')
    # result = LOOP.run_until_complete(send_test_message(user_id=user_id, session_string=session_string))
    result = LOOP.run_until_complete(send_test_message(user_id=user_id))
    if result[0]:
        # Записываем инфо об аккаунте телеграм
        profile_obj = Profile.objects.get(user=User.objects.get(id=user_id))
        profile_obj.tlg_acc_info = f'TG ID: {result[1]} | {result[2], result[3]}'
        profile_obj.save()
    return result[0]

