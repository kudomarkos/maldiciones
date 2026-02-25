document.addEventListener("DOMContentLoaded", function () {
    const mainContent = document.getElementById('mainContent');







        // Crear la tabla básica
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const tbody = document.createElement('tbody');

        // Crear la fila de encabezado
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = `
            <th>IMAGEN</th>
            <th>Serie/Personaje</th>
            <th>Título</th>

        `;
        thead.appendChild(headerRow);
        table.appendChild(thead);
        table.appendChild(tbody);
        mainContent.appendChild(table);

        loadTableData("", tbody); // Cargar los datos en la tabla

});

// Función para formatear valores de la columna TT
function formatCerosCuatro(value) {
    if (typeof value === "number") {
        return value.toString().padStart(4, '0');
    } else {
        return value;
    }
}

// Función para formatear valores de la columna TT
function formatCerosTres(value) {
    if (typeof value === "number") {
        return value.toString().padStart(3, '0');
    } else {
        return value;
    }
}

// Función para formatear valores de la columna TT
function formatCeros(value) {
    if (typeof value === "number") {
        return value.toString().padStart(2, '0');
    } else {
        return value;
    }
}

// Función para cargar datos en la tabla
function loadTableData(year, tbody) {
    const fileName = `ddtextra.json`; // Nombre del archivo JSON

    fetch(`https://kudomarkos.github.io/maldiciones/COMPARTIDOS/${fileName}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(item => {
                const tr = document.createElement('tr');

                // Crear las celdas según la definición de columnas
                const imagen = `ddtep03_extra${formatCerosTres(item.numExtra)}_${formatCerosTres(item.pagina)}.jpg`;
                tr.innerHTML = `
                    <td>${imagen}</td>
                    <td>${item.personaje ?? ""}</td>
                    <td>${item.titulo ?? ""}</td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(error => console.error(`Error al cargar el JSON ${year}:`, error));
}
