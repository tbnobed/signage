// Digital Signage Manager - Main JavaScript

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeModals();
    initializeFileUploads();
    initializeFormValidation();
    setupAutoRefresh();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize Bootstrap modals
function initializeModals() {
    const modalElements = document.querySelectorAll('.modal');
    modalElements.forEach(function(modalEl) {
        modalEl.addEventListener('show.bs.modal', function() {
            // Clear form validation states when modal opens
            const form = modalEl.querySelector('form');
            if (form) {
                form.classList.remove('was-validated');
                clearFormErrors(form);
            }
        });
    });
}

// Initialize file upload functionality
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            handleFileSelect(e);
        });
    });

    // Drag and drop functionality
    const uploadAreas = document.querySelectorAll('.file-upload-area');
    uploadAreas.forEach(function(area) {
        area.addEventListener('dragover', function(e) {
            e.preventDefault();
            area.classList.add('dragover');
        });

        area.addEventListener('dragleave', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
        });

        area.addEventListener('drop', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const fileInput = area.querySelector('input[type="file"]');
                if (fileInput) {
                    fileInput.files = files;
                    handleFileSelect({target: fileInput});
                }
            }
        });
    });
}

// Handle file selection
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file size (500MB max)
    const maxSize = 500 * 1024 * 1024;
    if (file.size > maxSize) {
        showAlert('File size too large. Maximum allowed size is 500MB.', 'danger');
        event.target.value = '';
        return;
    }

    // Show file preview if applicable
    showFilePreview(file, event.target);

    // Update UI
    const fileName = event.target.closest('.input-group')?.querySelector('.file-name');
    if (fileName) {
        fileName.textContent = file.name;
        fileName.classList.remove('d-none');
    }
}

// Show file preview
function showFilePreview(file, input) {
    const previewContainer = document.getElementById('preview') || 
                           input.closest('form')?.querySelector('.preview-container');
    
    if (!previewContainer) return;

    const reader = new FileReader();
    
    if (file.type.startsWith('image/')) {
        reader.onload = function(e) {
            const img = previewContainer.querySelector('img') || document.createElement('img');
            img.src = e.target.result;
            img.className = 'img-fluid rounded mb-2';
            img.style.maxHeight = '200px';
            
            if (!previewContainer.querySelector('img')) {
                previewContainer.appendChild(img);
            }
            
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else if (file.type.startsWith('video/')) {
        previewContainer.innerHTML = `
            <div class="text-center">
                <i class="fas fa-video fa-3x text-muted mb-2"></i>
                <p class="mb-0">Video file selected: ${file.name}</p>
                <small class="text-muted">${formatFileSize(file.size)}</small>
            </div>
        `;
        previewContainer.style.display = 'block';
    }
}

// Initialize form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// Setup auto-refresh for dashboard
function setupAutoRefresh() {
    if (window.location.pathname === '/' || window.location.pathname.includes('dashboard')) {
        // Refresh device status every 30 seconds
        setInterval(refreshDeviceStatus, 30000);
    }
}

// Refresh device status
async function refreshDeviceStatus() {
    try {
        const response = await fetch('/api/devices/status');
        if (response.ok) {
            const data = await response.json();
            updateDeviceCards(data);
        } else {
            console.error('Failed to refresh device status - HTTP error:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('Failed to refresh device status - Network error:', error.message, error);
    }
}

// Update device cards with new status
function updateDeviceCards(devices) {
    devices.forEach(function(device) {
        const deviceCard = document.querySelector(`[data-device-id="${device.id}"]`);
        if (deviceCard) {
            const statusBadge = deviceCard.querySelector('.status-badge');
            const lastCheckin = deviceCard.querySelector('.last-checkin');
            
            if (statusBadge) {
                statusBadge.className = `badge ${device.is_online ? 'bg-success' : 'bg-secondary'}`;
                statusBadge.textContent = device.is_online ? 'Online' : 'Offline';
            }
            
            if (lastCheckin && device.last_checkin) {
                lastCheckin.textContent = formatDateTime(device.last_checkin);
            }
        }
    });
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts-container') || 
                           document.querySelector('.container');
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertsContainer.insertBefore(alert, alertsContainer.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function clearFormErrors(form) {
    const errorElements = form.querySelectorAll('.is-invalid');
    errorElements.forEach(function(element) {
        element.classList.remove('is-invalid');
    });
    
    const feedbackElements = form.querySelectorAll('.invalid-feedback');
    feedbackElements.forEach(function(element) {
        element.remove();
    });
}

// Button loading states
function setButtonLoading(button, loading = true) {
    if (loading) {
        button.classList.add('btn-loading');
        button.disabled = true;
        const text = button.querySelector('.btn-text') || button;
        text.dataset.originalText = text.textContent;
        text.textContent = 'Loading...';
    } else {
        button.classList.remove('btn-loading');
        button.disabled = false;
        const text = button.querySelector('.btn-text') || button;
        if (text.dataset.originalText) {
            text.textContent = text.dataset.originalText;
        }
    }
}

// AJAX form submission helper
async function submitForm(form, options = {}) {
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    
    try {
        if (submitButton) setButtonLoading(submitButton, true);
        
        const response = await fetch(form.action || window.location.href, {
            method: form.method || 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            if (options.onSuccess) {
                options.onSuccess(result);
            } else if (result.redirect) {
                window.location.href = result.redirect;
            } else {
                showAlert(result.message || 'Operation completed successfully', 'success');
            }
        } else {
            const error = await response.json();
            showAlert(error.message || 'An error occurred', 'danger');
        }
    } catch (error) {
        console.error('Form submission error:', error);
        showAlert('Network error occurred', 'danger');
    } finally {
        if (submitButton) setButtonLoading(submitButton, false);
    }
}

// Export functions for use in templates
window.DSManager = {
    showAlert,
    setButtonLoading,
    submitForm,
    formatFileSize,
    formatDateTime
};
