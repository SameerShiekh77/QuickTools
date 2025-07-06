from django.contrib import admin
from .models import PDFTask, UploadedFile

@admin.register(PDFTask)
class PDFTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'task_type', 'status', 'created_at', 'updated_at']
    list_filter = ['task_type', 'status', 'created_at']
    search_fields = ['id', 'user_session']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_name', 'file_size', 'uploaded_at', 'task']
    list_filter = ['uploaded_at', 'task__task_type']
    search_fields = ['original_name', 'task__id']
    readonly_fields = ['id', 'uploaded_at']