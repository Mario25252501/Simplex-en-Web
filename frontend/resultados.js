// Dirección base de la API (vacía porque el mismo servidor entrega la página)
const API = "";

// Datos de la pantalla: problema abierto, su resultado y la iteración visible
let problemaId = null;
let nombreProblema = "";
let resultado = null;
let indice = 0;

// Atajo para buscar un elemento por su id
const $ = (id) => document.getElementById(id);

// Evita que un texto con símbolos como < o > rompa el HTML
const esc = (t) => String(t).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// Redondea números a 4 decimales para que la tabla se vea limpia
const fmt = (v) => (typeof v === "number" ? String(Math.round(v * 10000) / 10000) : v === null || v === undefined ? "" : String(v));

// Hace una petición a la API y lanza error si la respuesta no es exitosa
async function pedir(url, opciones) {
  const r = await fetch(API + url, opciones);
  if (!r.ok) {
    const e = new Error("Error " + r.status);
    e.status = r.status;
    throw e;
  }
  return r.json();
}

// Muestra un mensaje de aviso en la parte superior del resultado
function avisar(texto, tipo) {
  $("detalle").classList.add("d-none");
  $("mensaje").className = "alert alert-" + tipo;
  $("mensaje").textContent = texto;
}

// Carga la lista de problemas guardados (historial)
async function cargarHistorial() {
  const cont = $("historial");
  try {
    const lista = await pedir("/problemas");
    if (lista.length === 0) {
      cont.innerHTML = '<div class="p-3 text-muted">Sin problemas guardados</div>';
      return;
    }
    cont.innerHTML = lista.map((p) => `
      <button class="list-group-item list-group-item-action" data-id="${p.id}" data-nombre="${esc(p.nombre)}">
        <div class="fw-semibold">${esc(p.nombre)}</div>
        <small class="text-muted">#${p.id} · ${esc(p.tipo)} · ${p.num_variables} variables</small>
      </button>`).join("");
    // Al hacer clic en un problema, se abre su resultado
    cont.querySelectorAll("button").forEach((b) =>
      b.addEventListener("click", () => abrirProblema(Number(b.dataset.id), b.dataset.nombre)));
    if (problemaId) marcarActivo(problemaId);
  } catch (e) {
    cont.innerHTML = '<div class="p-3 text-danger">No se pudo cargar. ¿Está encendido el servidor?</div>';
  }
}

// Resalta en el historial el problema que está abierto
function marcarActivo(id) {
  $("historial").querySelectorAll("button").forEach((b) =>
    b.classList.toggle("active", Number(b.dataset.id) === id));
}

// Abre un problema: pide su resultado a la API
async function abrirProblema(id, nombre) {
  problemaId = id;
  nombreProblema = nombre;
  marcarActivo(id);
  try {
    resultado = await pedir(`/problemas/${id}/resultado`);
    mostrarResultado();
  } catch (e) {
    if (e.status === 404) mostrarSinResolver();
    else avisar("No se pudo consultar el resultado.", "danger");
  }
}

// Si el problema aún no tiene resultado, ofrece resolverlo
function mostrarSinResolver() {
  $("detalle").classList.add("d-none");
  $("mensaje").className = "alert alert-warning";
  $("mensaje").innerHTML = `El problema "${esc(nombreProblema)}" aún no se ha resuelto.
    <button id="btn-resolver" class="btn btn-sm btn-primary ms-2">Resolver ahora</button>`;
  $("btn-resolver").addEventListener("click", resolver);
}

// Pide a la API que resuelva el problema y luego muestra el resultado
async function resolver() {
  try {
    await pedir(`/problemas/${problemaId}/resolver`, { method: "POST" });
    await abrirProblema(problemaId, nombreProblema);
  } catch (e) {
    avisar("No se pudo resolver el problema.", "danger");
  }
}

// Dibuja el resumen (estado, Z y solución) y la primera iteración
function mostrarResultado() {
  $("mensaje").className = "d-none";
  $("detalle").classList.remove("d-none");
  $("titulo").textContent = nombreProblema;

  // Estado final con color según el caso
  const colores = { OPTIMO: "success", INFACTIBLE: "danger", NO_ACOTADO: "warning" };
  const textos = { OPTIMO: "Solución óptima", INFACTIBLE: "Sin solución factible", NO_ACOTADO: "Solución no acotada" };
  $("estado").className = "badge fs-6 text-bg-" + (colores[resultado.estado] || "secondary");
  $("estado").textContent = textos[resultado.estado] || resultado.estado;

  // Valor de Z y valor de cada variable
  $("valor-z").textContent = resultado.valor_z === null ? "—" : fmt(resultado.valor_z);
  const sol = Object.entries(resultado.solucion || {});
  $("solucion").innerHTML = sol.length
    ? sol.map(([k, v]) => `<span class="badge text-bg-light border fs-6 me-1">${esc(k)} = ${esc(fmt(v))}</span>`).join("")
    : "—";

  indice = 0;
  dibujar();
}

// Dibuja la tabla de la iteración actual con el pivote resaltado
function dibujar() {
  const its = resultado.iteraciones;
  if (its.length === 0) {
    $("it-titulo").textContent = "Sin iteraciones";
    return;
  }
  const it = its[indice];

  // Título, contador y botones de navegación
  $("it-titulo").textContent = `Iteración ${it.numero}` + (it.fase ? ` · Fase ${it.fase}` : "");
  $("it-contador").textContent = `${indice + 1} de ${its.length}`;
  $("btn-anterior").disabled = indice === 0;
  $("btn-siguiente").disabled = indice === its.length - 1;

  // Variable que entra, variable que sale y elemento pivote
  $("it-info").innerHTML = it.variable_entrante
    ? `Entra: <b>${esc(it.variable_entrante)}</b> · Sale: <b>${esc(it.variable_saliente)}</b> · Elemento pivote: <b>${esc(fmt(it.elemento_pivote))}</b>`
    : "Tabla final: ya no hay pivotes por aplicar.";

  // Encabezado de la tabla (la columna pivote se marca en naranja)
  const cols = it.tabla.columnas;
  let html = "<thead><tr>" + cols.map((c, j) =>
    `<th class="${j === it.columna_pivote ? "col-pivote" : ""}">${esc(c)}</th>`).join("") + "</tr></thead><tbody>";

  // Filas: se resalta la fila pivote, la columna pivote y la celda pivote
  it.tabla.filas.forEach((fila, i) => {
    html += `<tr class="${i === 0 ? "fila-z" : ""}">`;
    fila.forEach((celda, j) => {
      let clase = j === 0 ? "nombre-fila" : "";
      if (i === it.fila_pivote && j === it.columna_pivote) clase += " pivote";
      else if (i === it.fila_pivote) clase += " fila-pivote";
      else if (j === it.columna_pivote) clase += " col-pivote";
      html += `<td class="${clase}">${esc(fmt(celda))}</td>`;
    });
    html += "</tr>";
  });
  $("tabla").innerHTML = html + "</tbody>";

  // Operaciones de fila realizadas en esta iteración
  $("it-operaciones").innerHTML = it.operaciones && it.operaciones.length
    ? `<div class="fw-semibold mb-1">Operaciones</div>
       <ul class="operaciones mb-0">${it.operaciones.map((o) => `<li><code>${esc(o)}</code></li>`).join("")}</ul>`
    : "";
}

// Botones anterior y siguiente
$("btn-anterior").addEventListener("click", () => { if (indice > 0) { indice--; dibujar(); } });
$("btn-siguiente").addEventListener("click", () => { if (indice < resultado.iteraciones.length - 1) { indice++; dibujar(); } });
// Botón para volver a cargar el historial
$("btn-actualizar").addEventListener("click", cargarHistorial);

// Al abrir la página, carga el historial y abre el problema indicado en la dirección (?id=...)
cargarHistorial().then(() => {
  const id = new URLSearchParams(location.search).get("id");
  const boton = id && document.querySelector(`#historial button[data-id="${id}"]`);
  if (boton) boton.click();
});
