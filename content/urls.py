from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sections/', views.home, name='sections'),
    path('section/<slug:slug>/', views.section_detail, name='section_detail'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<slug:post_slug>/edit/', views.create_revision, name='create_revision'),
    path('revision/<int:revision_id>/make-current/', views.make_revision_current, name='make_revision_current'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('post/<slug:slug>/publish/', views.publish_post, name='publish_post'),
    path('post/<slug:slug>/archive/', views.archive_post, name='archive_post'),
    path('post/create/', views.create_post, name='create_post'),


]
