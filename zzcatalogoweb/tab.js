document.addEventListener("DOMContentLoaded", function () {
    const mainContent = document.getElementById('mainContent');
    const loadingOverlay = document.getElementById('loadingOverlay');

    const totalYears = 1993 - 1948 + 1; // Total de años a cargar
    const fetchPromises = []; // Array para almacenar las promesas

    for (let year = 1948; year <= 1993; year++) {
        const header = document.createElement('h2');
        header.textContent = year;
        mainContent.appendChild(header);

        const paragraph = document.createElement('p');
        paragraph.textContent = '...';
        mainContent.appendChild(paragraph);

        const tableDiv = document.createElement('div');
        tableDiv.id = `table${year}`;
        mainContent.appendChild(tableDiv);

        // Crear una promesa para cada solicitud de JSON
        const fileName = `ZZ${year}.json`; // Crear el nombre del archivo dinámico
        const fetchPromise = fetch(`https://kudomarkos.github.io/maldiciones/output/${fileName}`)
            .then(response => response.json())
            .then(data => {
                initTabulator(data, tableDiv.id, ${year}); // Inicializa Tabulator en la tabla correspondiente
            })
            .catch(error => console.error(`Error al cargar el JSON ${year}:`, error));

        fetchPromises.push(fetchPromise); // Agrega la promesa al array
    }

    // Esperar a que todas las promesas se resuelvan
    Promise.all(fetchPromises).then(() => {
        loadingOverlay.style.display = 'none'; // Oculta el overlay cuando todas las tablas están cargadas
    });
});
// Función para formatear valores de la columna TT
function formatCeros(value) {
    if (typeof value === "number") {
        return value.toString().padStart(2, '0');
    } else {
        return value;
    }
}

// Función para obtener la configuración de columnas
function getColumnDefinitions(anio) {
    return [
        {
            title: "FECHA",
            formatter: function (cell) {
                const datos = cell.getData();
                return `${anio}.${formatCeros(datos.MES)}.${formatCeros(datos.DIA)}`;
            },
            hozAlign: "center", width:80
        },
        {
            title: "PUBLICACIÓN",
            field: "P", width:120
        },
        {
            title: "TÍTULO - DIÁLOGO",
            formatter: function (cell) {
                const data = cell.getData();
                return `<b>${data.T}</b> - <i style="color: LightSlateGray;">${data.D}</i>`;
            }
        },
        {title: "PP", field: "PP",hozAlign: "center", width:20},
        {title: "TT", field: "TT",hozAlign: "center", width:20},
        {title: "REVISTAS", field: "R"},
        {title: "COLECCIONES", field: "C"}
        // Otras columnas...
    ];
}

// Función para inicializar el Tabulator para diferentes JSON y tablas
function initTabulator(data, tableId, anio) {
    new Tabulator(`#${tableId}`, {
        data: data, // Datos de la fuente
        layout: "fitColumns", // Ajusta las columnas al ancho del contenedor
        columns: getColumnDefinitions(anio), // Llama a la función para obtener columnas
    });
}
