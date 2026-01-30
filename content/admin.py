from django.contrib import admin
from django.utils.html import format_html

from .models import Section, Tag, Post, PostImage, PostRevision


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'slug')
    list_editable = ('order',)
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 0


class PostRevisionInline(admin.TabularInline):
    model = PostRevision
    extra = 0
    fields = ('created_at', 'created_by', 'note', 'is_published_snapshot')
    readonly_fields = ('created_at', 'created_by', 'is_published_snapshot')
    can_delete = False
    show_change_link = True


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'status', 'is_featured', 'published_at', 'updated_at')
    list_filter = ('status', 'section', 'is_featured', 'tags')
    search_fields = ('title', 'summary')
    list_editable = ('status', 'is_featured')
    autocomplete_fields = ('tags',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PostImageInline, PostRevisionInline]
    date_hierarchy = 'published_at'

    fieldsets = (
        (None, {
            'fields': ('section', 'title', 'slug', 'author')
        }),
        ('Кратко и медиа', {
            'fields': ('summary', 'cover_image', 'tags')
        }),
        ('Публикация', {
            'fields': ('status', 'published_at', 'is_featured', 'order')
        }),
    )

    def save_model(self, request, obj: Post, form, change):
        if not obj.author:
            obj.author = request.user

        # если статус published - проставим дату, если пусто
        if obj.status == Post.Status.PUBLISHED and not obj.published_at:
            obj.published_at = obj.published_at  # сигнал проставит при необходимости

        super().save_model(request, obj, form, change)


@admin.register(PostRevision)
class PostRevisionAdmin(admin.ModelAdmin):
    list_display = ('post', 'created_at', 'created_by', 'note', 'is_published_snapshot')
    list_filter = ('is_published_snapshot', 'created_at')
    search_fields = ('post__title', 'note', 'content')
    readonly_fields = ('created_at',)

    def has_add_permission(self, request):
        # добавление ревизий будем делать позже через отдельный UI, пока пусть будет только чтение
        return False


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ('post', 'title', 'order', 'preview')
    list_filter = ('post',)
    search_fields = ('post__title', 'title', 'alt_text')
    list_editable = ('order',)

    def preview(self, obj: PostImage):
        if not obj.image:
            return "-"
        return format_html('<img src="{}" style="height:40px" />', obj.image.url)
