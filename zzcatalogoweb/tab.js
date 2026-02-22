document.addEventListener("DOMContentLoaded", function () {
    const mainContent = document.getElementById('mainContent');
    const menu = document.getElementById('menu');

    for (let year = 1948; year <= 1993; year++) {
        const header = document.createElement('h1');
        header.id = year;  // Establece el id como el año actual

        const yearText = document.createTextNode(year); // Texto del año
        header.appendChild(yearText); // Añade el texto

        const anchor = document.createElement('a'); // Crea un enlace para la flecha
        anchor.href = "#"; // Vuelve al inicio de la página
        anchor.innerHTML = "⇈"; // Flecha hacia arriba
        // Se eliminaron los estilos en línea

        header.appendChild(anchor); // Añade el enlace al h1
        mainContent.appendChild(header); // Añade el h1 al contenido principal

        const link = document.createElement('a'); // Nueva instancia en cada iteración para el menú
        link.href = `#${year}`;
        link.textContent = year;

        // Añadir el enlace al menú
        menu.appendChild(link);

        // Crear la tabla básica
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const tbody = document.createElement('tbody');

        // Crear la fila de encabezado
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = `
            <th style="text-align: center;">FECHA</th>
            <th style="text-align: center;">PUBLICACIÓN</th>
            <th>TÍTULO - DIÁLOGO</th>
            <th style="text-align: center;">PP</th>
            <th style="text-align: center;">TT</th>
            <th>REVISTAS</th>
            <th>COLECCIONES</th>
        `;
        thead.appendChild(headerRow);
        table.appendChild(thead);
        table.appendChild(tbody);
        mainContent.appendChild(table);

        loadTableData(year, tbody); // Cargar los datos en la tabla
    }
});

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
    const fileName = `ZZ${year}.json`; // Nombre del archivo JSON

    fetch(`https://kudomarkos.github.io/maldiciones/zzcatalogoweb/output/${fileName}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(item => {
                const tr = document.createElement('tr');

                // Crear las celdas según la definición de columnas
                const fecha = `${year}.${formatCeros(item.MES)}.${formatCeros(item.DIA)}`;
                tr.innerHTML = `
                    <td style="text-align: center;">${fecha}</td>
                    <td>${item.P}</td>
                    <td title="${item.T} - ${item.D}"><b>${item.T}</b> - <i style="color: LightSlateGray;">${item.D}</i></td>
                    <td style="text-align: center;">${item.PP}</td>
                    <td style="text-align: center;">${item.TT}</td>
                    <td>${item.R}</td>
                    <td>${item.C}</td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(error => console.error(`Error al cargar el JSON ${year}:`, error));
}
