from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

class CustomUser(AbstractUser):
    first_name = models.CharField(
        'Имя',
        max_length=settings.CONST_LENGTH
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=settings.CONST_LENGTH
    )
    email = models.EmailField(
        'Email',
        unique=True,
        max_length=settings.CONST_LENGTH
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=('username', 'email'),
                name='unique_user'
            )
        ]

    def clean(self):
        if self.username == 'me':
            raise ValidationError(
                {'error': 'Невозможно создать пользователя с именем me'}
            )

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        CustomUser,
        related_name='followers',
        verbose_name='Подписчик',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        CustomUser,
        related_name='followings',
        verbose_name='Автор',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'],
                name='unique_follower'
            )
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError(
                {'error': 'Нельзя подписаться на себя'}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'Автор: {self.author}, подписчик: {self.user}'
