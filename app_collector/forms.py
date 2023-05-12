from django import forms

from app_collector.models import ClientsFiles


class DfltMsgForm(forms.Form):
    """
    Форма для изменения текста типового сообщения.
    """

    dflt_txt = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "id": "popupMessage",
            "placeholder": "Текст типового сообщения",
            "maxlength": "500",
            "style": "height:80px;",
            "rows": "3",
            "required": "required",
        }),
        label='Текст рассылки'
    )

    def __init__(self, user=None, *args, **kwargs):
        """
        Переопределяем метод конструктора, так как нам нужно добавить текст по умолчанию в тэг <textarea>,
        а он лежит в этой форме. За него отвечает параметр initial у forms.Textarea().
        Мы принимаем в конструктор объект пользователя(его получаем во вьюхе), из него уже и достаём дефолтный текст.
        """
        super().__init__(*args, **kwargs)
        # Set the default text based on user data
        if user:
            profile = user.profile
            self.fields['dflt_txt'].initial = profile.dflt_mlng_txt


class UploadFileForm(forms.Form):
    """
    Форма для загрузки файла со списком клиентов.
    """
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            "class": "form-control",
            "required": "required",
        }),
        required=False
    )


class SendFeedbackForm(forms.Form):
    """
    Форма для отправки обратной связи ("Напишите нам").
    """
    feedback_text = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={
        "style": "height: 200px",
        "class": "form-control",
        "id": "text-read-us",
    }))


class UpdateOrCreateClientForm(forms.Form):
    # TODO: эту форму надо доделать и подставить во вьюшку UpdateOrCreateClientView
    """
    Форма для обновления или добавления нового клиента.
    """
    client_id = forms.IntegerField(max_value=99999, required=False)
    client_name = forms.CharField(max_length=100)
    telephone_or_username = forms.CharField(max_length=100)
    pmnt_date = forms.DateTimeField()
    amount_of_pmnt = forms.CharField(max_length=20)
    mailing_text = forms.CharField(max_length=500, required=False)
    dflt_txt = forms.CharField(max_length=500, required=False)


class MultiplyFileForm(forms.Form):
    """
    Форма для загрузки нескольких файлов.
    """
    new_files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            "multiple": True,
            "class": "form-control",
        }),
        label='Добавить новые файлы',
        required=False,
    )
