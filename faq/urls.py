from django.urls import path
from . import views

urlpatterns = [
    path('faq/add/', views.add_faq_page, name='add_faq'),
    path('faq/add/main-topic/', views.add_main_topic, name='add_main_topic'),
    path('faq/add/sub-topic/', views.add_sub_topic, name='add_sub_topic'),
    path('faq/add/question-answer/', views.add_question_answer, name='add_question_answer'),
    path('detail/<int:pk>/', views.faq_detail, name='faq_detail'),
]