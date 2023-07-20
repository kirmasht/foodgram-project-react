from django.utils import timezone
from django.db.models import F, Sum
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as djoser_UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from recipes.models import Ingredient, IngredientsAmount, Recipe, Tag
from users.models import Follow

from .filters import RecipeFilter
from .paginations import LimitPagination
from .permissions import AuthorStaffOrReadOnly
from .serializers import (CustomUserSerializer, FavoriteRecipeSerializer,
                          FollowSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeListSerializer,
                          ShoppingCartSerializer, TagSerializer)
from .mixins import CreateRetrievListPatchDestroyViewSet

CustomUser = get_user_model()

class UsersViewSet(djoser_UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]

    @action(methods=['GET'], detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        user = self.request.user
        authors = CustomUser.objects.filter(followings__user=user)
        page = self.paginate_queryset(authors)
        serializer = FollowSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, id):
        user = self.request.user
        author = get_object_or_404(CustomUser, id=id)
        subscription = Follow.objects.filter(user=user, author=author)

        if request.method == 'POST':
            if subscription.exists():
                return Response(
                    {'error': 'Вы подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FollowSerializer(author, context={'request': request})
            Follow.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not subscription.exists():
                return Response(
                    {'error': 'Вы не подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(CreateRetrievListPatchDestroyViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [AuthorStaffOrReadOnly]
    pagination_class = LimitPagination

    def get_serializer_class(self):
        if self.action in permissions.SAFE_METHODS:
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def action_post_delete(self, pk, serializer_class):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        model_obj = serializer_class.Meta.model.objects.filter(
            user=user, recipe=recipe
        )

        if self.request.method == 'POST':
            serializer = serializer_class(
                data={'user': user.id, 'recipe': pk},
                context={'request': self.request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            if not model_obj.exists():
                return Response({'error': 'Рецепта нет в избранном.'},
                                status=status.HTTP_400_BAD_REQUEST)
        model_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        return self.action_post_delete(pk, FavoriteRecipeSerializer)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self.action_post_delete(pk, ShoppingCartSerializer)

    @action(methods=['GET'], detail=False,
            permission_classes=[permissions.IsAuthenticated], pagination_class=None)
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopcarts.exists():
            return Response({'error': 'Список покупок пуст'},
                            status=status.HTTP_204_NO_CONTENT)
        ingredients = IngredientsAmount.objects.filter(
            recipe__shopcarts__user=user
        ).values(
            ingredients=F('ingredient__name'),
            measure=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount'))

        filename = f'{user.username}_shopping_list.txt'
        shopping_list = (f'Список покупок\n\n{user.username}\n'
                         f'{timezone.now().strftime("%d/%m/%Y %H:%M")}\n\n')
        for ing in ingredients:
            shopping_list += (
                f'{ing["ingredients"]} - {ing["amount"]}, {ing["measure"]}\n'
            )
        response = HttpResponse(shopping_list,
                                content_type='text.txt; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
