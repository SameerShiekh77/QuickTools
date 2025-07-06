from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import os
import uuid
from .models import PDFTask, UploadedFile
from pdftools.utils import (
    merge_pdfs, 
    convert_pdf_to_word, 
    convert_pdf_to_ppt, 
    password_protect_pdf,
    validate_pdf_file
)

def index(request):
    """Main page with PDF tools interface"""
    return render(request, 'pdftools/index.html')

@csrf_exempt
@require_http_methods(["POST"])
def upload_files(request):
    """Handle file uploads for all PDF operations"""
    try:
        task_type = request.POST.get('task_type')
        if not task_type:
            return JsonResponse({'error': 'Task type is required'}, status=400)
        
        # Create new task
        task = PDFTask.objects.create(
            task_type=task_type,
            user_session=request.session.session_key or str(uuid.uuid4())
        )
        
        uploaded_files = []
        files = request.FILES.getlist('files')
        
        if not files:
            return JsonResponse({'error': 'No files uploaded'}, status=400)
        
        # Validate file limit based on task type
        if task_type == 'merge' and len(files) < 2:
            return JsonResponse({'error': 'At least 2 files required for merging'}, status=400)
        elif task_type in ['pdf_to_word', 'pdf_to_ppt', 'password_protect'] and len(files) != 1:
            return JsonResponse({'error': 'Only one file allowed for this operation'}, status=400)
        
        for file in files:
            # Validate PDF file
            if not validate_pdf_file(file):
                return JsonResponse({'error': f'Invalid PDF file: {file.name}'}, status=400)
            
            # Save uploaded file
            uploaded_file = UploadedFile.objects.create(
                file=file,
                original_name=file.name,
                file_size=file.size,
                task=task
            )
            uploaded_files.append({
                'id': str(uploaded_file.id),
                'name': uploaded_file.original_name,
                'size': uploaded_file.file_size
            })
        
        return JsonResponse({
            'task_id': str(task.id),
            'files': uploaded_files,
            'message': 'Files uploaded successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def process_merge(request):
    """Process PDF merge operation"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        file_order = data.get('file_order', [])
        
        task = get_object_or_404(PDFTask, id=task_id, task_type='merge')
        task.status = 'processing'
        task.merge_order = file_order
        task.save()
        
        # Get uploaded files in specified order
        input_files = []
        for file_id in file_order:
            uploaded_file = get_object_or_404(UploadedFile, id=file_id, task=task)
            input_files.append(uploaded_file.file.path)
        
        # Merge PDFs
        output_path = merge_pdfs(input_files, str(task.id))
        
        # Save output file
        with open(output_path, 'rb') as f:
            task.output_file.save(
                f'merged_{task.id}.pdf',
                ContentFile(f.read())
            )
        
        task.status = 'completed'
        task.save()
        
        # Clean up temporary file
        os.remove(output_path)
        
        return JsonResponse({
            'task_id': str(task.id),
            'download_url': task.output_file.url,
            'message': 'PDFs merged successfully'
        })
        
    except Exception as e:
        if 'task' in locals():
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def process_pdf_to_word(request):
    """Convert PDF to Word document with image preservation"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        
        task = get_object_or_404(PDFTask, id=task_id, task_type='pdf_to_word')
        task.status = 'processing'
        task.save()
        
        # Get uploaded file
        uploaded_file = task.uploaded_files.first()
        if not uploaded_file:
            raise ValueError("No file found for conversion")
        
        # Convert PDF to Word
        output_path = convert_pdf_to_word(uploaded_file.file.path, str(task.id))
        
        # Save output file
        with open(output_path, 'rb') as f:
            task.output_file.save(
                f'converted_{task.id}.docx',
                ContentFile(f.read())
            )
        
        task.status = 'completed'
        task.save()
        
        # Clean up temporary file
        os.remove(output_path)
        
        return JsonResponse({
            'task_id': str(task.id),
            'download_url': task.output_file.url,
            'message': 'PDF converted to Word successfully'
        })
        
    except Exception as e:
        if 'task' in locals():
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def process_pdf_to_ppt(request):
    """Convert PDF to PowerPoint presentation with image preservation"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        
        task = get_object_or_404(PDFTask, id=task_id, task_type='pdf_to_ppt')
        task.status = 'processing'
        task.save()
        
        # Get uploaded file
        uploaded_file = task.uploaded_files.first()
        if not uploaded_file:
            raise ValueError("No file found for conversion")
        
        # Convert PDF to PowerPoint
        output_path = convert_pdf_to_ppt(uploaded_file.file.path, str(task.id))
        
        # Save output file
        with open(output_path, 'rb') as f:
            task.output_file.save(
                f'converted_{task.id}.pptx',
                ContentFile(f.read())
            )
        
        task.status = 'completed'
        task.save()
        
        # Clean up temporary file
        os.remove(output_path)
        
        return JsonResponse({
            'task_id': str(task.id),
            'download_url': task.output_file.url,
            'message': 'PDF converted to PowerPoint successfully'
        })
        
    except Exception as e:
        if 'task' in locals():
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def process_password_protect(request):
    """Add password protection to PDF"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        password = data.get('password')
        
        if not password:
            return JsonResponse({'error': 'Password is required'}, status=400)
        
        task = get_object_or_404(PDFTask, id=task_id, task_type='password_protect')
        task.status = 'processing'
        task.password = password
        task.save()
        
        # Get uploaded file
        uploaded_file = task.uploaded_files.first()
        if not uploaded_file:
            raise ValueError("No file found for protection")
        
        # Password protect PDF
        output_path = password_protect_pdf(uploaded_file.file.path, password, str(task.id))
        
        # Save output file
        with open(output_path, 'rb') as f:
            task.output_file.save(
                f'protected_{task.id}.pdf',
                ContentFile(f.read())
            )
        
        task.status = 'completed'
        task.save()
        
        # Clean up temporary file
        os.remove(output_path)
        
        return JsonResponse({
            'task_id': str(task.id),
            'download_url': task.output_file.url,
            'message': 'PDF password protected successfully'
        })
        
    except Exception as e:
        if 'task' in locals():
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def task_status(request, task_id):
    """Get task status and progress"""
    try:
        task = get_object_or_404(PDFTask, id=task_id)
        
        response_data = {
            'task_id': str(task.id),
            'status': task.status,
            'task_type': task.task_type,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
        }
        
        if task.status == 'completed' and task.output_file:
            response_data['download_url'] = task.output_file.url
        
        if task.status == 'failed' and task.error_message:
            response_data['error'] = task.error_message
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def download_file(request, task_id):
    """Download processed file"""
    try:
        task = get_object_or_404(PDFTask, id=task_id, status='completed')
        
        if not task.output_file:
            raise Http404("No output file available")
        
        response = HttpResponse(
            task.output_file.read(),
            content_type='application/octet-stream'
        )
        
        # Set filename based on task type
        filename_map = {
            'merge': 'merged_document.pdf',
            'pdf_to_word': 'converted_document.docx',
            'pdf_to_ppt': 'converted_presentation.pptx',
            'password_protect': 'protected_document.pdf',
        }
        
        filename = filename_map.get(task.task_type, 'processed_file')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)