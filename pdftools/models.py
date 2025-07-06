from django.db import models
from django.contrib.auth.models import User
import uuid
import os

class PDFTask(models.Model):
    TASK_TYPES = [
        ('merge', 'Merge PDFs'),
        ('pdf_to_word', 'PDF to Word'),
        ('pdf_to_ppt', 'PDF to PowerPoint'),
        ('password_protect', 'Password Protect'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_session = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Input files
    input_files = models.JSONField(default=list)  # Store file paths
    
    # Output file
    output_file = models.FileField(upload_to='processed/', blank=True, null=True)
    
    # Task-specific parameters
    password = models.CharField(max_length=255, blank=True, null=True)
    merge_order = models.JSONField(default=list)
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.status}"

class UploadedFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='uploads/')
    original_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey(PDFTask, on_delete=models.CASCADE, related_name='uploaded_files')
    
    def __str__(self):
        return self.original_name