/**
 * Inicializa un autocompletado personalizado de Google Places (versión nueva, con async/await)
 * en el input de localidad. Las sugerencias aparecen automáticamente mientras el usuario escribe.
 * Esta función es llamada por el callback en el script de la API de Google Maps.
 */
async function initAutocomplete() {
  const inputLocalidad = document.getElementById("inputLocalidad");
  const suggestionsWrapper = document.getElementById("suggestions-wrapper");

  if (!inputLocalidad || !suggestionsWrapper) {
    console.error("Elementos del DOM para autocompletado no encontrados.");
    return;
  }

  // Importamos las librerías necesarias de la nueva API de Places
  const { AutocompleteService, PlacesServiceStatus } = await google.maps.importLibrary("places");
  const autocompleteService = new AutocompleteService();

  // Función para posicionar el contenedor de sugerencias debajo del input
  function positionSuggestions() {
    const inputRect = inputLocalidad.getBoundingClientRect();
    suggestionsWrapper.style.position = 'absolute';
    suggestionsWrapper.style.top = `${inputRect.bottom + window.scrollY}px`;
    suggestionsWrapper.style.left = `${inputRect.left + window.scrollX}px`;
    suggestionsWrapper.style.width = `${inputRect.width}px`;
  }

  // Función para mostrar las sugerencias en el DOM
  function displaySuggestions(predictions) {
    suggestionsWrapper.innerHTML = ''; // Limpiamos antes de mostrar nuevas

    if (!predictions || predictions.length === 0) {
      suggestionsWrapper.style.display = 'none';
      return;
    }

    predictions.forEach(prediction => {
      const suggestionItem = document.createElement('a');
      suggestionItem.href = '#';
      suggestionItem.className = 'list-group-item list-group-item-action suggestion-item';
      suggestionItem.innerHTML = `
        <i class="bi bi-geo-alt-fill me-2"></i>
        ${prediction.description}
      `;

      suggestionItem.addEventListener('click', (e) => {
        e.preventDefault();
        inputLocalidad.value = prediction.description;
        suggestionsWrapper.style.display = 'none';
      });

      suggestionsWrapper.appendChild(suggestionItem);
    });

    positionSuggestions();
    suggestionsWrapper.style.display = 'block';
  }

  // Event listener en el input para buscar mientras se escribe
  inputLocalidad.addEventListener('input', () => {
    const query = inputLocalidad.value;

    if (query.length < 3) {
      suggestionsWrapper.style.display = 'none';
      return;
    }

    // Hacemos la llamada a la API
    autocompleteService.getPlacePredictions({
      input: query,
      types: ['(cities)'] // Seguimos buscando solo ciudades
    }, (predictions, status) => {
      if (status === PlacesServiceStatus.OK) {
        displaySuggestions(predictions);
      } else {
        // En caso de error (ej: ZERO_RESULTS), simplemente ocultamos las sugerencias.
        // El error de API Key inválida se verá en la consola del navegador.
        suggestionsWrapper.style.display = 'none';
      }
    });
  });

  // Ocultar sugerencias si se hace clic fuera del input o del contenedor de sugerencias
  document.addEventListener('click', (e) => {
    const isClickInside = inputLocalidad.contains(e.target) || suggestionsWrapper.contains(e.target);
    if (!isClickInside) {
      suggestionsWrapper.style.display = 'none';
    }
  });

  // Reposicionar si la ventana cambia de tamaño
  window.addEventListener('resize', () => {
    if (suggestionsWrapper.style.display === 'block') {
      positionSuggestions();
    }
  });

  // Eliminamos el listener del botón de búsqueda, ya no es necesario.
  const btnBuscarLocalidad = document.getElementById("btnBuscarLocalidad");
  if (btnBuscarLocalidad) {
    // Ocultamos el botón ya que no tiene uso.
    btnBuscarLocalidad.style.display = 'none';
  }
}

// Hacemos la función global para que el callback de Google la encuentre.
window.initAutocomplete = initAutocomplete;