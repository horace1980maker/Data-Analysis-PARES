document.addEventListener('DOMContentLoaded', () => {
    // ==== ELEMENTS ====
    const analyzerDropZone = document.getElementById('analyzer-drop-zone');
    const analyzerFileInput = document.getElementById('analyzer-file-input');
    const analyzerFileInfo = document.getElementById('analyzer-file-info');
    const analyzerFileName = document.getElementById('analyzer-file-display-name');
    const analyzerRemoveFile = document.getElementById('analyzer-remove-file');
    const analyzeBtn = document.getElementById('analyze-btn');
    const analysisProgress = document.getElementById('analysis-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const analysisResultCard = document.getElementById('analysis-result-card');
    const storylineCards = document.querySelectorAll('.storyline-card');

    let analyzerSelectedFile = null;
    let selectedStoryline = 1;
    let analysisResults = {
        xlsx: null,
        report: null,
        zip: null
    };

    // ==== STORYLINE SELECTION ====
    storylineCards.forEach(card => {
        card.addEventListener('click', () => {
            if (card.classList.contains('disabled')) {
                showToast('This storyline is coming soon!', 'info');
                return;
            }
            storylineCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedStoryline = parseInt(card.dataset.storyline);

            // Re-validate if file already selected
            if (analyzerSelectedFile) {
                validateFile(analyzerSelectedFile, selectedStoryline);
            }
        });
    });

    // ==== FILE UPLOAD ====
    analyzerDropZone.addEventListener('click', () => analyzerFileInput.click());

    ['dragenter', 'dragover'].forEach(name => {
        analyzerDropZone.addEventListener(name, (e) => {
            e.preventDefault();
            analyzerDropZone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(name => {
        analyzerDropZone.addEventListener(name, (e) => {
            e.preventDefault();
            analyzerDropZone.classList.remove('drag-over');
        });
    });

    analyzerDropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length) handleAnalyzerFile(files[0]);
    });

    analyzerFileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleAnalyzerFile(e.target.files[0]);
    });

    function handleAnalyzerFile(file) {
        if (!file.name.endsWith('.xlsx')) {
            showToast('Please upload an Excel file (.xlsx)', 'error');
            return;
        }
        analyzerSelectedFile = file;
        analyzerFileName.textContent = file.name;
        analyzerFileInfo.style.display = 'flex';
        analysisResultCard.style.display = 'none';
        showToast(`File selected: ${file.name}`, 'success');

        // Validate the file for the selected storyline
        validateFile(file, selectedStoryline);
    }

    async function validateFile(file, storyline) {
        const validationStatus = document.getElementById('validation-status');
        const validationIcon = document.getElementById('validation-icon');
        const validationMessage = document.getElementById('validation-message');
        const validationDetails = document.getElementById('validation-details');

        validationStatus.style.display = 'flex';
        validationStatus.className = 'validation-status';
        validationIcon.textContent = '⏳';
        validationMessage.innerHTML = '<strong>Validating file...</strong>';
        validationDetails.textContent = '';
        analyzeBtn.disabled = true;

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
                validationIcon.textContent = '⚠️';
                validationMessage.innerHTML = '<strong>Raw Database Detected</strong><br>This appears to be a raw database file. Please convert it first using the Converter page.';
                validationDetails.innerHTML = `<a href="/" style="color: var(--primary);">Go to Converter →</a>`;
                analyzeBtn.disabled = true;
            } else if (!result.valid) {
                validationStatus.className = 'validation-status invalid';
                validationIcon.textContent = '❌';
                validationMessage.innerHTML = `<strong>Missing Required Sheets</strong><br>${result.message}`;
                validationDetails.innerHTML = `Required: <code>${result.missing_required.join('</code>, <code>')}</code>`;
                analyzeBtn.disabled = true;
            } else if (result.missing_recommended.length > 0) {
                validationStatus.className = 'validation-status warning';
                validationIcon.textContent = '⚡';
                validationMessage.innerHTML = `<strong>Ready with Warnings</strong><br>${result.message}`;
                validationDetails.innerHTML = `Some optional sheets missing: <code>${result.missing_recommended.slice(0, 3).join('</code>, <code>')}</code>`;
                analyzeBtn.disabled = false;
            } else {
                validationStatus.className = 'validation-status valid';
                validationIcon.textContent = '✅';
                validationMessage.innerHTML = '<strong>Ready to Analyze!</strong><br>All required sheets found.';
                validationDetails.innerHTML = `Found: <code>${result.present_required.join('</code>, <code>')}</code>`;
                analyzeBtn.disabled = false;
            }
        } catch (error) {
            validationStatus.className = 'validation-status warning';
            validationIcon.textContent = '⚠️';
            validationMessage.innerHTML = '<strong>Validation skipped</strong><br>Could not validate file. You can still try to analyze.';
            validationDetails.textContent = error.message;
            analyzeBtn.disabled = false;
        }
    }

    analyzerRemoveFile.addEventListener('click', (e) => {
        e.stopPropagation();
        analyzerSelectedFile = null;
        analyzerFileInfo.style.display = 'none';
        analyzeBtn.disabled = true;
        analyzerFileInput.value = '';
    });

    // ==== RUN ANALYSIS ====
    analyzeBtn.addEventListener('click', async () => {
        if (!analyzerSelectedFile) return;

        showToast('Running Analysis V3...', 'info');

        // FORCE CAST TO NUMBER TO BE ABSOLUTELY SURE
        const currentStoryline = parseInt(selectedStoryline);

        if (currentStoryline === 1) {
            endpoint = '/analyze/storyline1';
            storylineName = 'Storyline 1';
        } else if (currentStoryline === 2) {
            endpoint = '/analyze/storyline2';
            storylineName = 'Storyline 2';
        } else if (currentStoryline === 3) {
            endpoint = '/analyze/storyline3';
            storylineName = 'Storyline 3';
        } else if (currentStoryline === 4) {
            endpoint = '/analyze/storyline4';
            storylineName = 'Storyline 4';
        } else if (currentStoryline === 5) {
            endpoint = '/analyze/storyline5';
            storylineName = 'Storyline 5';
        } else if (currentStoryline === 6) {
            endpoint = '/analyze/capacity';
            storylineName = 'Capacidad Adaptativa';
        }

        console.log('!!! ANALYZER V3 RUNNING !!!');
        console.log('!!! RAW selectedStoryline:', selectedStoryline);
        console.log('!!! PARSED currentStoryline:', currentStoryline);
        console.log('!!! FINAL ENDPOINT:', endpoint);

        const topN = document.getElementById('top-n').value;
        const includeFigures = document.getElementById('include-figures').checked;
        const includeReport = document.getElementById('include-report').checked;

        // Clear previous results
        analysisResults = { xlsx: null, report: null, zip: null };

        setLoading(analyzeBtn, true);
        analysisProgress.style.display = 'block';
        analysisResultCard.style.display = 'none';
        updateProgress(10, 'Uploading file...');

        const formData = new FormData();
        formData.append('file', analyzerSelectedFile);
        formData.append('top_n', topN);
        formData.append('include_figures', includeFigures);
        formData.append('include_report', includeReport);
        formData.append('lang', window.i18n ? window.i18n.getLang() : 'es');

        try {
            updateProgress(20, `Starting ${storylineName} analysis...`);

            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                let errorMessage = 'Analysis failed';
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

            updateProgress(70, 'Processing results...');

            const result = await response.json();

            // Store results
            if (result.xlsx_base64) {
                analysisResults.xlsx = base64ToBlob(result.xlsx_base64, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
            }
            if (result.report_html) {
                analysisResults.report = new Blob([result.report_html], { type: 'text/html' });
            }
            if (result.zip_base64) {
                analysisResults.zip = base64ToBlob(result.zip_base64, 'application/zip');
            }

            // Display stats
            document.getElementById('res-tables').textContent = result.tables_count || '0';
            document.getElementById('res-figures').textContent = result.figures_count || '0';
            document.getElementById('res-duration').textContent = result.duration || '-';

            // Update result card subtitle
            const resultSubtitle = document.querySelector('.result-subtitle');
            if (resultSubtitle) resultSubtitle.textContent = `Your ${storylineName} analysis is ready`;

            updateProgress(100, 'Complete!');

            setTimeout(() => {
                analysisProgress.style.display = 'none';
                analysisResultCard.style.display = 'block';
                showToast(`${storylineName} analysis completed successfully!`, 'success');
            }, 500);

        } catch (error) {
            console.error(error);
            showToast(error.message, 'error');
            analysisProgress.style.display = 'none';
        } finally {
            setLoading(analyzeBtn, false);
        }
    });

    // ==== DOWNLOAD BUTTONS ====
    document.getElementById('download-xlsx-btn').addEventListener('click', () => {
        if (analysisResults.xlsx) {
            const prefix = `storyline${selectedStoryline}`;
            downloadBlob(analysisResults.xlsx, `${prefix}_outputs.xlsx`);
            showToast('Downloading Excel workbook...', 'success');
        } else {
            showToast('Excel file not available', 'error');
        }
    });

    document.getElementById('download-report-btn').addEventListener('click', () => {
        if (analysisResults.report) {
            const url = window.URL.createObjectURL(analysisResults.report);
            window.open(url, '_blank');
        } else {
            showToast('Report not available', 'error');
        }
    });

    document.getElementById('download-html-btn').addEventListener('click', () => {
        console.log('[ANALYZER] Download HTML clicked, report blob:', analysisResults.report);
        if (analysisResults.report) {
            const prefix = `storyline${selectedStoryline}`;
            const timestamp = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
            downloadBlob(analysisResults.report, `${prefix}_report_${timestamp}.html`);
            showToast('Descargando informe HTML...', 'success');
        } else {
            console.warn('[ANALYZER] Report blob is null/undefined');
            showToast('Informe no disponible', 'error');
        }
    });

    document.getElementById('download-zip-btn').addEventListener('click', () => {
        if (analysisResults.zip) {
            const prefix = `storyline${selectedStoryline}`;
            const timestamp = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
            downloadBlob(analysisResults.zip, `${prefix}_outputs_${timestamp}.zip`);
            showToast('Downloading all outputs...', 'success');
        } else {
            showToast('ZIP file not available', 'error');
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
        console.log('[ANALYZER] downloadBlob called:', filename, 'size:', blob?.size);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        // Delay cleanup to ensure download starts
        setTimeout(() => {
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }, 1000);
    }

    function base64ToBlob(base64, mimeType) {
        const byteCharacters = atob(base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        return new Blob([byteArray], { type: mimeType });
    }
});
