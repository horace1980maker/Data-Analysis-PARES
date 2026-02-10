document.addEventListener('DOMContentLoaded', () => {
    console.log("%c PARES CONVERTER v5.0 LOADED ", "background: #2ecc71; color: #fff; font-weight: bold; padding: 4px; border-radius: 4px;");

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

    async function handleFile(file) {
        if (!file.name.endsWith('.xlsx')) {
            showToast('Please upload an Excel file (.xlsx)', 'error');
            return;
        }
        selectedFile = file;
        fileName.textContent = file.name;
        fileInfo.style.display = 'flex';
        resultCard.style.display = 'none';

        // Run diagnostics automatically
        const apiUrl = document.getElementById('api-url').value.replace(/\/$/, '');
        showToast(`Analizando archivo: ${file.name}...`, 'info');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('lang', 'es');

        try {
            const response = await fetch(`${apiUrl}/diagnose`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (data.error_count > 0 || data.warning_count > 0) {
                showDiagnosticResults(data);
                if (data.error_count > 0) {
                    showToast(`⚠️ Se encontraron ${data.error_count} errores que deben corregirse`, 'error');
                    convertBtn.disabled = true;
                } else {
                    showToast(`✓ Archivo listo con ${data.warning_count} advertencias`, 'warning');
                    convertBtn.disabled = false;
                }
            } else {
                clearDiagnosticResults();
                showToast(`✓ Archivo válido: ${file.name}`, 'success');
                convertBtn.disabled = false;
            }
        } catch (e) {
            console.error('Diagnostic error:', e);
            // If diagnostics fail, still allow conversion attempt
            convertBtn.disabled = false;
            showToast(`Archivo seleccionado: ${file.name}`, 'success');
        }
    }

    function showDiagnosticResults(data) {
        let container = document.getElementById('diagnostic-results');
        if (!container) {
            container = document.createElement('div');
            container.id = 'diagnostic-results';
            container.style.cssText = 'margin-top:20px;padding:15px;background:#fff;border-radius:8px;border:1px solid #ddd;color:#333;';
            // Insert after convert button
            if (resultCard && resultCard.parentNode) {
                resultCard.parentNode.insertBefore(container, resultCard);
            }
        }

        let html = `<h3 style="margin:0 0 15px 0;color:#333;">📋 Diagnóstico del Archivo</h3>`;

        if (data.errors && data.errors.length > 0) {
            html += `<div style="margin-bottom:15px;"><strong style="color:#d32f2f;">❌ Errores (${data.errors.length})</strong>`;
            html += `<table style="width:100%;margin-top:10px;border-collapse:collapse;font-size:0.9em;color:#333;">`;
            html += `<tr style="background:#ffebee;"><th style="padding:8px;text-align:left;border:1px solid #ffcdd2;color:#b71c1c;">Hoja</th><th style="padding:8px;text-align:left;border:1px solid #ffcdd2;color:#b71c1c;">Problema</th><th style="padding:8px;text-align:left;border:1px solid #ffcdd2;color:#b71c1c;">Solución</th></tr>`;
            for (const e of data.errors) {
                html += `<tr><td style="padding:8px;border:1px solid #ffcdd2;color:#333;">${e.sheet || '-'}</td><td style="padding:8px;border:1px solid #ffcdd2;color:#333;">${e.description}</td><td style="padding:8px;border:1px solid #ffcdd2;color:#333;">${e.suggested_fix}</td></tr>`;
            }
            html += `</table></div>`;
        }

        if (data.warnings && data.warnings.length > 0) {
            html += `<div><strong style="color:#f57c00;">⚠️ Advertencias (${data.warnings.length})</strong>`;
            html += `<table style="width:100%;margin-top:10px;border-collapse:collapse;font-size:0.9em;color:#333;">`;
            html += `<tr style="background:#fff8e1;"><th style="padding:8px;text-align:left;border:1px solid #ffecb3;color:#e65100;">Hoja</th><th style="padding:8px;text-align:left;border:1px solid #ffecb3;color:#e65100;">Problema</th><th style="padding:8px;text-align:left;border:1px solid #ffecb3;color:#e65100;">Solución</th></tr>`;
            for (const w of data.warnings) {
                html += `<tr><td style="padding:8px;border:1px solid #ffecb3;color:#333;">${w.sheet || '-'}</td><td style="padding:8px;border:1px solid #ffecb3;color:#333;">${w.description}</td><td style="padding:8px;border:1px solid #ffecb3;color:#333;">${w.suggested_fix}</td></tr>`;
            }
            html += `</table></div>`;
        }

        container.innerHTML = html;
        container.style.display = 'block';
    }

    function clearDiagnosticResults() {
        const container = document.getElementById('diagnostic-results');
        if (container) container.style.display = 'none';
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
                let errData = {};
                try {
                    errData = await response.json();
                } catch (e) {
                    const text = await response.text();
                    errData = { error: `Error ${response.status}: ${text.substring(0, 100)}` };
                }

                // 1. Validation Issues
                if (errData.issues) {
                    showValidationErrors(errData.issues);
                    throw new Error("Validación fallida. Revise la lista de problemas detectados abajo.");
                }

                // 2. Internal Server Error with Traceback
                if (errData.detail) {
                    showErrorDetails(errData.error || "Error Interno", errData.detail);
                    throw new Error(errData.error || "Error interno del servidor");
                }

                // 3. Generic Error
                const msg = errData.detail || errData.error || `Conversion failed (${response.status})`;
                throw new Error(msg);
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
            // Insert before resultCard using its parent
            if (resultCard && resultCard.parentNode) {
                resultCard.parentNode.insertBefore(container, resultCard);
            } else {
                console.warn("resultCard or parent not found, appending to main");
                const main = document.querySelector('main');
                if (main) main.appendChild(container);
                else document.body.appendChild(container);
            }
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

        table.style.color = '#333';
        container.appendChild(table);
        container.style.display = 'block';
    }

    function showErrorDetails(title, detail) {
        let container = document.getElementById('validation-errors');
        if (!container) {
            container = document.createElement('div');
            container.id = 'validation-errors';
            // Insert before resultCard using its parent
            if (resultCard && resultCard.parentNode) {
                resultCard.parentNode.insertBefore(container, resultCard);
            } else {
                document.querySelector('main').appendChild(container);
            }
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
