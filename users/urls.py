from django.urls import path
from users.views import login_view, logout_view, TelegramAuthGetPhone, TelegramAuthGetCode, TelegramTwoFactorAuth, \
    RegistrationView, AccountView, disable_telegram_account, ChangePasswordView, ConnectWhatsAppView, \
    disable_whatsapp_account, choose_mailing_channel_view, WalletView, service_in_dev_view, test_view, \
    ReplenishmentBalanceView

app_name = 'app_users'

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('input_tlg_phone/', TelegramAuthGetPhone.as_view(), name='input_tlg_phone'),
    path('input_tlg_code/', TelegramAuthGetCode.as_view(), name='input_tlg_code'),
    path('input_2fa_pass/', TelegramTwoFactorAuth.as_view(), name='input_2fa_pass'),
    path('disable_tlg_acc/', disable_telegram_account, name='disable_tlg_acc'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('account/', AccountView.as_view(), name='account'),
    path('change_pass/', ChangePasswordView.as_view(), name='change_pass'),
    path('connect_whatsapp/', ConnectWhatsAppView.as_view(), name='connect_whatsapp'),
    path('disable_whts_acc/', disable_whatsapp_account, name='disable_whts_acc'),
    path('choose_mailing_channel/', choose_mailing_channel_view, name='choose_mailing_channel'),
    path('wallet/', WalletView.as_view(), name='wallet'),
    path('wallet/<int:page_numb>', WalletView.as_view(), name='wallet_pagination'),
    path('replenish_balance/', ReplenishmentBalanceView.as_view(), name='replenish_balance'),

    path('test/', test_view, name='test'),
]
