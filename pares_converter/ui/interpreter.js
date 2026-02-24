document.addEventListener('DOMContentLoaded', () => {
    // ==== ELEMENTS ====
    const dropZone = document.getElementById('interp-drop-zone');
    const fileInput = document.getElementById('interp-file-input');
    const fileInfo = document.getElementById('interp-file-info');
    const fileName = document.getElementById('interp-file-display-name');
    const removeFile = document.getElementById('interp-remove-file');
    const interpBtn = document.getElementById('interp-btn');
    const progressContainer = document.getElementById('interp-progress');
    const progressFill = document.getElementById('interp-progress-fill');
    const progressText = document.getElementById('interp-progress-text');
    const resultCard = document.getElementById('interp-result-card');
    const storylineCards = document.querySelectorAll('.storyline-card');

    let selectedFile = null;
    let selectedStoryline = 1;
    let interpResults = {
        xlsx: null,
        report: null,
        zip: null
    };

    // ==== STORYLINE SELECTION ====
    storylineCards.forEach(card => {
        card.addEventListener('click', () => {
            if (card.classList.contains('disabled')) {
                showToast('Esta storyline estará disponible próximamente.', 'info');
                return;
            }
            storylineCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedStoryline = parseInt(card.dataset.storyline);

            if (selectedFile) {
                validateFile(selectedFile, selectedStoryline);
            }
        });
    });

    // ==== FILE UPLOAD ====
    dropZone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(name => {
        dropZone.addEventListener(name, (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(name => {
        dropZone.addEventListener(name, (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length) handleFile(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
    });

    function handleFile(file) {
        if (!file.name.endsWith('.xlsx')) {
            showToast('Por favor sube un archivo Excel (.xlsx)', 'error');
            return;
        }
        selectedFile = file;
        fileName.textContent = file.name;
        fileInfo.style.display = 'flex';
        resultCard.style.display = 'none';
        showToast(`Archivo seleccionado: ${file.name}`, 'success');

        validateFile(file, selectedStoryline);
    }

    async function validateFile(file, storyline) {
        const validationStatus = document.getElementById('interp-validation-status');
        const validationIcon = document.getElementById('interp-validation-icon');
        const validationMessage = document.getElementById('interp-validation-message');
        const validationDetails = document.getElementById('interp-validation-details');

        validationStatus.style.display = 'flex';
        validationStatus.className = 'validation-status';
        validationIcon.textContent = '...';
        validationMessage.innerHTML = '<strong>Validando archivo...</strong>';
        validationDetails.textContent = '';
        interpBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('storyline', storyline);

        try {
            const response = await fetch('/validate', {
                method: 'POST',
                body: formData,
            });
            const result = await response.json();

            if (result.is_raw_database) {
                validationStatus.className = 'validation-status invalid';
                validationIcon.textContent = '!';
                validationMessage.innerHTML = '<strong>Base de datos cruda detectada</strong><br>Este archivo debe ser convertido primero usando el Conversor.';
                validationDetails.innerHTML = `<a href="/" style="color: var(--primary);">Ir al Conversor &rarr;</a>`;
                interpBtn.disabled = true;
            } else if (!result.valid) {
                validationStatus.className = 'validation-status invalid';
                validationIcon.textContent = 'X';
                validationMessage.innerHTML = `<strong>Hojas requeridas faltantes</strong><br>${result.message}`;
                validationDetails.innerHTML = `Requeridas: <code>${result.missing_required.join('</code>, <code>')}</code>`;
                interpBtn.disabled = true;
            } else if (result.missing_recommended.length > 0) {
                validationStatus.className = 'validation-status warning';
                validationIcon.textContent = '!';
                validationMessage.innerHTML = `<strong>Listo con advertencias</strong><br>${result.message}`;
                validationDetails.innerHTML = `Hojas opcionales faltantes: <code>${result.missing_recommended.slice(0, 3).join('</code>, <code>')}</code>`;
                interpBtn.disabled = false;
            } else {
                validationStatus.className = 'validation-status valid';
                validationIcon.textContent = 'OK';
                validationMessage.innerHTML = '<strong>Listo para generar informe</strong><br>Todas las hojas requeridas fueron encontradas.';
                validationDetails.innerHTML = `Encontradas: <code>${result.present_required.join('</code>, <code>')}</code>`;
                interpBtn.disabled = false;
            }
        } catch (error) {
            validationStatus.className = 'validation-status warning';
            validationIcon.textContent = '!';
            validationMessage.innerHTML = '<strong>Validación omitida</strong><br>No se pudo validar el archivo. Puedes intentar generar el informe.';
            validationDetails.textContent = error.message;
            interpBtn.disabled = false;
        }
    }

    removeFile.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedFile = null;
        fileInfo.style.display = 'none';
        interpBtn.disabled = true;
        fileInput.value = '';
        document.getElementById('interp-validation-status').style.display = 'none';
    });

    // ==== RUN INTERPRETATION ====
    // ==== RUN INTERPRETATION ====
    interpBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        let endpoint = '';
        let storylineName = '';

        if (selectedStoryline === 1) {
            endpoint = '/interpret/storyline1';
            storylineName = 'Storyline 1';
        } else if (selectedStoryline === 2) {
            endpoint = '/interpret/storyline2';
            storylineName = 'Storyline 2 (Servicios Ecosistémicos)';
        } else if (selectedStoryline === 3) {
            endpoint = '/interpret/storyline3';
            storylineName = 'Storyline 3 (Equidad y Vulnerabilidad)';
        } else if (selectedStoryline === 4) {
            endpoint = '/interpret/storyline4';
            storylineName = 'Storyline 4 (Viabilidad y Gobernanza)';
        } else if (selectedStoryline === 5) {
            endpoint = '/interpret/storyline5';
            storylineName = 'Storyline 5 (Portafolio SbN)';
        } else if (selectedStoryline === 6) {
            endpoint = '/analyze/capacity';
            storylineName = 'Capacidad Adaptativa';
        } else {
            showToast('Storyline no implementada aún', 'error');
            return;
        }

        console.log('[INTERPRETER] Selected Storyline:', selectedStoryline);
        console.log('[INTERPRETER] Final Endpoint:', endpoint);
        console.log('[INTERPRETER] Final Storyline Name:', storylineName);

        // Clear previous result
        interpResults = { xlsx: null, report: null, zip: null };

        setLoading(interpBtn, true);
        progressContainer.style.display = 'block';
        resultCard.style.display = 'none';
        updateProgress(10, 'Subiendo archivo...');

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            updateProgress(20, 'Generando reporte analítico...');

            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                let errorMessage = 'Error al generar informe';
                try {
                    const errData = await response.json();
                    errorMessage = errData.detail || errData.error || errorMessage;
                } catch (e) {
                    try {
                        errorMessage = await response.text() || errorMessage;
                    } catch (e2) { }
                }
                throw new Error(errorMessage);
            }

            updateProgress(70, 'Procesando resultados...');

            const result = await response.json();

            if (result.report_html) {
                interpResults.report = new Blob([result.report_html], { type: 'text/html' });
            }
            if (result.xlsx_base64) {
                interpResults.xlsx = base64ToBlob(result.xlsx_base64, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
            }
            if (result.zip_base64) {
                interpResults.zip = base64ToBlob(result.zip_base64, 'application/zip');
            }

            // Display stats
            // Handle different result structures (Dashboard generator vs Storyline1 generator)
            document.getElementById('interp-res-tables').textContent = result.tables_count || '-';
            document.getElementById('interp-res-figures').textContent = result.figures_count || '-';
            document.getElementById('interp-res-duration').textContent = result.duration || '-';

            updateProgress(100, 'Completado!');

            setTimeout(() => {
                progressContainer.style.display = 'none';
                resultCard.style.display = 'block';
                showToast('Reporte analítico generado exitosamente!', 'success');
            }, 500);

        } catch (error) {
            console.error(error);
            showToast(error.message, 'error');
            progressContainer.style.display = 'none';
        } finally {
            setLoading(interpBtn, false);
        }
    });

    // ==== DOWNLOAD BUTTONS ====
    document.getElementById('interp-download-xlsx-btn').addEventListener('click', () => {
        if (interpResults.xlsx) {
            const prefix = `storyline${selectedStoryline}`;
            downloadBlob(interpResults.xlsx, `${prefix}_outputs.xlsx`);
            showToast('Descargando libro Excel...', 'success');
        } else {
            showToast('Archivo Excel no disponible', 'error');
        }
    });

    document.getElementById('interp-download-report-btn').addEventListener('click', () => {
        if (interpResults.report) {
            const url = window.URL.createObjectURL(interpResults.report);
            window.open(url, '_blank');
        } else {
            showToast('Informe no disponible', 'error');
        }
    });

    document.getElementById('interp-download-html-btn').addEventListener('click', () => {
        if (interpResults.report) {
            const prefix = `storyline${selectedStoryline}`;
            const timestamp = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
            downloadBlob(interpResults.report, `${prefix}_analysis_${timestamp}.html`);
            showToast('Descargando informe HTML...', 'success');
        } else {
            showToast('Informe no disponible', 'error');
        }
    });

    document.getElementById('interp-download-zip-btn').addEventListener('click', () => {
        if (interpResults.zip) {
            const prefix = `storyline${selectedStoryline}`;
            const timestamp = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
            downloadBlob(interpResults.zip, `${prefix}_outputs_${timestamp}.zip`);
            showToast('Descargando todos los archivos...', 'success');
        } else {
            showToast('Archivo ZIP no disponible', 'error');
        }
    });

    // ==== UTILITY FUNCTIONS ====
    function setLoading(btn, isLoading) {
        const loader = btn.querySelector('.loader');
        const text = btn.querySelector('span');
        btn.disabled = isLoading;
        if (loader) loader.style.display = isLoading ? 'block' : 'none';
        if (text) text.style.display = isLoading ? 'none' : 'block';
    }

    function updateProgress(percent, text) {
        progressFill.style.width = `${percent}%`;
        progressText.textContent = text;
    }

    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        if (type === 'error') toast.style.borderLeft = '4px solid var(--error)';
        if (type === 'success') toast.style.borderLeft = '4px solid var(--success)';

        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    function downloadBlob(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    function base64ToBlob(base64, mimeType) {
        const byteChars = atob(base64);
        const byteNumbers = new Array(byteChars.length);
        for (let i = 0; i < byteChars.length; i++) {
            byteNumbers[i] = byteChars.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        return new Blob([byteArray], { type: mimeType });
    }
});
