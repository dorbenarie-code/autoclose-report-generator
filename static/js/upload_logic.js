document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('excel_files');
    const dropzone = document.querySelector('.upload-dropzone');
    const selectedFilesDisplay = document.getElementById('selectedFilesDisplay');
    const uploadForm = document.getElementById('uploadForm');
    const uploadStatusDiv = document.getElementById('uploadStatus');
    const emailInput = document.getElementById('recipient_email');

    // פונקציה לוולידציית אימייל
    function isValidEmail(email) {
        if (!email || typeof email !== 'string') {
            return false;
        }
        
        // הסרת רווחים
        email = email.trim();
        
        // בדיקת פורמט בסיסי
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(email)) {
            return false;
        }
        
        try {
            // פיצול לחלק מקומי ודומיין
            const [localPart, domain] = email.split('@');
            
            // בדיקת אורך החלק המקומי (מקסימום 64 תווים)
            if (localPart.length > 64) {
                return false;
            }
            
            // בדיקת אורך הדומיין (מקסימום 255 תווים)
            if (domain.length > 255) {
                return false;
            }
            
            // בדיקת נקודות רצופות
            if (localPart.includes('..') || domain.includes('..')) {
                return false;
            }
            
            // בדיקת TLD תקין (לפחות 2 תווים)
            const tld = domain.split('.').pop();
            if (tld.length < 2) {
                return false;
            }
            
            return true;
        } catch (error) {
            console.error('שגיאה בוולידציית אימייל:', error);
            return false;
        }
    }

    // פונקציה להצגת הודעות שגיאה
    function showError(message) {
        if (uploadStatusDiv) {
            uploadStatusDiv.innerHTML = `<div class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                ${message}
            </div>`;
        }
    }

    // פונקציה להצגת הודעות הצלחה
    function showSuccess(message) {
        if (uploadStatusDiv) {
            uploadStatusDiv.innerHTML = `<div class="alert alert-success" role="alert">
                <i class="bi bi-check-circle-fill me-2"></i>
                ${message}
            </div>`;
        }
    }

    // Drag & Drop logic (existing)
    if (dropzone && fileInput) {
        dropzone.addEventListener('click', () => fileInput.click());
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('shadow-lg');
        });
        dropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropzone.classList.remove('shadow-lg');
        });
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('shadow-lg');
            fileInput.files = e.dataTransfer.files;
            updateSelectedFilesDisplay();
        });
        fileInput.addEventListener('change', updateSelectedFilesDisplay);
        function updateSelectedFilesDisplay() {
            if (selectedFilesDisplay) {
                if (fileInput.files.length > 0) {
                    const fileNames = Array.from(fileInput.files).map(file => file.name);
                    selectedFilesDisplay.textContent = `נבחרו: ${fileNames.join(', ')}`;
                } else {
                    selectedFilesDisplay.textContent = '';
                }
            }
        }
    }

    // AJAX upload logic
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const expectedUploadPath = '/upload/upload';
            const actualAction = uploadForm.action;
            if (!actualAction.includes(expectedUploadPath)) {
                showError(`⚠️ כתובת הטופס שגויה. ציפינו ל: ${expectedUploadPath}, בפועל: ${actualAction}`);
                return;
            }

            // בדיקת תקינות האימייל
            if (!emailInput || !emailInput.value) {
                showError('נא להזין כתובת אימייל');
                return;
            }

            if (!isValidEmail(emailInput.value)) {
                showError('כתובת האימייל אינה תקינה');
                return;
            }

            if (uploadStatusDiv) uploadStatusDiv.innerHTML = '<div class="alert alert-info" role="alert"><i class="bi bi-hourglass-split me-2"></i>מעבד קבצים...</div>';
            
            const formData = new FormData(uploadForm);
            
            try {
                const response = await fetch(expectedUploadPath, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    // טיפול בשגיאות מהשרת
                    if (data.field) {
                        // הדגשת השדה הבעייתי
                        const fieldElement = document.getElementById(data.field);
                        if (fieldElement) {
                            fieldElement.classList.add('is-invalid');
                            // הוספת הודעת שגיאה מתחת לשדה
                            const feedbackDiv = document.createElement('div');
                            feedbackDiv.className = 'invalid-feedback';
                            feedbackDiv.textContent = data.message;
                            fieldElement.parentNode.appendChild(feedbackDiv);
                        }
                    }
                    showError(data.message);
                    return;
                }

                if (data.status === 'success') {
                    showSuccess(data.message);
                    
                    // הצגת תוצאות לכל קובץ
                    if (data.results && data.results.length > 0) {
                        const resultsDiv = document.createElement('div');
                        resultsDiv.className = 'mt-3';
                        resultsDiv.innerHTML = '<h4>תוצאות העלאה:</h4>';
                        
                        data.results.forEach(result => {
                            const resultDiv = document.createElement('div');
                            resultDiv.className = `alert ${result.status === 'success' ? 'alert-success' : 'alert-danger'} mb-2`;
                            
                            let resultHtml = `<strong>${result.filename}:</strong> ${result.message}`;
                            if (result.status === 'success' && result.download_url) {
                                resultHtml += ` <a href="${result.download_url}" class="btn btn-sm btn-primary ms-2" target="_blank">
                                    <i class="bi bi-download"></i> הורדת דוח
                                </a>`;
                            }
                            
                            resultDiv.innerHTML = resultHtml;
                            resultsDiv.appendChild(resultDiv);
                        });
                        
                        uploadStatusDiv.appendChild(resultsDiv);
                    }
                } else {
                    showError(data.message);
                }
            } catch (error) {
                console.error('שגיאה בהעלאת הקבצים:', error);
                showError('שגיאה בהעלאת הקבצים. נסה שוב מאוחר יותר.');
            }
        });
    }
}); 