document.addEventListener('DOMContentLoaded', () => {
    // ==== CONVERTER ====
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-display-name');
    const removeFile = document.getElementById('remove-file');
    const convertBtn = document.getElementById('convert-btn');
    const resultCard = document.getElementById('result-card');
    const downloadBtn = document.getElementById('download-btn');
    const loader = convertBtn.querySelector('.loader');
    const btnText = convertBtn.querySelector('span');

    let selectedFile = null;
    let convertedBlob = null;
    let outputFilename = 'converted.xlsx';

    // Set default API URL to current origin
    const apiUrlInput = document.getElementById('api-url');
    if (apiUrlInput) {
        apiUrlInput.value = window.location.origin;
    }

    // Drag and Drop
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
            showToast('Please upload an Excel file (.xlsx)', 'error');
            return;
        }
        selectedFile = file;
        fileName.textContent = file.name;
        fileInfo.style.display = 'flex';
        convertBtn.disabled = false;
        resultCard.style.display = 'none';
        showToast(`File selected: ${file.name}`, 'success');
    }

    removeFile.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedFile = null;
        fileInfo.style.display = 'none';
        convertBtn.disabled = true;
        fileInput.value = '';
    });

    // Conversion
    convertBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        const apiUrl = document.getElementById('api-url').value.replace(/\/$/, '');
        const orgSlug = document.getElementById('org-slug').value;

        setLoading(true);

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('org_slug', orgSlug);

        try {
            const response = await fetch(`${apiUrl}/convert`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                let errorMessage = `Conversion failed (${response.status})`;
                try {
                    const errData = await response.json();

                    // Handle key validation issues
                    if (errData.issues) {
                        showValidationErrors(errData.issues);
                        throw new Error("Validación fallida. Revise la lista de problemas detectados abajo.");
                    }

                    // Handle Internal Server Error (500) with detail
                    if (errData.detail) {
                        // Display the traceback in the error box
                        showErrorDetails(errData.error, errData.detail);
                        throw new Error(errData.error || "Error interno del servidor");
                    }

                    errorMessage = errData.detail || errData.error || errorMessage;
                } catch (e) {
                    if (e.message.startsWith("Validación") || e.message.startsWith("Error interno")) throw e;
                    try {
                        const text = await response.text();
                        if (text) errorMessage = `Error ${response.status}: ${text.substring(0, 100)}`;
                    } catch (e2) { }
                }
                throw new Error(errorMessage);
            }

            // Clear errors on success
            const errDiv = document.getElementById('validation-errors');
            if (errDiv) errDiv.style.display = 'none';

            convertedBlob = await response.blob();

            const geoId = response.headers.get('X-Converter-GeoId');
            const qaIssues = response.headers.get('X-Converter-QAIssues');
            const contentDisp = response.headers.get('Content-Disposition');

            if (contentDisp && contentDisp.includes('filename=')) {
                outputFilename = contentDisp.split('filename=')[1].replace(/"/g, '');
            } else {
                outputFilename = `FINAL_${orgSlug}_analysis_ready.xlsx`;
            }

            document.getElementById('res-geoid').textContent = geoId || 'N/A';
            document.getElementById('res-qa').textContent = qaIssues || '0';

            resultCard.style.display = 'block';
            showToast('Conversion successful!', 'success');

        } catch (error) {
            console.error(error);
            showToast(error.message, 'error');
        } finally {
            setLoading(false);
        }
    });

    downloadBtn.addEventListener('click', () => {
        if (!convertedBlob) return;
        const url = window.URL.createObjectURL(convertedBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = outputFilename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showToast('Downloading file...', 'success');
    });

    function setLoading(isLoading) {
        convertBtn.disabled = isLoading;
        loader.style.display = isLoading ? 'block' : 'none';
        btnText.style.display = isLoading ? 'none' : 'block';
    }

    function showValidationErrors(issues) {
        let container = document.getElementById('validation-errors');
        if (!container) {
            container = document.createElement('div');
            container.id = 'validation-errors';
            // Insert after convert button container
            convertBtn.parentNode.parentNode.insertBefore(container, resultCard);
            // Apply base styles
            container.style.marginTop = '20px';
            container.style.padding = '15px';
            container.style.background = '#fff0f0';
            container.style.border = '1px solid #ffcdcd';
            container.style.borderRadius = '8px';
            container.style.color = '#d8000c';
        }

        container.innerHTML = '<h3>Problemas Detectados:</h3>';

        const table = document.createElement('table');
        table.style.width = '100%';
        table.style.borderCollapse = 'collapse';
        table.style.marginTop = '10px';
        table.style.fontSize = '0.9em';

        // Header
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr style="background: #ffdbdb; text-align: left;">
                <th style="padding: 8px; border: 1px solid #ffcdcd;">Hoja</th>
                <th style="padding: 8px; border: 1px solid #ffcdcd;">Estado</th>
                <th style="padding: 8px; border: 1px solid #ffcdcd;">Falta</th>
            </tr>
        `;
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        issues.forEach(issue => {
            if (issue.status === 'ok') return;
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="padding: 8px; border: 1px solid #ffcdcd;">${issue.sheet}</td>
                <td style="padding: 8px; border: 1px solid #ffcdcd;">${issue.status}</td>
                <td style="padding: 8px; border: 1px solid #ffcdcd; font-family: monospace;">${issue.missing_cols || '-'}</td>
            `;
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        container.appendChild(table);
        container.style.display = 'block';
    }

    function showErrorDetails(title, detail) {
        let container = document.getElementById('validation-errors');
        if (!container) {
            container = document.createElement('div');
            container.id = 'validation-errors';
            convertBtn.parentNode.parentNode.insertBefore(container, resultCard);
            container.style.marginTop = '20px';
            container.style.padding = '15px';
            container.style.background = '#fff0f0';
            container.style.border = '1px solid #ffcdcd';
            container.style.borderRadius = '8px';
            container.style.color = '#d8000c';
        }

        container.innerHTML = `<h3>${title || 'Error'}</h3>`;

        const pre = document.createElement('pre');
        pre.style.whiteSpace = 'pre-wrap';
        pre.style.marginTop = '10px';
        pre.style.fontSize = '0.85em';
        pre.style.fontFamily = 'monospace';
        pre.style.color = '#333';
        pre.style.background = '#f8f8f8';
        pre.style.padding = '10px';
        pre.style.overflowX = 'auto';
        pre.textContent = detail;

        container.appendChild(pre);
        container.style.display = 'block';
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
});
