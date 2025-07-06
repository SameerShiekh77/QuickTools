from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from pdftools.models import PDFTask, UploadedFile
import os

class Command(BaseCommand):
    help = 'Clean up old PDF files and tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to keep files (default: 7)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Get old tasks
        old_tasks = PDFTask.objects.all()
        deleted_count = 0
        
        for task in old_tasks:
            # Delete associated files
            for uploaded_file in task.uploaded_files.all():
                if uploaded_file.file and os.path.exists(uploaded_file.file.path):
                    try:
                        os.remove(uploaded_file.file.path)
                        deleted_count += 1
                    except OSError:
                        pass
            
            # Delete output file
            if task.output_file and os.path.exists(task.output_file.path):
                try:
                    os.remove(task.output_file.path)
                    deleted_count += 1
                except OSError:
                    pass
        
        # Delete task records
        tasks_deleted = old_tasks.count()
        old_tasks.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {tasks_deleted} tasks and {deleted_count} files older than {days} days'
            )
        )