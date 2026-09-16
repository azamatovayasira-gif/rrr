from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import ContactMessage, Post, Profile


class SignUpForm(forms.Form):
    pseudonym = forms.CharField(max_length=24, min_length=3, label='Псевдоним')
    password = forms.CharField(min_length=8, widget=forms.PasswordInput, label='Пароль')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Повторите пароль')

    def clean_pseudonym(self):
        pseudonym = self.cleaned_data['pseudonym'].strip().lower()
        if not pseudonym.replace('_', '').isalnum():
            raise ValidationError('Используйте только буквы, цифры и символ _.')
        if Profile.objects.filter(pseudonym__iexact=pseudonym).exists():
            raise ValidationError('Этот псевдоним уже занят.')
        return pseudonym

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') and cleaned.get('password') != cleaned.get('password_confirm'):
            raise ValidationError('Пароли не совпадают.')
        return cleaned


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('body', 'image', 'video', 'tags')
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Что происходит рядом?'}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*', 'class': 'post-image-input'}),
            'video': forms.ClearableFileInput(attrs={'accept': 'video/*', 'class': 'post-video-input'}),
            'tags': forms.TextInput(attrs={'placeholder': '#теги'}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and image.size > 8 * 1024 * 1024:
            raise ValidationError('Изображение должно быть меньше 8 МБ.')
        return image

    def clean_video(self):
        video = self.cleaned_data.get('video')
        if video and video.size > 50 * 1024 * 1024:
            raise ValidationError('Видео должно быть меньше 50 МБ.')
        if video and not video.content_type.startswith('video/'):
            raise ValidationError('Можно загружать только видеофайлы.')
        return video

    def clean_tags(self):
        tags = self.cleaned_data['tags'].strip()
        return ' '.join(tag if tag.startswith('#') else f'#{tag}' for tag in tags.split())


class FriendLookupForm(forms.Form):
    pseudonym = forms.CharField(max_length=24, label='Анонимный ID', widget=forms.TextInput(attrs={'placeholder': '@psevdonim'}))


class LocationForm(forms.Form):
    friend_id = forms.IntegerField(widget=forms.HiddenInput)
    latitude = forms.DecimalField(min_value=-90, max_value=90, max_digits=9, decimal_places=6, widget=forms.HiddenInput)
    longitude = forms.DecimalField(min_value=-180, max_value=180, max_digits=9, decimal_places=6, widget=forms.HiddenInput)


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Псевдоним')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def clean_username(self):
        return self.cleaned_data['username'].strip().lstrip('@').lower()


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('message',)
        labels = {'message': 'Сообщение'}
        widgets = {'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Опиши вопрос или проблему'})}


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('pseudonym', 'bio', 'avatar')
        widgets = {
            'pseudonym': forms.TextInput(attrs={'placeholder': 'Новый псевдоним'}),
            'bio': forms.TextInput(attrs={'placeholder': 'Коротко о себе'}),
            'avatar': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def clean_pseudonym(self):
        pseudonym = self.cleaned_data['pseudonym'].strip().lower()
        if not pseudonym.replace('_', '').isalnum():
            raise ValidationError('Используйте только буквы, цифры и символ _.')
        if Profile.objects.filter(pseudonym__iexact=pseudonym).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Этот псевдоним уже занят.')
        return pseudonym


class SwitchAccountForm(forms.Form):
    pseudonym = forms.CharField(label='Псевдоним')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def clean_pseudonym(self):
        return self.cleaned_data['pseudonym'].strip().lstrip('@').lower()


class MessageForm(forms.Form):
    text = forms.CharField(max_length=2000, required=False, widget=forms.TextInput(attrs={'placeholder': 'Напиши сообщение...'}))
    sticker = forms.CharField(max_length=16, required=False, widget=forms.HiddenInput)
    image = forms.ImageField(required=False)
    video = forms.FileField(required=False)
    audio = forms.FileField(required=False)

    def clean(self):
        cleaned = super().clean()
        if not any(cleaned.get(field) for field in ('text', 'sticker', 'image', 'video', 'audio')):
            raise ValidationError('Добавь текст, emoji или файл.')
        for field, limit in (('image', 8), ('video', 50), ('audio', 20)):
            upload = cleaned.get(field)
            if upload and upload.size > limit * 1024 * 1024:
                self.add_error(field, f'Файл должен быть меньше {limit} МБ.')
        return cleaned
