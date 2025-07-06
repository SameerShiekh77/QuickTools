from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('pdftools/', views.index, name='index'),
    path('upload/', views.upload_files, name='upload_files'),
    path('merge/', views.process_merge, name='process_merge'),
    path('pdf-to-word/', views.process_pdf_to_word, name='process_pdf_to_word'),
    path('pdf-to-ppt/', views.process_pdf_to_ppt, name='process_pdf_to_ppt'),
    path('password-protect/', views.process_password_protect, name='process_password_protect'),
    path('task/<uuid:task_id>/status/', views.task_status, name='task_status'),
    path('download/<uuid:task_id>/', views.download_file, name='download_file'),
]   