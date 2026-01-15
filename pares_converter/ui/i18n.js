/**
 * Internationalization (i18n) System for PARES Application
 * Supports English (en) and Spanish (es)
 * Default: Spanish
 */

const translations = {
    // ===== COMMON =====
    'app.title': {
        en: 'PARES Excel Converter & Analyzer',
        es: 'PARES Conversor y Analizador Excel'
    },
    'app.subtitle': {
        en: 'Transform and analyze PARES workshop data',
        es: 'Transformar y analizar datos de talleres PARES'
    },
    'app.footer': {
        en: 'PARES Methodology | Nature-Based Solutions',
        es: 'Metodología PARES | Soluciones Basadas en la Naturaleza'
    },

    // ===== NAVIGATION =====
    'nav.converter': {
        en: 'Converter',
        es: 'Conversor'
    },
    'nav.analyzer': {
        en: 'Analyzer',
        es: 'Analizador'
    },

    // ===== CONVERTER PAGE =====
    'converter.title': {
        en: 'Excel Converter',
        es: 'Conversor Excel'
    },
    'converter.subtitle': {
        en: 'Transform raw workshop data into analysis-ready format',
        es: 'Transforma datos de taller en formato listo para análisis'
    },
    'converter.upload.title': {
        en: 'Upload Raw Database',
        es: 'Cargar Base de Datos'
    },
    'converter.upload.hint': {
        en: 'Drag & drop your Excel file or click to browse',
        es: 'Arrastra y suelta tu archivo Excel o haz clic para buscar'
    },
    'converter.upload.format': {
        en: 'Accepts .xlsx files only',
        es: 'Solo acepta archivos .xlsx'
    },
    'converter.org.label': {
        en: 'Organization',
        es: 'Organización'
    },
    'converter.date.label': {
        en: 'Workshop Date',
        es: 'Fecha del Taller'
    },
    'converter.button.convert': {
        en: '🔄 Convert Now',
        es: '🔄 Convertir Ahora'
    },
    'converter.button.converting': {
        en: 'Converting...',
        es: 'Convirtiendo...'
    },
    'converter.success': {
        en: 'Conversion Complete!',
        es: '¡Conversión Completada!'
    },
    'converter.download': {
        en: '📥 Download Converted File',
        es: '📥 Descargar Archivo Convertido'
    },

    // ===== ANALYZER PAGE =====
    'analyzer.title': {
        en: 'PARES Analyzer',
        es: 'Analizador PARES'
    },
    'analyzer.subtitle': {
        en: 'Deep insights from your converted data',
        es: 'Análisis profundo de tus datos convertidos'
    },
    'analyzer.step1.title': {
        en: 'Select Storyline',
        es: 'Seleccionar Storyline'
    },
    'analyzer.step1.subtitle': {
        en: 'Choose the analysis perspective',
        es: 'Elige la perspectiva de análisis'
    },
    'analyzer.step2.title': {
        en: 'Upload & Configure',
        es: 'Cargar y Configurar'
    },
    'analyzer.upload.title': {
        en: 'Upload Analysis-Ready Workbook',
        es: 'Cargar Libro de Trabajo Listo para Análisis'
    },
    'analyzer.upload.hint': {
        en: 'Must contain LOOKUP_* and TIDY_* sheets',
        es: 'Debe contener hojas LOOKUP_* y TIDY_*'
    },
    'analyzer.config.topn': {
        en: 'Top N Rankings',
        es: 'Top N Rankings'
    },
    'analyzer.config.figures': {
        en: 'Generate Visualizations',
        es: 'Generar Visualizaciones'
    },
    'analyzer.config.report': {
        en: 'Generate HTML Report',
        es: 'Generar Reporte HTML'
    },
    'analyzer.button.run': {
        en: '🚀 Run Analysis',
        es: '🚀 Ejecutar Análisis'
    },
    'analyzer.button.running': {
        en: 'Analyzing...',
        es: 'Analizando...'
    },
    'analyzer.progress.starting': {
        en: 'Starting analysis...',
        es: 'Iniciando análisis...'
    },
    'analyzer.progress.loading': {
        en: 'Loading tables...',
        es: 'Cargando tablas...'
    },
    'analyzer.progress.computing': {
        en: 'Computing metrics...',
        es: 'Calculando métricas...'
    },
    'analyzer.progress.generating': {
        en: 'Generating outputs...',
        es: 'Generando resultados...'
    },

    // ===== STORYLINES =====
    'storyline.1.title': {
        en: 'Where to Act First?',
        es: '¿Dónde Actuar Primero?'
    },
    'storyline.1.desc': {
        en: 'Priority analysis for SbN/adaptation actions',
        es: 'Análisis de priorización para acciones SbN/adaptación'
    },
    'storyline.2.title': {
        en: 'Ecosystem-Service Lifelines',
        es: 'Líneas de Vida Ecosistema-Servicio'
    },
    'storyline.2.desc': {
        en: 'Critical services and ecosystem leverage points',
        es: 'Servicios críticos y puntos de apalancamiento ecosistémico'
    },
    'storyline.3.title': {
        en: 'Equity & Vulnerability',
        es: 'Equidad y Vulnerabilidad'
    },
    'storyline.3.desc': {
        en: 'Differentiated impacts and inclusion analysis',
        es: 'Impactos diferenciados y análisis de inclusión'
    },
    'storyline.4.title': {
        en: 'Feasibility & Governance',
        es: 'Factibilidad y Gobernanza'
    },
    'storyline.4.desc': {
        en: 'Actor networks and conflict dynamics',
        es: 'Redes de actores y dinámicas de conflicto'
    },
    'storyline.5.title': {
        en: 'SbN Portfolio Design',
        es: 'Diseño de Portafolio SbN'
    },
    'storyline.5.desc': {
        en: 'Synthesize findings into recommendations',
        es: 'Sintetizar hallazgos en recomendaciones'
    },
    'storyline.status.available': {
        en: 'Available',
        es: 'Disponible'
    },
    'storyline.status.coming': {
        en: 'Coming Soon',
        es: 'Próximamente'
    },

    // ===== VALIDATION =====
    'validation.validating': {
        en: 'Validating file...',
        es: 'Validando archivo...'
    },
    'validation.ready': {
        en: 'Ready to Analyze!',
        es: '¡Listo para Analizar!'
    },
    'validation.ready.desc': {
        en: 'All required sheets found.',
        es: 'Todas las hojas requeridas encontradas.'
    },
    'validation.warning': {
        en: 'Ready with Warnings',
        es: 'Listo con Advertencias'
    },
    'validation.missing': {
        en: 'Missing Required Sheets',
        es: 'Faltan Hojas Requeridas'
    },
    'validation.raw': {
        en: 'Raw Database Detected',
        es: 'Base de Datos Sin Convertir'
    },
    'validation.raw.desc': {
        en: 'This appears to be a raw database file. Please convert it first using the Converter page.',
        es: 'Este parece ser un archivo de base de datos sin convertir. Por favor conviértelo primero en la página del Conversor.'
    },
    'validation.goto.converter': {
        en: 'Go to Converter →',
        es: 'Ir al Conversor →'
    },

    // ===== RESULTS =====
    'results.title': {
        en: 'Analysis Complete!',
        es: '¡Análisis Completado!'
    },
    'results.tables': {
        en: 'Tables Generated',
        es: 'Tablas Generadas'
    },
    'results.figures': {
        en: 'Figures Created',
        es: 'Figuras Creadas'
    },
    'results.duration': {
        en: 'Duration',
        es: 'Duración'
    },
    'results.download.xlsx': {
        en: '📊 Download Excel',
        es: '📊 Descargar Excel'
    },
    'results.download.report': {
        en: '📄 Download Report',
        es: '📄 Descargar Reporte'
    },
    'results.download.all': {
        en: '📦 Download All',
        es: '📦 Descargar Todo'
    },

    // ===== TOASTS =====
    'toast.file.selected': {
        en: 'File selected:',
        es: 'Archivo seleccionado:'
    },
    'toast.file.invalid': {
        en: 'Please upload an Excel file (.xlsx)',
        es: 'Por favor sube un archivo Excel (.xlsx)'
    },
    'toast.error.generic': {
        en: 'An error occurred',
        es: 'Ocurrió un error'
    },
    'toast.download.starting': {
        en: 'Downloading...',
        es: 'Descargando...'
    },
    'toast.storyline.coming': {
        en: 'This storyline is coming soon!',
        es: '¡Este storyline estará disponible pronto!'
    },

    // ===== LANGUAGE =====
    'lang.en': {
        en: 'English',
        es: 'Inglés'
    },
    'lang.es': {
        en: 'Spanish',
        es: 'Español'
    }
};

// Current language (default: Spanish)
let currentLang = localStorage.getItem('pares_lang') || 'es';

/**
 * Get translated string for a key
 * @param {string} key - Translation key
 * @param {object} params - Optional parameters for interpolation
 * @returns {string} Translated string
 */
function t(key, params = {}) {
    const entry = translations[key];
    if (!entry) {
        console.warn(`Missing translation: ${key}`);
        return key;
    }
    let text = entry[currentLang] || entry['en'] || key;

    // Simple interpolation: {name} -> value
    Object.keys(params).forEach(param => {
        text = text.replace(new RegExp(`{${param}}`, 'g'), params[param]);
    });

    return text;
}

/**
 * Get current language code
 * @returns {string} 'en' or 'es'
 */
function getLang() {
    return currentLang;
}

/**
 * Set language and update UI
 * @param {string} lang - 'en' or 'es'
 */
function setLang(lang) {
    if (lang !== 'en' && lang !== 'es') return;
    currentLang = lang;
    localStorage.setItem('pares_lang', lang);
    updateAllTranslations();

    // Update toggle buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });
}

/**
 * Update all elements with data-i18n attribute
 */
function updateAllTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        el.textContent = t(key);
    });

    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.dataset.i18nPlaceholder;
        el.placeholder = t(key);
    });

    // Update titles
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.dataset.i18nTitle;
        el.title = t(key);
    });
}

/**
 * Initialize language toggle buttons
 */
function initLangToggle() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', () => setLang(btn.dataset.lang));
        btn.classList.toggle('active', btn.dataset.lang === currentLang);
    });

    // Initial translation
    updateAllTranslations();
}

// Export for use in other scripts
window.i18n = { t, getLang, setLang, initLangToggle, updateAllTranslations };
