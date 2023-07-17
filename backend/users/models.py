from django.contrib.auth.models import AbstractUser
from django.db.models import (CASCADE, CharField, EmailField, ForeignKey,
                              Model, UniqueConstraint)
from rest_framework.exceptions import ValidationError


class CustomUser(AbstractUser):

    first_name = CharField(
        'Имя',
        max_length=200
    )
    last_name = CharField(
        'Фамилия',
        max_length=200
    )
    email = EmailField(
        'Email',
        unique=True,
        max_length=200
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            UniqueConstraint(
                fields=('username', 'email'),
                name='unique_user'
            )
        ]

    def clean(self):
        if self.username == 'me':
            raise ValidationError(
                {'error': 'Невозможно создать пользователя с именем me'}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Follow(Model):
    user = ForeignKey(
        CustomUser,
        related_name='followers',
        verbose_name='Подписчик',
        on_delete=CASCADE
    )
    author = ForeignKey(
        CustomUser,
        related_name='followings',
        verbose_name='Автор',
        on_delete=CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(
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
