from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    pseudonym = models.CharField(max_length=24, unique=True)
    bio = models.CharField(max_length=160, blank=True)
    avatar = models.ImageField(upload_to='avatars/%Y/%m/', blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True,
                                   validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True,
                                    validators=[MinValueValidator(-180), MaxValueValidator(180)])
    location_updated = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f'@{self.pseudonym}'


class Friendship(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        ACCEPTED = 'accepted', 'Принята'

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friendships')
    addressee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friendships')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['requester', 'addressee'], name='unique_friendship')]
        ordering = ['-created_at']


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    body = models.TextField(max_length=1000)
    image = models.ImageField(upload_to='posts/%Y/%m/', blank=True, null=True)
    video = models.FileField(upload_to='posts/videos/%Y/%m/', blank=True, null=True)
    tags = models.CharField(max_length=180, blank=True, help_text='Теги через пробел, например #новости #район')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Support(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='supports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supports')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['post', 'user'], name='unique_post_support')]


class ContactMessage(models.Model):
    pseudonym = models.CharField(max_length=24, blank=True)
    message = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']


class SharedLocation(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_locations')
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']


class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField(max_length=2000, blank=True)
    sticker = models.CharField(max_length=16, blank=True)
    image = models.ImageField(upload_to='messages/images/%Y/%m/', blank=True, null=True)
    video = models.FileField(upload_to='messages/videos/%Y/%m/', blank=True, null=True)
    audio = models.FileField(upload_to='messages/audio/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
