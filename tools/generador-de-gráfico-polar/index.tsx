// Globals from CDN scripts
declare var Chart: any;
declare var Papa: any;

interface CsvRow {
    Medio_de_vida?: string;
    grupo_indicador?: string;
    average_valor?: string;
    dimension?: string;
}

const initialCsvData = `Medio_de_vida,grupo_indicador,average_valor,dimension
Ganadería,Agencia,3.67,action
Granos Básicos,Agencia,3.00,action
Granos Básicos ,Agencia,1.67,action
Pesca,Agencia,4.00,action
Ganadería,Comunicaciones,5.00,innovation
Granos Básicos,Comunicaciones,4.00,innovation
Granos Básicos ,Comunicaciones,4.00,innovation
Pesca,Comunicaciones,5.00,innovation
Ganadería,Confianza,4.33,innovation
Granos Básicos,Confianza,2.67,innovation
Granos Básicos ,Confianza,1.33,innovation
Pesca,Confianza,2.67,innovation
Ganadería,Disposición al cambio,4.00,innovation
Granos Básicos,Disposición al cambio,4.33,innovation
Granos Básicos ,Disposición al cambio,3.00,innovation
Pesca,Disposición al cambio,3.67,innovation
Ganadería,Educación,4.67,basic needs
Granos Básicos,Educación,4.67,basic needs
Granos Básicos ,Educación,3.33,basic needs
Pesca,Educación,4.00,basic needs
Ganadería,Energía doméstica,4.33,basic needs
Granos Básicos,Energía doméstica,3.67,basic needs
Granos Básicos ,Energía doméstica,4.00,basic needs
Pesca,Energía doméstica,4.67,basic needs
Ganadería,Equidad NB,3.00,basic needs
Granos Básicos,Equidad NB,1.00,basic needs
Granos Básicos ,Equidad NB,1.00,basic needs
Pesca,Equidad NB,1.00,basic needs
Ganadería,Equidad_AC,3.00,action
Granos Básicos,Equidad_AC,2.00,action
Granos Básicos ,Equidad_AC,3.50,action
Pesca,Equidad_AC,4.00,action
Ganadería,Equidad_INN,5.00,innovation
Granos Básicos,Equidad_INN,0.00,innovation
Granos Básicos ,Equidad_INN,3.00,innovation
Pesca,Equidad_INN,2.00,innovation
Ganadería,Equidad_NB,4.00,basic needs
Granos Básicos,Equidad_NB,1.00,basic needs
Granos Básicos ,Equidad_NB,3.00,basic needs
Pesca,Equidad_NB,4.00,basic needs
Ganadería,Extensión,4.33,innovation
Granos Básicos,Extensión,1.67,innovation
Granos Básicos ,Extensión,1.33,innovation
Pesca,Extensión,4.00,innovation
Ganadería,Insumos,2.50,action
Granos Básicos,Insumos,2.25,action
Granos Básicos ,Insumos,2.50,action
Pesca,Insumos,2.88,action
Ganadería,Organización,4.00,innovation
Granos Básicos,Organización,2.00,innovation
Granos Básicos ,Organización,4.00,innovation
Pesca,Organización,3.50,innovation
Ganadería,Seguridad alimentaria,4.00,basic needs
Granos Básicos,Seguridad alimentaria,5.00,basic needs
Granos Básicos ,Seguridad alimentaria,5.00,basic needs
Pesca,Seguridad alimentaria,5.00,basic needs
Ganadería,Seguridad comunitaria,3.00,basic needs
Granos Básicos,Seguridad comunitaria,5.00,basic needs
Granos Básicos ,Seguridad comunitaria,3.00,basic needs
Pesca,Seguridad comunitaria,1.00,basic needs
Ganadería,Seguridad económica,1.00,basic needs
Granos Básicos,Seguridad económica,3.00,basic needs
Granos Básicos ,Seguridad económica,0.00,basic needs
Pesca,Seguridad económica,1.00,basic needs
Ganadería,Seguridad en salud,4.33,basic needs
Granos Básicos,Seguridad en salud,2.00,basic needs
Granos Básicos ,Seguridad en salud,2.67,basic needs
Pesca,Seguridad en salud,2.67,basic needs
Ganadería,Seguridad personal,5.00,basic needs
Granos Básicos,Seguridad personal,5.00,basic needs
Granos Básicos ,Seguridad personal,3.67,basic needs
Pesca,Seguridad personal,3.33,basic needs
Ganadería,Seguridad política,2.50,basic needs
Granos Básicos,Seguridad política,2.50,basic needs
Granos Básicos ,Seguridad política,3.00,basic needs
Pesca,Seguridad política,3.00,basic needs
Ganadería,Valor añadido y comercio,2.80,action
Granos Básicos,Valor añadido y comercio,1.80,action
Granos Básicos ,Valor añadido y comercio,1.40,action
Pesca,Valor añadido y comercio,2.20,action
Ganadería,Vivienda,4.00,basic needs
Granos Básicos,Vivienda,1.33,basic needs
Granos Básicos ,Vivienda,2.33,basic needs
Pesca,Vivienda,2.67,basic needs`;

// A predefined list of aesthetically pleasing colors for dimensions.
const PREDEFINED_COLORS = [
    'rgba(40, 167, 69, 0.7)',    // Green
    'rgba(253, 126, 20, 0.7)',   // Orange
    'rgba(23, 162, 184, 0.7)',    // Teal
    'rgba(0, 123, 255, 0.7)',   // Blue
    'rgba(220, 53, 69, 0.7)',    // Red
    'rgba(255, 193, 7, 0.7)',     // Yellow
    'rgba(108, 117, 125, 0.7)',  // Gray
];

let chartInstance: any = null;

/**
 * Formats a date string into a more readable format.
 * @param {string} dateString - The date string (e.g., 'YYYY-MM-DD').
 * @returns {string} The formatted date string.
 */
function formatDate(dateString: string): string {
    if (!dateString) return '';
    // Adding T00:00:00 ensures the date is parsed in the local timezone, avoiding off-by-one day errors.
    const date = new Date(`${dateString}T00:00:00`);
    const options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('es-ES', options);
}


/**
 * Generates a color map for a given list of dimensions.
 * @param {string[]} dimensions - An array of unique dimension names.
 * @returns {{ [key: string]: string }} A map of dimension names to color strings.
 */
function generateDimensionColors(dimensions: string[]): { [key: string]: string } {
    const colorMap: { [key: string]: string } = {};
    dimensions.forEach((dim, index) => {
        colorMap[dim] = PREDEFINED_COLORS[index % PREDEFINED_COLORS.length];
    });
    return colorMap;
}


/**
 * Processes raw CSV data into a format usable by Chart.js.
 * @param {Array<Object>} data - Array of objects from Papaparse.
 * @param {Object} dimensionColorMap - A map of dimension names to color strings.
 * @returns {Object} Chart.js data object.
 */
function processData(data: CsvRow[], dimensionColorMap: { [key: string]: string }) {
    const groups: { [key: string]: { values: number[]; dimension: string } } = {};
    data.forEach(row => {
        if (!row.grupo_indicador || !row.average_valor) return;
        
        const indicator = row.grupo_indicador.trim().replace(/\s+/g, ' ');
        const value = parseFloat(row.average_valor);
        const dimension = row.dimension?.trim();

        if (isNaN(value) || !dimension) return;
        
        if (!groups[indicator]) {
            groups[indicator] = {
                values: [],
                dimension: dimension
            };
        }
        groups[indicator].values.push(value);
    });

    const processed = Object.keys(groups).map(indicator => {
        const group = groups[indicator];
        const sum = group.values.reduce((a, b) => a + b, 0);
        const avg = sum / group.values.length;
        return {
            label: indicator,
            value: avg,
            dimension: group.dimension
        };
    });

    const dimensionOrder = Object.keys(dimensionColorMap);
    processed.sort((a, b) => dimensionOrder.indexOf(a.dimension) - dimensionOrder.indexOf(b.dimension));
    
    const dimensionCounts: { [key: string]: number } = {};
    const dimensionIndices: { [key: string]: number } = {};

    dimensionOrder.forEach(dim => {
        dimensionCounts[dim] = processed.filter(d => d.dimension === dim).length;
        dimensionIndices[dim] = 0;
    });

    const backgroundColors = processed.map(d => {
        const baseColor = dimensionColorMap[d.dimension];
        if (!baseColor) {
            return 'rgba(108, 117, 125, 0.7)'; // fallback
        }

        const total = dimensionCounts[d.dimension];
        const currentIndex = dimensionIndices[d.dimension];
        
        const factor = 1.25 - (currentIndex / (total - 1 || 1)) * 0.5;

        const rgba = baseColor.replace(/[^\d,]/g, '').split(',').map(Number);
        const r = Math.min(255, Math.round(rgba[0] * factor));
        const g = Math.min(255, Math.round(rgba[1] * factor));
        const b = Math.min(255, Math.round(rgba[2] * factor));
        const a = rgba[3];

        dimensionIndices[d.dimension]++;

        return `rgba(${r}, ${g}, ${b}, ${a})`;
    });

    return {
        labels: processed.map(d => `${d.label} (${d.value.toFixed(2)})`),
        datasets: [{
            label: 'Valor Promedio',
            data: processed.map(d => d.value),
            backgroundColor: backgroundColors,
        }]
    };
}

/**
 * Renders the polar area chart on the canvas.
 * @param {Object} data - Chart.js data object from processData.
 * @param {string} orgName - The name of the organization.
 * @param {string} dataDate - The date of the data survey.
 */
function renderChart(data: any, orgName: string, dataDate: string) {
    const ctx = (document.getElementById('polar-chart') as HTMLCanvasElement).getContext('2d');
    if (!ctx) return;
    
    if (chartInstance) {
        chartInstance.destroy();
    }

    const isMobile = window.innerWidth < 768;

    const whiteCenterPlugin = {
        id: 'whiteCenter',
        afterDraw: (chart: any) => {
            const { ctx } = chart;
            const rScale = chart.scales.r;

            if (rScale && rScale.drawingArea > 0) {
                const centerX = rScale.xCenter;
                const centerY = rScale.yCenter;
                
                const valueToCover = 0.5;
                const scaleRange = rScale.max - rScale.min;
                
                if (scaleRange > 0) {
                    const valueFraction = (valueToCover - rScale.min) / scaleRange;
                    const radius = rScale.drawingArea * valueFraction;

                    if (radius > 0) {
                        ctx.save();
                        ctx.beginPath();
                        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
                        ctx.fillStyle = '#FFFFFF';
                        ctx.fill();
                        ctx.restore();
                    }
                }
            }
        }
    };

    chartInstance = new Chart(ctx, {
        type: 'polarArea',
        data: data,
        plugins: [whiteCenterPlugin],
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: orgName || 'Generador de Gráfico Polar',
                    font: { size: isMobile ? 16 : 20, weight: 'bold' },
                    padding: { top: 10, bottom: 5 },
                    color: '#333'
                },
                subtitle: {
                    display: !!dataDate,
                    text: dataDate ? `Fecha de levantamiento: ${formatDate(dataDate)}` : '',
                    font: { size: isMobile ? 12 : 14 },
                    padding: { bottom: 20 },
                    color: '#666'
                },
                legend: {
                   display: false,
                },
                tooltip: {
                    callbacks: {
                        label: function(context: any) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.r !== null) {
                                label += context.parsed.r.toFixed(2);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                r: {
                    min: 0,
                    max: 5,
                    grid: {
                        lineWidth: 3,
                        color: '#FFFFFF',
                        z: 1
                    },
                    pointLabels: {
                        display: true,
                        centerPointLabels: true,
                        font: {
                            size: isMobile ? 9 : 11
                        }
                    },
                    ticks: {
                        display: false,
                        z: 1,
                        backdropColor: 'rgba(0,0,0,0)'
                    }
                }
            },
            elements: {
                arc: {
                    borderColor: '#fff',
                    borderWidth: 3
                }
            }
        }
    });
}

/**
 * Renders a custom HTML legend based on dynamic dimensions.
 * @param {Object} dimensionColorMap - Map of dimension names to color strings.
 */
function renderCustomLegend(dimensionColorMap: { [key: string]: string }) {
    const legendContainer = document.getElementById('custom-legend');
    if (!legendContainer) return;

    const legendItemsHTML = Object.entries(dimensionColorMap).map(([dimension, color]) => {
        // Capitalize the first letter of each word for the label.
        const label = dimension.replace(/\b\w/g, l => l.toUpperCase());
        return `
            <div class="legend-item">
                <div class="legend-color-box" style="background-color: ${color};"></div>
                <span>${label}</span>
            </div>
        `;
    }).join('');

    legendContainer.innerHTML = legendItemsHTML;
}

/**
 * Main function to update the chart and legend from parsed CSV data.
 * @param {Array<Object>} csvData - Array of data objects from Papaparse.
 */
function updateAppWithData(csvData: CsvRow[]) {
    const errorElement = document.getElementById('error-message');
    if (!errorElement) return;
    try {
        const validData = csvData.filter(row => row.dimension && row.dimension.trim());
        if (validData.length === 0) {
            errorElement.textContent = 'El archivo CSV no contiene datos válidos o le falta la columna "dimension".';
            if (chartInstance) {
                chartInstance.destroy();
                chartInstance = null;
            }
            const legendContainer = document.getElementById('custom-legend');
            if (legendContainer) {
              legendContainer.innerHTML = '';
            }
            return;
        }

        const uniqueDimensions = [...new Set(validData.map(row => row.dimension!.trim()))].sort();
        const dimensionColorMap = generateDimensionColors(uniqueDimensions);
        const chartData = processData(validData, dimensionColorMap);
        
        const orgName = (document.getElementById('org-name') as HTMLInputElement)?.value;
        const dataDate = (document.getElementById('data-date') as HTMLInputElement)?.value;
        
        renderChart(chartData, orgName, dataDate);
        renderCustomLegend(dimensionColorMap);

        errorElement.textContent = ''; // Clear previous errors
    } catch (e) {
        errorElement.textContent = 'Ocurrió un error al procesar los datos.';
        console.error(e);
    }
}


/**
 * Handles the file input change event.
 * @param {Event} event
 */
function handleFileChange(event: Event) {
    const errorElement = document.getElementById('error-message');
    if(!errorElement) return;

    const file = (event.target as HTMLInputElement).files?.[0];

    if (!file) {
      return;
    }
    
    if (file.type !== 'text/csv' && !file.name.toLowerCase().endsWith('.csv')) {
        errorElement.textContent = 'Por favor, suba un archivo CSV válido.';
        return;
    }
    
    errorElement.textContent = '';

    Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results: { data: CsvRow[], errors: any[] }) => {
            if (results.errors.length) {
                errorElement.textContent = 'Error al analizar el archivo CSV.';
                console.error(results.errors);
            } else {
                updateAppWithData(results.data);
            }
        },
        error: (err: any) => {
            errorElement.textContent = 'Error al leer el archivo.';
            console.error(err);
        }
    });
}

/**
 * Handles the download chart button click event.
 */
function handleDownload() {
    if (!chartInstance) {
        console.error('Chart instance not found for download.');
        return;
    }

    const originalCanvas = chartInstance.canvas;
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = originalCanvas.width;
    tempCanvas.height = originalCanvas.height;

    const ctx = tempCanvas.getContext('2d');
    if(!ctx) return;

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
    
    ctx.drawImage(originalCanvas, 0, 0);

    const link = document.createElement('a');
    link.href = tempCanvas.toDataURL('image/png');
    link.download = 'grafico-polar.png';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}


/**
 * Initializes the application.
 */
function main() {
    const fileInput = document.getElementById('file-input');
    const downloadBtn = document.getElementById('download-btn');
    const orgInput = document.getElementById('org-name');
    const dateInput = document.getElementById('data-date');

    if (fileInput) fileInput.addEventListener('change', handleFileChange);
    if (downloadBtn) downloadBtn.addEventListener('click', handleDownload);

    const handleMetadataChange = () => {
        if (!chartInstance) return;

        const orgName = (orgInput as HTMLInputElement)?.value || 'Generador de Gráfico Polar';
        const dataDate = (dateInput as HTMLInputElement)?.value;

        chartInstance.options.plugins.title.text = orgName;
        chartInstance.options.plugins.subtitle.display = !!dataDate;
        chartInstance.options.plugins.subtitle.text = dataDate ? `Fecha de levantamiento: ${formatDate(dataDate)}` : '';
        chartInstance.update();
    };

    if (orgInput) orgInput.addEventListener('input', handleMetadataChange);
    if (dateInput) dateInput.addEventListener('change', handleMetadataChange);

    // Render the initial chart with default data
    Papa.parse(initialCsvData, {
        header: true,
        skipEmptyLines: true,
        complete: (results: { data: CsvRow[] }) => {
            updateAppWithData(results.data);
        }
    });
}

// Run the app once the DOM is fully loaded
document.addEventListener('DOMContentLoaded', main);