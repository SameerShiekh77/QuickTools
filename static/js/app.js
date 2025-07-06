// static/js/app.js
class PDFPowerKit {
    constructor() {
        this.currentTask = null;
        this.uploadedFiles = {};
        this.init();
    }

    init() {
        this.setupTabs();
        this.setupFileUploads();
        this.setupProcessButtons();
        this.setupDragAndDrop();
    }

    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabId = button.getAttribute('data-tab');
                
                // Update button states
                tabButtons.forEach(btn => {
                    btn.classList.remove('active', 'text-blue-600', 'bg-blue-50');
                    btn.classList.add('text-gray-600');
                });
                button.classList.add('active', 'text-blue-600', 'bg-blue-50');
                button.classList.remove('text-gray-600');

                // Update tab content
                tabContents.forEach(content => {
                    content.classList.remove('active');
                });
                document.getElementById(`${tabId}-tab`).classList.add('active');

                // Reset current tab state
                this.resetTabState(tabId);
            });
        });
    }

    setupFileUploads() {
        // Merge files
        document.getElementById('merge-file-input').addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files, 'merge');
        });

        // Single file uploads
        ['word', 'ppt', 'protect'].forEach(type => {
            document.getElementById(`${type}-file-input`).addEventListener('change', (e) => {
                this.handleFileSelection(e.target.files, type);
            });
        });
    }

    setupDragAndDrop() {
        ['merge', 'word', 'ppt', 'protect'].forEach(type => {
            const dropZone = document.getElementById(`${type}-drop-zone`);
            
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('drag-over');
            });

            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
                this.handleFileSelection(e.dataTransfer.files, type);
            });
        });
    }

    setupProcessButtons() {
        // Merge process
        document.getElementById('merge-process-btn').addEventListener('click', () => {
            this.processMerge();
        });

        // Convert processes
        document.getElementById('word-process-btn').addEventListener('click', () => {
            this.processConversion('pdf-to-word');
        });

        document.getElementById('ppt-process-btn').addEventListener('click', () => {
            this.processConversion('pdf-to-ppt');
        });

        // Password protect
        document.getElementById('protect-process-btn').addEventListener('click', () => {
            this.processPasswordProtect();
        });
    }

    async handleFileSelection(files, type) {
        if (!files || files.length === 0) return;

        // Validate file count
        if (type === 'merge' && files.length < 2) {
            showToast('Please select at least 2 PDF files for merging', 'error');
            return;
        }

        if (type !== 'merge' && files.length > 1) {
            showToast('Please select only one PDF file', 'error');
            return;
        }

        // Validate file types
        for (let file of files) {
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                showToast('Please select only PDF files', 'error');
                return;
            }
            if (file.size > 50 * 1024 * 1024) { // 50MB limit
                showToast('File size must be less than 50MB', 'error');
                return;
            }
        }

        try {
            const taskType = type === 'word' ? 'pdf_to_word' : 
                           type === 'ppt' ? 'pdf_to_ppt' : 
                           type === 'protect' ? 'password_protect' : 'merge';

            await this.uploadFiles(files, taskType, type);
        } catch (error) {
            showToast('Upload failed: ' + error.message, 'error');
        }
    }

    async uploadFiles(files, taskType, uiType) {
        const formData = new FormData();
        formData.append('task_type', taskType);
        
        for (let file of files) {
            formData.append('files', file);
        }

        try {
            const response = await fetch('/upload/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Upload failed');
            }

            this.currentTask = data.task_id;
            this.uploadedFiles[uiType] = data.files;

            this.updateUI(uiType, data.files);
            showToast('Files uploaded successfully', 'success');

        } catch (error) {
            throw error;
        }
    }

    updateUI(type, files) {
        if (type === 'merge') {
            this.updateMergeUI(files);
        } else {
            this.updateSingleFileUI(type, files[0]);
        }
    }

    updateMergeUI(files) {
        const fileList = document.getElementById('merge-file-list');
        const filesContainer = document.getElementById('merge-files');
        const processBtn = document.getElementById('merge-process-btn');

        fileList.classList.remove('hidden');
        processBtn.classList.remove('hidden');

        filesContainer.innerHTML = '';

        files.forEach((file, index) => {
            const fileElement = document.createElement('div');
            fileElement.className = 'flex items-center justify-between p-4 bg-gray-50 rounded-lg';
            fileElement.setAttribute('data-file-id', file.id);
            
            fileElement.innerHTML = `
                <div class="flex items-center">
                    <i class="fas fa-grip-vertical text-gray-400 mr-3 cursor-move"></i>
                    <i class="fas fa-file-pdf text-red-500 text-xl mr-3"></i>
                    <div>
                        <p class="font-medium text-gray-800">${file.name}</p>
                        <p class="text-sm text-gray-500">${this.formatFileSize(file.size)}</p>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <button class="move-up-btn p-2 text-gray-500 hover:text-blue-600" ${index === 0 ? 'disabled' : ''}>
                        <i class="fas fa-chevron-up"></i>
                    </button>
                    <button class="move-down-btn p-2 text-gray-500 hover:text-blue-600" ${index === files.length - 1 ? 'disabled' : ''}>
                        <i class="fas fa-chevron-down"></i>
                    </button>
                    <button class="remove-file-btn p-2 text-gray-500 hover:text-red-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;

            filesContainer.appendChild(fileElement);

            // Add event listeners for file controls
            this.setupFileControls(fileElement, file.id);
        });
    }

    updateSingleFileUI(type, file) {
        const preview = document.getElementById(`${type}-file-preview`);
        const fileName = document.getElementById(`${type}-file-name`);
        const fileSize = document.getElementById(`${type}-file-size`);
        const processBtn = document.getElementById(`${type}-process-btn`);

        preview.classList.remove('hidden');
        processBtn.classList.remove('hidden');

        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);

        // Show password section for protect type
        if (type === 'protect') {
            document.getElementById('protect-password-section').classList.remove('hidden');
        }
    }

    setupFileControls(fileElement, fileId) {
        const moveUpBtn = fileElement.querySelector('.move-up-btn');
        const moveDownBtn = fileElement.querySelector('.move-down-btn');
        const removeBtn = fileElement.querySelector('.remove-file-btn');

        moveUpBtn.addEventListener('click', () => {
            this.moveFile(fileElement, 'up');
        });

        moveDownBtn.addEventListener('click', () => {
            this.moveFile(fileElement, 'down');
        });

        removeBtn.addEventListener('click', () => {
            this.removeFile(fileElement, fileId);
        });
    }

    moveFile(fileElement, direction) {
        const container = fileElement.parentNode;
        const sibling = direction === 'up' ? fileElement.previousElementSibling : fileElement.nextElementSibling;
        
        if (sibling) {
            if (direction === 'up') {
                container.insertBefore(fileElement, sibling);
            } else {
                container.insertBefore(sibling, fileElement);
            }
            this.updateMoveButtons();
        }
    }

    removeFile(fileElement, fileId) {
        fileElement.remove();
        
        // Update uploaded files array
        this.uploadedFiles.merge = this.uploadedFiles.merge.filter(f => f.id !== fileId);
        
        // Hide merge UI if less than 2 files
        if (this.uploadedFiles.merge.length < 2) {
            document.getElementById('merge-file-list').classList.add('hidden');
            document.getElementById('merge-process-btn').classList.add('hidden');
        }
        
        this.updateMoveButtons();
    }

    updateMoveButtons() {
        const fileElements = document.querySelectorAll('#merge-files > div');
        fileElements.forEach((element, index) => {
            const moveUpBtn = element.querySelector('.move-up-btn');
            const moveDownBtn = element.querySelector('.move-down-btn');
            
            moveUpBtn.disabled = index === 0;
            moveDownBtn.disabled = index === fileElements.length - 1;
        });
    }

    async processMerge() {
        const fileElements = document.querySelectorAll('#merge-files > div');
        const fileOrder = Array.from(fileElements).map(el => el.getAttribute('data-file-id'));

        if (fileOrder.length < 2) {
            showToast('Please upload at least 2 PDF files', 'error');
            return;
        }

        this.showLoading('merge');

        try {
            const response = await fetch('/merge/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    task_id: this.currentTask,
                    file_order: fileOrder
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Merge failed');
            }

            this.hideLoading('merge');
            this.showDownloadButton('merge', data.download_url);
            showToast('PDFs merged successfully!', 'success');

        } catch (error) {
            this.hideLoading('merge');
            showToast('Merge failed: ' + error.message, 'error');
        }
    }

    async processConversion(type) {
        const uiType = type === 'pdf-to-word' ? 'word' : 'ppt';
        const endpoint = type === 'pdf-to-word' ? '/pdf-to-word/' : '/pdf-to-ppt/';

        this.showLoading(uiType);

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    task_id: this.currentTask
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Conversion failed');
            }

            this.hideLoading(uiType);
            this.showDownloadButton(uiType, data.download_url);
            showToast(`PDF converted successfully!`, 'success');

        } catch (error) {
            this.hideLoading(uiType);
            showToast('Conversion failed: ' + error.message, 'error');
        }
    }

    async processPasswordProtect() {
        const password = document.getElementById('protect-password').value;
        const confirmPassword = document.getElementById('protect-confirm-password').value;

        // Validate passwords
        if (!password || !confirmPassword) {
            showToast('Please enter and confirm your password', 'error');
            return;
        }

        if (password !== confirmPassword) {
            showToast('Passwords do not match', 'error');
            return;
        }

        if (password.length < 6) {
            showToast('Password must be at least 6 characters long', 'error');
            return;
        }

        this.showLoading('protect');

        try {
            const response = await fetch('/password-protect/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    task_id: this.currentTask,
                    password: password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Password protection failed');
            }

            this.hideLoading('protect');
            this.showDownloadButton('protect', data.download_url);
            showToast('PDF password protected successfully!', 'success');

        } catch (error) {
            this.hideLoading('protect');
            showToast('Password protection failed: ' + error.message, 'error');
        }
    }

    showLoading(type) {
        document.getElementById(`${type}-loading`).classList.remove('hidden');
        document.getElementById(`${type}-process-btn`).classList.add('hidden');
    }

    hideLoading(type) {
        document.getElementById(`${type}-loading`).classList.add('hidden');
    }

    showDownloadButton(type, downloadUrl) {
        const downloadBtn = document.getElementById(`${type}-download-btn`);
        downloadBtn.classList.remove('hidden');
        downloadBtn.onclick = () => {
            window.location.href = downloadUrl;
        };
    }

    resetTabState(tabType) {
        // Hide all UI elements for the tab
        const elements = [
            `${tabType}-file-list`,
            `${tabType}-file-preview`,
            `${tabType}-password-section`,
            `${tabType}-process-btn`,
            `${tabType}-download-btn`,
            `${tabType}-loading`
        ];

        elements.forEach(elementId => {
            const element = document.getElementById(elementId);
            if (element) {
                element.classList.add('hidden');
            }
        });

        // Clear file inputs
        const fileInput = document.getElementById(`${tabType}-file-input`);
        if (fileInput) {
            fileInput.value = '';
        }

        // Clear password fields
        if (tabType === 'protect') {
            document.getElementById('protect-password').value = '';
            document.getElementById('protect-confirm-password').value = '';
        }

        // Clear merge files container
        if (tabType === 'merge') {
            const filesContainer = document.getElementById('merge-files');
            if (filesContainer) {
                filesContainer.innerHTML = '';
            }
        }

        // Reset current task
        this.currentTask = null;
        this.uploadedFiles[tabType] = [];
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async checkTaskStatus(taskId) {
        try {
            const response = await fetch(`/task/${taskId}/status/`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to check task status:', error);
            return null;
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PDFPowerKit();
});

// Utility function for file validation
function validateFile(file) {
    const validTypes = ['application/pdf'];
    const maxSize = 50 * 1024 * 1024; // 50MB

    if (!validTypes.includes(file.type) && !file.name.toLowerCase().endsWith('.pdf')) {
        throw new Error('Please select a valid PDF file');
    }

    if (file.size > maxSize) {
        throw new Error('File size must be less than 50MB');
    }

    return true;
}

// Utility function for progress tracking
function trackProgress(taskId, callback) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/task/${taskId}/status/`);
            const data = await response.json();
            
            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(interval);
                callback(data);
            }
        } catch (error) {
            console.error('Progress tracking error:', error);
            clearInterval(interval);
        }
    }, 1000);
}

// Service Worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}