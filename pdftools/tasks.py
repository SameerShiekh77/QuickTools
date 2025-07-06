# pdftools/tasks.py (Celery tasks for background processing)
from celery import shared_task
from django.core.files.base import ContentFile
from .models import PDFTask
from .utils import merge_pdfs, convert_pdf_to_word, convert_pdf_to_ppt, password_protect_pdf
import logging
import os

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def process_merge_task(self, task_id, file_paths, file_order):
    """Background task for PDF merging"""
    try:
        task = PDFTask.objects.get(id=task_id)
        task.status = 'processing'
        task.save()
        
        # Reorder files according to user preference
        ordered_files = [file_paths[i] for i in file_order]
        
        # Merge PDFs
        output_path = merge_pdfs(ordered_files, str(task_id))
        
        # Save output file
        with open(output_path, 'rb') as f:
            task.output_file.save(
                f'merged_{task_id}.pdf',
                ContentFile(f.read())
            )
        
        task.status = 'completed'
        task.save()
        
        # Clean up temporary file
        os.remove(output_path)
        
        return {'status': 'success', 'task_id': str(task_id)}
        
    except Exception as e:
        logger.error(f"Merge task failed: {str(e)}")
        task.status = 'failed'
        task.error_message = str(e)
        task.save()
        raise

@shared_task(bind=True)
def process_conversion_task(self, task_id, file_path, conversion_type):
    """Background task for PDF conversion"""
    try:
        task = PDFTask.objects.get(id=task_id)
        task.status = 'processing'
        task.save()
        
        if conversion_type == 'pdf_to_word':
            output_path = convert_pdf_to_word(file_path, str(task_id))
            filename = f'converted_{task_id}.docx'
        elif conversion_type == 'pdf_to_ppt':
            output_path = convert_pdf_to_ppt(file_path, str(task_id))
            filename = f'converted_{task_id}.pptx'
        else:
            raise ValueError(f"Unknown conversion type: {conversion_type}")
        
        # Save output file
        with open(output_path, 'rb') as f:
            task.output_file.save(filename, ContentFile(f.read()))
        
        task.status = 'completed'
        task.save()
        
        # Clean up temporary file
        os.remove(output_path)
        
        return {'status': 'success', 'task_id': str(task_id)}
        
    except Exception as e:
        logger.error(f"Conversion task failed: {str(e)}")
        task.status = 'failed'
        task.error_message = str(e)
        task.save()
        raise

@shared_task(bind=True)
def process_password_protect_task(self, task_id, file_path, password):
    """Background task for PDF password protection"""
    try:
        task = PDFTask.objects.get(id=task_id)
        task.status = 'processing'
        task.save()
        
        # Password protect PDF
        output_path = password_protect_pdf(file_path, password, str(task_id))
        
        # Save output file
        with open(output_path, 'rb') as f:
            task.output_file.save(
                f'protected_{task_id}.pdf',
                ContentFile(f.read())
            )
        
        task.status = 'completed'
        task.save()
        
        # Clean up temporary file
        os.remove(output_path)
        
        return {'status': 'success', 'task_id': str(task_id)}
        
    except Exception as e:
        logger.error(f"Password protection task failed: {str(e)}")
        task.status = 'failed'
        task.error_message = str(e)
        task.save()
        raise