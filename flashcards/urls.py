from django.urls import path
from . import views

urlpatterns = [
    # Decks
    path('', views.deck_list, name='deck_list'),
    path('deck/create/', views.deck_create, name='deck_create'),
    path('deck/<int:pk>/', views.deck_detail, name='deck_detail'),
    path('deck/<int:pk>/edit/', views.deck_edit, name='deck_edit'),
    path('deck/<int:pk>/delete/', views.deck_delete, name='deck_delete'),
    path('deck/<int:pk>/reset/', views.deck_reset, name='deck_reset'),

    # Cards
    path('deck/<int:deck_pk>/card/create/', views.card_create, name='card_create'),
    path('deck/<int:deck_pk>/import/', views.csv_import, name='csv_import'),
    path('card/<int:pk>/edit/', views.card_edit, name='card_edit'),
    path('card/<int:pk>/delete/', views.card_delete, name='card_delete'),

    # Study
    path('deck/<int:deck_pk>/study/', views.study_session_start, name='study_session_start'),
    path('session/<int:session_pk>/', views.study_session, name='study_session'),
    path('session/<int:session_pk>/answer/', views.card_answer, name='card_answer'),
    path('session/<int:session_pk>/summary/', views.session_summary, name='session_summary'),
]