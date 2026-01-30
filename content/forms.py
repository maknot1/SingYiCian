from django import forms
from .models import PostRevision, Post

class PostRevisionForm(forms.ModelForm):
    class Meta:
        model = PostRevision
        fields = ['content', 'note']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 15,
                'placeholder': 'Введите текст статьи...'
            }),
            'note': forms.TextInput(attrs={
                'placeholder': 'Кратко: что изменилось'
            }),
        }

class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['section', 'title', 'slug', 'status', 'is_featured', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Заголовок'}),
            'slug': forms.TextInput(attrs={'placeholder': 'url-slug'}),
        }