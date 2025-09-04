const params = new URLSearchParams(window.location.search);
const plantId = params.get("id");
let planta = null;

function renderizarDetalle(planta) {
  document.getElementById("nombre").textContent = planta.nombre_personalizado;
  document.getElementById("tipo").textContent = planta.tipo_planta;
  document.getElementById("tamano").textContent = planta.tamano_planta;
  document.getElementById("maceta").textContent = `${planta.tamano_maceta_litros} `;
  document.getElementById("ultimoRiego").textContent = planta.fecha_ultimo_riego;
  document.getElementById("enFloracion").textContent = planta.en_floracion ? "Si" : "No";
  document.getElementById("estadoRiego").textContent = planta.estado_texto;
  document.getElementById("sugerencia").textContent = planta.sugerencia_suplementos;
  document.getElementById("recomendado").textContent = `${planta.recommended_water_ml} ml`;
  document.getElementById("frecuencia").textContent = `${planta.frequency_days} días`;
  document.getElementById("proximoRiego").textContent = planta.next_watering_date;
  document.getElementById("diasRestantes").textContent = planta.days_left;
}



function configurarBotonVolver(idBoton, destino) {
  const boton = document.getElementById(idBoton);
  if (boton) {
    boton.addEventListener("click", () => window.location.href = destino);
  }
}

configurarBotonVolver("btn-volver", "/home/dashboard/");



document.addEventListener("DOMContentLoaded", async () => {
  const id = params.get("id");
  if (!id) {
    alert("No se proporcionó un ID de planta. Redirigiendo al dashboard...");
    window.location.href = "/home/dashboard/";
    return;
  }


  const plantaId = id; // función que extrae el ID de la URL
  const token = await obtenerTokenValido();

  try {
    const res = await fetch(`/api/plantas/${plantaId}/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) throw new Error("Error al obtener los datos de la planta");

    planta = await res.json();
    console.log("🌱 Detalle de planta:", planta);

    renderizarDetalle(planta); // función que actualiza el DOM con los datos
  } catch (err) {
    console.error("❌ Error en el fetch:", err);
    alert("No se pudo cargar el detalle de la planta. Intentá de nuevo.");
  }
});



function mostrarToast(mensaje) {
  const toast = document.createElement("div");
  toast.textContent = mensaje;
  toast.className = "toast-mensaje"; // Asegurate de tener estilos CSS para esto
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
}



function habilitarEdicion(campo) {
  document.getElementById("guardarCambios").classList.remove("d-none");

  const litros = document.getElementById("unidad-maceta");
  if (campo === "maceta" && litros) {
    litros.classList.add('d-none'); // Oculta "Litros" al editar maceta
  }

  const span = document.getElementById(campo);
  const input = document.getElementById(`input-${campo}`);
  const boton = event.currentTarget; // Captura el botón que disparó el evento

  if (!span || !input || !boton) {
    console.warn(`Elemento no encontrado para campo: ${campo}`);
    return;
  }

  input.value = span.textContent.trim();
  span.classList.add('d-none');
  input.classList.remove('d-none');
  boton.classList.add('d-none'); // Oculta el botón de edición
  litros.classList.remove('d-none'); // Muestra "Litros" al editar maceta
}

function obtenerIdDesdeURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}




document.getElementById('guardarCambios').addEventListener('click', async () => {
  const idPlanta = obtenerIdDesdeURL();
  const token = await obtenerTokenValido();

  const camposMap = {
    nombre: "nombre_personalizado",
    tipo: "tipo_planta",
    tamano: "tamano_planta",
    maceta: "tamano_maceta_litros",
    ultimoRiego: "fecha_ultimo_riego",
    enFloracion: "en_floracion",
    estadoRiego: "estado_texto",
    sugerencia: "sugerencia_suplementos"
    // ⚠️ Quitamos los campos calculados: recomendado, frecuencia, proximoRiego, diasRestantes
  };
  
  const payload = { ...planta };



  Object.entries(camposMap).forEach(([campoFrontend, campoBackend]) => {
  const input = document.getElementById(`input-${campoFrontend}`);
  if (input && !input.classList.contains('d-none')) {
    if (campoFrontend === "enFloracion") {
      payload[campoBackend] = input.value.trim().toLowerCase() === "si"; // ✅ booleano
    } else {
      payload[campoBackend] = input.value.trim();
    }
  }
});


  const camposInvalidos = Object.entries(payload).filter(([_, valor]) => {
    return typeof valor === 'string' && valor.trim() === '';
  });

  if (camposInvalidos.length > 0) {
    mostrarToast('⚠️ Hay campos vacíos');
    return;
  }

  try {
    guardarCambios.disabled = true;
    guardarCambios.textContent = 'Guardando...';

    console.log("Payload enviado:", JSON.stringify(payload));

    // 1. PUT
    const resPut = await fetch(`/api/plantas/${idPlanta}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    if (!resPut.ok) {
      mostrarToast('⚠️ Error al actualizar');
      throw new Error("Error en PUT");
    }

    mostrarToast('✅ Planta actualizada');

    // 2. GET
    const resGet = await fetch(`/api/plantas/${idPlanta}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      }
    });

    if (!resGet.ok) {
      mostrarToast('⚠️ Error al refrescar datos');
      throw new Error("Error en GET");
    }

    const plantaActualizada = await resGet.json();
    planta = plantaActualizada; // actualizamos la variable global

    // 3. Actualizar DOM
    renderizarDetalle(plantaActualizada);

    // Restaurar visibilidad
    Object.keys(camposMap).forEach(campo => {
      const span = document.getElementById(campo);
      const input = document.getElementById(`input-${campo}`);
      const btnEditar = document.getElementById(`editar-${campo}`);
      if (span && input) {
        span.classList.remove('d-none');
        input.classList.add('d-none');
        if (btnEditar) btnEditar.classList.remove('d-none');
      }
    });

    document.getElementById("guardarCambios").classList.add("d-none");
    guardarCambios.disabled = false;
    guardarCambios.textContent = '💾 Guardar cambios';

  } catch (err) {
    console.error("❌ Error en actualización:", err);
    mostrarToast('❌ Fallo de conexión');
    guardarCambios.disabled = false;
    guardarCambios.textContent = '💾 Guardar cambios';
  }
});


// document.getElementById('guardarCambios').addEventListener('click', async () => {
//   const idPlanta = obtenerIdDesdeURL();

//   const camposMap = {
//    nombre: "nombre_personalizado",
//    tipo: "tipo_planta",
//    tamano: "tamano_planta",
//    maceta: "tamano_maceta_litros",
//    ultimoRiego: "fecha_ultimo_riego",
//    enFloracion: "en_floracion",
//    estadoRiego: "estado_texto",
//    sugerencia: "sugerencia_suplementos",
//    recomendado: "recommended_water_ml",
//    frecuencia: "frequency_days",
//    proximoRiego: "next_watering_date",
//    diasRestantes: "days_left"
//    };

// const payload = { ...planta }; // copia todos los datos originales

// Object.entries(camposMap).forEach(([campoFrontend, campoBackend]) => {
//   const input = document.getElementById(`input-${campoFrontend}`);
//   if (input && !input.classList.contains('d-none')) {
//     payload[campoBackend] = input.value.trim();
//   }
// });


//   const camposInvalidos = Object.entries(payload).filter(([_, valor]) => {
//   return typeof valor === 'string' && valor.trim() === '';
//   });

//   if (camposInvalidos.length > 0) {
//   mostrarToast('⚠️ Hay campos vacíos');
//   return;
//   }

//   try {
//       guardarCambios.disabled = true;
//       guardarCambios.textContent = 'Guardando...';

//       const token = await obtenerTokenValido();
//       console.log("📦 Payload enviado:", JSON.stringify(payload, null, 2));

//       const res = await fetch(`/api/plantas/${idPlanta}/`, {
//       method: 'PUT',
//       headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },   
//       body: JSON.stringify(payload)
//     });

//     if (res.ok) {
//       const data = await res.json();
//       mostrarToast('✅ Planta actualizada');
//       actualizarVista(data); // helper que refresca los spans
//     } else {
//       mostrarToast('⚠️ Error al actualizar');
//     }
    
//     guardarCambios.disabled = false;
//     guardarCambios.textContent = '💾 Guardar cambios';
//     document.getElementById("guardarCambios").classList.add("d-none");

//   } catch (err) {
//     console.error(err);
//     mostrarToast('❌ Fallo de conexión');
//   }
// });



// function actualizarVista(data) {
//   const camposMap = {
//     nombre: "nombre_personalizado",
//     tipo: "tipo_planta",
//     tamano: "tamano_planta",
//     maceta: "tamano_maceta_litros",
//     ultimoRiego: "fecha_ultimo_riego",
//     enFloracion: "en_floracion",
//     estadoRiego: "estado_texto",
//     sugerencia: "sugerencia_suplementos",
//     recomendado: "recommended_water_ml",
//     frecuencia: "frequency_days",
//     proximoRiego: "next_watering_date",
//     diasRestantes: "days_left"
//   };

//   Object.entries(camposMap).forEach(([campoFrontend, campoBackend]) => {
//     const span = document.getElementById(campoFrontend);
//     const input = document.getElementById(`input-${campoFrontend}`);
//     const nuevoValor = data[campoBackend];

//     if (span && input && nuevoValor !== undefined) {
//       span.textContent = nuevoValor;
//       span.classList.remove('d-none');
//        input.classList.add('d-none');

//        const btnEditar = document.getElementById(`editar-${campoFrontend}`);
//        if (btnEditar) btnEditar.classList.remove('d-none');
//      }
//    });
//  }





// function actualizarVista(data) {
//   const camposMap = {
//     nombre: "nombre_personalizado",
//     tipo: "tipo_planta",
//     tamano: "tamano_planta",
//     maceta: "tamano_maceta_litros",
//     ultimoRiego: "fecha_ultimo_riego",
//     enFloracion: "en_floracion",
//     estadoRiego: "estado_texto",
//     sugerencia: "sugerencia_suplementos",
//     recomendado: "recommended_water_ml",
//     frecuencia: "frequency_days",
//     proximoRiego: "next_watering_date",
//     diasRestantes: "days_left"
//   };

//   Object.entries(camposMap).forEach(([campoFrontend, campoBackend]) => {
//     const span = document.getElementById(campoFrontend);
//     const input = document.getElementById(`input-${campoFrontend}`);
//     const nuevoValor = data[campoBackend];

//     if (nuevoValor !== undefined && span) {
//       // Actualiza el span siempre
//       span.textContent = campoFrontend === "enFloracion"
//         ? nuevoValor ? "Sí" : "No"
//         : campoFrontend === "recomendado"
//         ? `${nuevoValor} ml`
//         : campoFrontend === "frecuencia"
//         ? `${nuevoValor} días`
//         : nuevoValor;

//       // Si el campo fue editado, restaurar visibilidad
//       if (input && !input.classList.contains("d-none")) {
//         span.classList.remove("d-none");
//         input.classList.add("d-none");

//         const btnEditar = document.getElementById(`editar-${campoFrontend}`);
//         if (btnEditar) btnEditar.classList.remove("d-none");
//       }
//     }
//   });
// }
