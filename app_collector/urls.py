from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from app_collector.views import MailingStatView, PrepareToMailingView, change_dflt_msg_txt, StartMailingView, \
    UpdateOrCreateClientView, DeleteClientView, DownloadClientsFileView, UploadFileView, feedback_view, \
    ClientsFrom1C, DownloadMailingFileView, DownloadExtension1CView, agreement_view, AgreementFileView, about_us_view

app_name = 'app_collector'

urlpatterns = [
    path('mailing/', PrepareToMailingView.as_view(), name='mailing'),
    # TODO: поменять потом во всём коде переход на корень, а не mailing/
    path('', PrepareToMailingView.as_view(), name='mailing'),
    path('mlng_lst_page/<int:page_number>/', PrepareToMailingView.as_view(), name='mlng_lst_page'),
    path('statistic/', MailingStatView.as_view(), name='statistic'),
    path('stat_lst_page/<int:page_number>/', MailingStatView.as_view(), name='stat_lst_page'),
    path('change_dflt_txt/', change_dflt_msg_txt, name='change_dflt_txt'),
    path('start_mlng/', StartMailingView.as_view(), name='start_mlng'),
    path('upd_or_crt_client/', UpdateOrCreateClientView.as_view(), name='upd_or_crt_client'),
    path('dlt_client/', DeleteClientView.as_view(), name='dlt_client'),
    path('dwnld_clients_lst_example/<str:file_name>/', DownloadClientsFileView.as_view(), name='dwnld_clients_lst_example'),
    path('dwnld_clients_file/<str:file_name>/', DownloadMailingFileView.as_view(), name='dwnld_clients_file'),
    path('dwnld_1c_extension/<str:file_name>/', DownloadExtension1CView.as_view(), name='dwnld_1c_extension'),
    path('upload_clients_lst_file/', UploadFileView.as_view(), name='upload_clients_lst_file'),
    path('feedback/', feedback_view, name='feedback'),
    path('clients_1c/', ClientsFrom1C.as_view(), name='clients_1c'),
    path('agreement/', agreement_view, name='agreement'),
    path('agreement_file/', AgreementFileView.as_view(), name='agreement_file'),
    path('about_us/', about_us_view, name='about_us'),
]

if settings.DEBUG:  # Для обработки статики и медиа во время разработки
    urlpatterns.extend(
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    )
    urlpatterns.extend(
        static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    )
