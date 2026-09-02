# Tablero de Seguros &bull; Mercado Asegurador Argentino

Tablero de control analítico, monitoreo financiero y rankings del mercado asegurador de la República Argentina, basado en los datos oficiales de la **Superintendencia de Seguros de la Nación (SSN)** y diseñado bajo los lineamientos institucionales del **Brandbook de La Segunda Seguros**.

---

## 🚀 Características Principales

### 1. Cobertura Integral del Mercado (Basado en "Valores Financieros")
* **Primas Emitidas**: Total del mercado, Seguros Patrimoniales & ART y Seguros de Personas. Desglose detallado por ramos, cuotas de mercado y variaciones interanuales reales ajustadas por inflación.
* **Evolución Mensual**: Series históricas a valores corrientes y constantes (con deflactor IPC).
* **12 Rankings Oficiales SSN**:
  1. Grupos Aseguradores
  2. Total Mercado
  3. Patrimoniales Total
  4. Personas Total
  5. Automotores y Motos
  6. Riesgos del Trabajo (ART)
  7. Agro y Granizo
  8. Otros Patrimoniales
  9. Accidentes Personales
  10. Seguros de Retiro
  11. Seguros de Vida
  12. Seguros de Sepelio
* **Estados Contables y Balances SSN**: Activos, Inversiones, Disponibilidades, Compromisos Técnicos, Patrimonio Neto y Resultado del Ejercicio para más de 180 entidades.
* **Grupo Asegurador La Segunda**: Desglose y desempeño de *La Segunda Generales*, *La Segunda ART*, *La Segunda Personas* y *La Segunda Retiro*.
* **Seguros de Personas**: Estadísticas del boletín estadístico SSN (Vida Individual, Colectivo, AP, Salud y Sepelio).
* **Seguros de Retiro**: Compromisos técnicos, reservas matemáticas, primas y asegurados.

### 2. Módulos de Alto Valor Agregado
* **Inversiones y Portafolio SSN**: Distribución de más de $16.4 Billones administrados por el mercado (Títulos Públicos, FCIs, ONs, Plazo Fijo, Acciones, Inmuebles) y apertura por moneda/ajuste (ARS Tasa Fija, USD / Dólar Linked, CER).
* **Solvencia & KPIs Técnicos**: Ratios combinados estimados, siniestralidad neta, cobertura de pasivos técnicos (Art. 35) y apalancamiento patrimonial.
* **Comparador Cara a Cara (Head-to-Head)**: Herramienta interactiva para comparar dos entidades aseguradoras en primas, participación, ramos líderes y patrimonio neto.
* **Buscador en Tiempo Real y Exportación**: Filtrado instantáneo por nombre y exportación de datos a formato CSV/Excel.

### 3. Identidad Visual: Brandbook La Segunda
* **Tipografía**: Google Font `Sora` y `JetBrains Mono`.
* **Colores Institucionales**:
  * Rojo Seguro: `#e20039`
  * Rojos Análogos: `#b91f38`, `#f42c4b`, `#ff4c60`
  * Complementarios: Oro `#f8cc59`, Esmeralda `#3ac792`, Azul `#4183ca`, Coral `#ff593e`
* **Modo Oscuro & Claro**: Selector con persistencia local y contraste ultra-alto.

---

## 📂 Estructura del Proyecto

```
Tablero de Seguros/
├── data/
│   ├── insurance_dataset.json          # Base de datos JSON unificada
│   └── insurance_data.js               # Dataset ejecutable directamente en el cliente
├── src/
│   ├── scrapers/
│   │   ├── ssn_rankings_fetcher.py     # Extractor de rankings SSN
│   │   ├── ssn_balances_fetcher.py     # Extractor de balances SSN
│   │   ├── ssn_retiro_fetcher.py       # Extractor de retiro SSN
│   │   ├── ssn_personas_fetcher.py     # Extractor de personas SSN
│   │   └── ssn_inversiones_fetcher.py  # Extractor de inversiones SSN
│   └── utils/
│       └── formatters.py               # Formateadores monetarios y estadísticos
├── actualizar_tablero.py               # Actualizador maestro de datos SSN
├── deploy_to_github.py                 # Despliegue automático a GitHub Pages
├── index.html                          # Dashboard SPA interactivo
└── LaSegunda_Brandbook_Version_Reducida.pdf # Manual de marca oficial
```

---

## 🛠️ Instrucciones de Uso

### Actualización de Datos:
```bash
python actualizar_tablero.py
```

### Visualización Local:
Abrir directamente `index.html` en cualquier navegador web o mediante un servidor local:
```bash
python -m http.server 8000
```

### Despliegue:
```bash
python deploy_to_github.py
```
