import base64
import datetime
import math
import os
import random
import string
from datetime import timedelta
from urllib.parse import quote
import loguru
from django.contrib.auth.models import User
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.contrib import messages
from loguru import logger
# Импорты для работы с GreenApi (WhatsApp)
from whatsapp_api_client_python import API
from whatsapp_api_client_python.response import Response as WhatsResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from app_collector.forms import DfltMsgForm, UploadFileForm, SendFeedbackForm, UpdateOrCreateClientForm, \
    MultiplyFileForm
from app_collector.models import Clients, Mailings, Feedback, ClientsFiles
from collector.settings import MEDIA_ROOT, BASE_DIR
from users.forms import PhoneVerificationForm
from users.models import Profile, DyatelSettings, Transaction
from users.utils import send_sms


class PrepareToMailingView(View):
    """
    Вьюшка для обработки запросов к странице рассылки.
    """

    def get(self, request, format=None, page_number=1):
        """
        Обработка GET запроса.
        """
        if request.user.is_anonymous:  # Если пользователь анонимный(незалогинен)
            return redirect(to='/users/login/')  # Редиректим его на страницу логина

        clients_lst = Clients.objects.filter(user=request.user)
        profile_obj = Profile.objects.get(user=request.user)
        user_dflt_mlng_txt = profile_obj.dflt_mlng_txt
        transactions_lst = Transaction.objects.filter(user=request.user)[:3]
        reg_bonus = DyatelSettings.objects.get(key='reg_bonus').value

        rslt_clients_lst = []
        for i_client in clients_lst:
            i_pmnt_date = i_client.pmnt_date + timedelta(hours=3)
            rslt_clients_lst.append({
                'client_name': i_client.client_name,
                'telephone_or_username': i_client.telephone_or_username,
                # Если кастомный текс пустой, то в это значение упадёт дефолтный текст
                'custom_mlng_txt': user_dflt_mlng_txt if not i_client.custom_mlng_txt else i_client.custom_mlng_txt,
                'amount_of_pmnt': i_client.amount_of_pmnt,
                'pmnt_date': i_client.pmnt_date,
                'user_dflt_mlng_txt': user_dflt_mlng_txt,  # Стандартн. текст из профиля пользователя
                'client_id': i_client.id,
                'form_date_value': i_pmnt_date.strftime("%Y-%m-%dT%H:%M"),
                "files_lst": ClientsFiles.objects.filter(client=i_client),
            })

        paginator = Paginator(object_list=rslt_clients_lst, per_page=7)
        clients_lst_paginator = paginator.page(number=page_number)
        change_dflt_txt_form = DfltMsgForm(user=request.user)
        exist_tlg_session_file = True if profile_obj.tlg_session_file else False

        # Работаем над отображением инфы об аккаунте WhatsApp
        if not profile_obj.green_api_id_instance and not profile_obj.green_api_token_instance:
            whts_auth_status = None
        else:  # Если параметры для GreenApi записаны в профиле пользователя
            # Получение статуса авторизации аккаунта
            green_api = API.GreenApi(profile_obj.green_api_id_instance, profile_obj.green_api_token_instance)
            auth_status_rslt: WhatsResponse = green_api.account.getStateInstance()
            if auth_status_rslt.code != 200:  # Если запрос к GreenAPI неудачный
                logger.warning(f'НЕУДАЧНЫЙ запрос к GreenAPI для получения статуса авторизации')
                whts_auth_status = None
            else:  # Если запрос к GreenAPI успешный
                whts_auth_status = auth_status_rslt.data.get('stateInstance')

        context = {
            'change_dflt_txt_form': change_dflt_txt_form,
            'clients_lst': clients_lst_paginator,
            'dflt_txt': user_dflt_mlng_txt,
            'file_form': UploadFileForm(),
            'exist_tlg_session_file': exist_tlg_session_file,
            'feedback_form': SendFeedbackForm(),
            'whts_auth_status': whts_auth_status,
            'balance': profile_obj.balance,
            'transactions_lst': transactions_lst,
            'reg_bonus': reg_bonus,
            'multi_file_form': MultiplyFileForm(),
        }
        return render(request, 'prepare_to_mailing_2.html', context=context)


class MailingStatView(View):
    """
    Вьюшка для обработки запросов к странице статистики.
    """

    def get(self, request, format=None, page_number=1):
        """
        Обработка GET запроса.
        """
        if request.user.is_anonymous:  # Если пользователь анонимный(незалогинен)
            return redirect(to='/users/login/')  # Редиректим его на страницу логина

        final_lst = []  # Список со всеми необходимыми данными из двух моделей, которые будем отображать на странице
        clients_lst = Clients.objects.filter(user=request.user)
        profile_obj = Profile.objects.get(user=request.user)
        transactions_lst = Transaction.objects.filter(user=request.user)[:3]

        for i_numb, i_client in enumerate(clients_lst):
            i_mlng = Mailings.objects.filter(client=i_client).first()
            if not i_mlng:  # Если рассылок не найдено,то пропускаем и идём дальше
                continue
            # Форматируем дату и время для отображения на странице
            if i_mlng.sent_datetime:
                sent_datetime = i_mlng.sent_datetime + timedelta(hours=3)
                sent_date = sent_datetime.date()
                sent_time = sent_datetime.time()
            else:
                sent_date = '-'
                sent_time = '-'
            if i_mlng.sending_status == 'queued':
                sending_status = 'в очереди'
                status_badge = 'bg-warning'
            elif i_mlng.sending_status == 'cmplt':
                sending_status = 'отправлено'
                status_badge = 'bg-success'
            else:
                sending_status = 'не отправлено'
                status_badge = 'bg-danger'
            # Форматируем статус отправки для отображения на странице
            final_lst.append({  # Итоговый список, в который вкладываем данные для каждой строки таблицы
                'numb': i_numb + 1,
                'client_name': i_client.client_name,
                'contact': i_client.telephone_or_username,
                'mlng_txt': i_mlng.mlng_txt,
                'pmnt_date': i_client.pmnt_date,
                'amount_of_pmnt': i_client.amount_of_pmnt,
                'sent_date': sent_date,
                'sent_time': sent_time,
                'sending_status': sending_status,
                'status_badge': status_badge,
                'send_info': i_mlng.send_info
            })
        paginator = Paginator(object_list=final_lst, per_page=7)  # per_page - кол-во записей на странице
        final_lst_pag = paginator.page(number=page_number)
        context = {
            'clients_lst': final_lst_pag,
            'feedback_form': SendFeedbackForm(),
            'balance': profile_obj.balance,
            'transactions_lst': transactions_lst,
        }
        return render(request, 'mailing_statistic.html', context=context)


def change_dflt_msg_txt(request):
    """
    Вьюшка, которая ловит данные от формы изменения текста типового сообщения пользователя.
    """
    # Код вьюшки удалён из соображений приватности кода проекта
    return redirect(to='/mailing/')


class StartMailingView(View):
    """
    Вьюшка для кнопки старта рассылки.
    """

    def post(self, request, format=None):
        """
        Обработка POST запроса. Достаём всех клиентов данного пользователя и пускаем по ним рассылку.
        """
        if request.user.is_anonymous:  # Если пользователь анонимный(незалогинен)
            return redirect(to='/users/login/')

        # Получаем нужные данные из БД
        user_obj = User.objects.get(id=request.user.id)
        profile_obj = Profile.objects.get(user=user_obj)
        dflt_mlng_txt = profile_obj.dflt_mlng_txt
        clients_lst = Clients.objects.filter(user=user_obj)
        tariff = DyatelSettings.objects.get(key='tariff').value.replace(' ', '').replace(',', '.')

        # Высчитываем сумму для рассылки
        mailing_cost = float(tariff) * len(clients_lst)
        if float(profile_obj.balance) - mailing_cost < 0:   # Если на балансе недостаточно средств
            # Высчитываем сумму пополнения или кол-во лишних клиентов и отдаём страницу с этой инфой
            amount_difference = math.ceil(abs(float(profile_obj.balance) - mailing_cost))
            extra_clients_numb = math.ceil(amount_difference / float(tariff))
            context = {
                'amount_difference': amount_difference,
                'extra_clients_numb': extra_clients_numb,
            }
            return render(request=request, template_name='mailing_not_started.html', context=context)

        # Резервируем средства
        profile_obj.balance = float(profile_obj.balance) - mailing_cost
        profile_obj.reserved_for_mailing = mailing_cost
        profile_obj.save()
        # Записываем транзакцию о резервировании перед рассылкой
        Transaction.objects.create(
            user=user_obj,
            transaction_type='write-off',
            amount=float(mailing_cost),
            description=f'Резервирование средств под рассылку ({mailing_cost} руб.). Тариф за рассылку: {tariff} руб., '
                        f'всего клиентов для рассылки: {len(clients_lst)}'
        )

        for i_client in clients_lst:
            message = dflt_mlng_txt if not i_client.custom_mlng_txt else i_client.custom_mlng_txt
            mailing_obj = Mailings.objects.update_or_create(
                client=i_client,
                defaults={
                    'client': i_client,
                    'mlng_txt': message,
                }
            )
            logger.info(f'Запись о рассылке клиенту {i_client.client_name!r} юзера {request.user!r} '
                        f'{"создана" if mailing_obj[1] else "обновлена"}.')

        # Получаем выбранный мессенджер для рассылки
        mailing_channel = Profile.objects.get(id=request.user.id).mailing_channel

        # запускаем таск Celery
        from .tasks import sending_messages_tlg, sending_messages_whtsp

        if mailing_channel == 'tlg':
            sending_messages_tlg.delay(user_id=request.user.id)
        elif mailing_channel == 'whtsp':
            sending_messages_whtsp.delay(user_id=request.user.id)

        return redirect(to='/statistic/')


class UpdateOrCreateClientView(View):
    """
    Вьюшка для добавления, изменения или удаления клиента.
    """

    def post(self, request, format=None):
        """
        Обработчик POST запроса. Создаём нового клиента в БД или обновляем существующего.
        """

        if request.user.is_anonymous:  # Если пользователь анонимный(незалогинен)
            return redirect(to='/users/login/')

        file_form = MultiplyFileForm(request.POST, request.FILES)
        client_form = UpdateOrCreateClientForm(request.POST)

        if file_form.is_valid() and client_form.is_valid():
            client_id = client_form.cleaned_data.get('client_id')
            client_name = client_form.cleaned_data.get('client_name')
            telephone_or_username = client_form.cleaned_data.get('telephone_or_username')
            # pmnt_date = request.POST.get('pmnt_date')
            pmnt_date = client_form.cleaned_data.get('pmnt_date')
            amount_of_pmnt = client_form.cleaned_data.get('amount_of_pmnt')
            # Если редактируем строку, то параметр mailing_text, если добавляем одного клиента, то dflt_txt
            mailing_text = client_form.cleaned_data.get('mailing_text') if request.POST.get('mailing_text') else request.POST.get(
                'dflt_txt')

            # Обновляем или создаём запись в БД
            this_client = Clients.objects.update_or_create(
                id=None if client_id == '' else client_id,
                defaults={
                    "user": request.user,
                    "client_name": client_name,
                    "telephone_or_username": telephone_or_username,
                    "custom_mlng_txt": mailing_text,
                    "amount_of_pmnt": float(amount_of_pmnt.replace(',', '.')),
                    "pmnt_date": pmnt_date,
                }
            )[0]

            # Удаляем файлы
            files_pks = request.POST.getlist('delete_files')
            del_obj_numbs = ClientsFiles.objects.filter(pk__in=files_pks).delete()
            logger.info(f'Удалено {del_obj_numbs} файлов клиента с ID == {client_id}. Список с ID файлов: {files_pks}')

            # Сохраняем файлы для данного клиента
            for i_file in request.FILES.getlist('new_files'):
                ClientsFiles.objects.create(
                    client=this_client,
                    file=i_file,
                    file_size=i_file.size,
                    file_name=i_file.name
                )
                logger.success(f'Добавлен новый файл для клиента ID == {client_id}')

        return redirect(to='/mailing/#table_with_clients_for_mailing')


class DeleteClientView(View):
    """
    Вьюшка для удаления клиента из БД.
    """

    def post(self, request, format=None):
        """
        Обработка POST запроса для удаления записи клиента из БД.
        """
	# Код вьюшки удалён из соображений приватности кода проекта
        return redirect(to='/mailing/#table_with_clients_for_mailing')


class DownloadClientsFileView(View):
    """
    Вьюшка для скачивания пользователем образца файла с клиентами.
    """

    def get(self, request, file_name, format=None):
        """
        Обработка GET запроса. Скачивание файла - образца.
        """
        file_path = ''.join([f'media/files_examples/', file_name])
        try:
            example_file = open(file_path, 'rb')
        except FileNotFoundError:
            context = {
                'msg_title': 'Файл не найден',
                'msg_text': 'Извините, но файл, который Вы запрашиваете, не найден.'
            }
            return render(request, '404.html', context=context)
        response = FileResponse(example_file)
        response['content-disposition'] = f'attachment; filename="{file_name}"'
        return response


class DownloadMailingFileView(View):
    """
    Вьюшка для скачивания файлов из рассылки.
    """

    def get(self, request, file_name, format=None):
        """
        Скачивание файла.
        """
        file_path = ''.join([f'media/clients_files/', file_name])
        try:
            file_for_download = open(file_path, 'rb')
        except FileNotFoundError:
            context = {
                'msg_title': 'Файл не найден',
                'msg_text': 'Извините, но файл, который Вы запрашиваете, не найден.'
            }
            return render(request, '404.html', context=context)
        response = FileResponse(file_for_download)
        response['content-disposition'] = f'attachment; filename="{quote(file_name)}'
        return response


class DownloadExtension1CView(View):
    """
    Вьюшка для скачивания расширения для 1С.
    """

    def get(self, request, file_name, format=None):
        """
        Обработка GET запроса. Скачивание файла - расширения для 1С.
        """
        file_path = ''.join([f'media/files_examples/', file_name])
        try:
            file = open(file_path, 'rb')
        except FileNotFoundError:
            context = {
                'msg_title': 'Файл не найден',
                'msg_text': 'Извините, но файл, который Вы запрашиваете, не найден.'
            }
            return render(request, '404.html', context=context)
        response = FileResponse(file)
        response['content-disposition'] = f'attachment; filename="{quote(file_name)}"'
        return response


class AgreementFileView(View):
    """
    Вьюшка для обработки запросов, связанных с html файлом договора оферты (скачать файл и загрузить файл).
    """
    def get(self, request):
        """
        GET запрос. Отдаём html файл с договором оферты
        """
	# Код вьюшки удалён из соображений приватности кода проекта
    	return HttpResponse(status=status.HTTP_403_FORBIDDEN, content=content)

    def post(self, request):
        """
        POST - запрос. Загрузка нового html файла с договором оферты.
        """
	# Код вьюшки удалён из соображений приватности кода проекта
    	return HttpResponse(status=status.HTTP_403_FORBIDDEN, content=content)


class UploadFileView(View):
    """
    Вьюшка для загрузки пользователем файла с клиентами.
    """

    def post(self, request, format=None):
        """
        Обработка POST запроса. Получение файла со списком клиентов и обработка его.
        """
        from .tasks import file_processing_with_clients

        file_form = UploadFileForm(request.POST, request.FILES)
        if file_form.is_valid() and file_form.cleaned_data['file']:
            file = file_form.cleaned_data['file'].read()    # Достаём файл из запроса и сразу считываем в байты

            # Если выбрана очистка клиентов и добавление нового списка
            if request.POST.get('todo') == 'clear':
                Clients.objects.filter(user=request.user).delete()  # Удаляем все записи о клиентах

            # Сохраняем файл для последующей обработки
            file_path = os.path.join(MEDIA_ROOT, 'clients_files', f'file_with_clients_{request.user.id}')
            with open(file_path, 'wb') as new_file:
                new_file.write(file)

            # Вызываем задачку celery для обработки файла с клиентами
            file_processing_with_clients.delay(file_path=file_path, user_pk=request.user.id)

            return redirect(to='/mailing/#table_with_clients_for_mailing')
        else:
            return redirect(to='/mailing/')


def feedback_view(request):
    """
    Вьюшка, для записи фидбэков.
    """
    # Код вьюшки удалён из соображений приватности кода проекта	
    return render(request, 'success_feedback.html')


class ClientsFrom1C(APIView):
    """
    Вьюшка для обработки API запросов от 1С. Получение списка клиентов и файлов.
    """

    def post(self, request, format=None):
        """
        Получаем список клиентов и файлы для них.
        Сохраняем всё в БД (старые записи конкретного юзера из таблицы Clients удаляются), файлы сохраняем на диск.
        """

        if request.data.get('api_token') and len(request.data.get('api_token')) == 50:
            # Берём из БД объект юзера
            profile_obj = Profile.objects.filter(api_token_for_1c=request.data.get('api_token'))
            if len(profile_obj) < 1:  # Когда юзер не найден в БД
                return Response({'result': 'user not found'}, status.HTTP_404_NOT_FOUND)

            user_obj = User.objects.get(id=profile_obj[0].user.id)
            # Удаляем все записи из таблицы клиентов для данного юзера
            Clients.objects.filter(user=user_obj).delete()

            # Итерируемся по данным из запроса
            for i_obj in request.data.get('objects'):
                # Создаём запись в таблице Clients
                i_client = Clients.objects.create(
                    user=user_obj,
                    client_name=i_obj.get("Name"),
                    telephone_or_username=f'+7{i_obj.get("Phone")}' if not i_obj.get("Phone").startswith('+7')
                    else i_obj.get("Phone"),
                    amount_of_pmnt=i_obj.get("Sum"),
                    pmnt_date=i_obj.get("Date") if i_obj.get("Date") else datetime.datetime.now(),
                )
                if len(i_obj.get('Files')) > 0:
                    for j_numb, j_file in enumerate(i_obj.get('Files')):
                        # Декодируем файл из base64
                        decoded_file = base64.b64decode(j_file)
                        # Сохраняем файл на диск в формате PDF
                        file_name = f'mailing_doc_{i_client.pk}{j_numb}.pdf'
                        file_path = os.path.join(MEDIA_ROOT, 'clients_files', file_name)
                        with open(file_path, 'wb') as new_file:
                            new_file.write(decoded_file)
                        # Создаём запись в БД
                        ClientsFiles.objects.create(
                            client=i_client,
                            file=file_path,
                            file_size=len(decoded_file) / 8,
                            file_name=file_name
                        )
            return Response({'result': '👌Ok'}, status.HTTP_200_OK)
        else:
            return Response({'result: Токен отсутствует или некорректный.'}, status.HTTP_400_BAD_REQUEST)


def agreement_view(request):
    """
    Вьюшка для отображения договора оферты на странице.
    """
	# Код вьюшки удалён из соображений приватности кода проекта
        return render(request, 'agreement.html', context=context)


def about_us_view(request):
    """
    Вьюшка для странички "О нас".
    """
    # Код вьюшки удалён из соображений приватности кода проекта
    return render(request=request, context=context, template_name='about_us.html')
