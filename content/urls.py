from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('main/', views.main, name='main'),
    path("search/", views.search, name="search"),
    path("api/search/", views.search_api, name="search_api"),
    path("profile/confirm/<str:token>/", views.confirm_email, name="confirm_email"),



    # --- Catalog ---
    path("catalog/sinyi/", views.catalog_sinyi, name="catalog_sinyi"),
    path("catalog/taiji/", views.catalog_taiji, name="catalog_taiji"),
    path("profile/", views.profile, name="profile"),

    # --- API ---
    path("api/sections/", views.section_search_api, name="section_search_api"),
    path("api/sections/tree/", views.section_tree_page_api, name="section_tree_api"),

    # --- Sections ---
    path('sections/', views.section_tree, name='sections'),

    path('section/create/', views.create_section, name='create_section'),
    path("section/<slug:slug>/edit/", views.edit_section, name="edit_section"),
    path("sections/manage/", views.section_list, name="section_list"),
    path("section/<slug:slug>/delete/", views.delete_section, name="delete_section"),
    path('section/<slug:slug>/', views.section_detail, name='section_detail'),

    # --- Bookmark ---
    path("bookmark/<slug:slug>/toggle/", views.toggle_bookmark, name="toggle_bookmark"),
    path("bookmarks/", views.my_bookmarks, name="my_bookmarks"),

    # --- Posts ---
    path('post/create/', views.create_post, name='create_post'),
    path("editor/upload-image/", views.upload_editor_image, name="upload_editor_image"),
    path('post/<slug:post_slug>/edit/', views.edit_post, name='edit_post'),
    path('post/<slug:slug>/publish/', views.publish_post, name='publish_post'),
    path('post/<slug:slug>/archive/', views.archive_post, name='archive_post'),
    path('post/<slug:slug>/delete/', views.delete_post, name='delete_post'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),

    # --- Dashboard ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path("dashboard/archive/", views.archived_posts, name="archived_posts"),
]
