from django.contrib.admin import ModelAdmin, TabularInline, site

from .models import (FavoriteRecipe, Ingredient, IngredientsAmount, Recipe,
                     ShoppingCart, Tag)


class IngredientsAmountInline(TabularInline):
    model = IngredientsAmount
    extra = 1


class RecipeAdmin(ModelAdmin):
    list_display = ('name', 'author', 'display_tags')
    list_filter = ('name', 'author', 'tags')
    search_fields = ('name', 'author__username', 'author__last_name',
                     'author__first_name', 'tags__name')
    readonly_fields = ('favorite_count', 'shopping_count')
    filter_vertical = ('tags', 'ingredients')
    inlines = (IngredientsAmountInline,)

    def favorite_count(self, obj):
        return obj.favorites.count()

    def shopping_count(self, obj):
        return obj.shopcarts.count()

    def display_tags(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])

    favorite_count.short_description = 'В избранном'
    shopping_count.short_description = 'В списке покупок'
    display_tags.short_description = 'Теги'


class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class IngredientsAmountAdmin(ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


site.register(Recipe, RecipeAdmin)
site.register(Ingredient, IngredientAdmin)
site.register(IngredientsAmount, IngredientsAmountAdmin)
site.register(Tag)
site.register(FavoriteRecipe)
site.register(ShoppingCart)
