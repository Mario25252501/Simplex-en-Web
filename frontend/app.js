"use strict";
const nombres=["a","b","c","d","e","f"];
const $=id=>document.getElementById(id);
let siguienteId=0;
const crearCampo=(etiqueta,clase,valor="")=>`<div class="coef-field"><label class="form-label mb-1">${etiqueta}</label><input type="number" step="any" class="form-control ${clase}" value="${valor}" placeholder="0" aria-label="Coeficiente ${etiqueta}"></div>`;
function numeroVariables(){return Number($("cantidad").value)}
function renderObjetivo(){const cont=$("objetivo");const actuales=[...cont.querySelectorAll("input")].map(e=>e.value);cont.innerHTML=nombres.slice(0,numeroVariables()).map((n,i)=>crearCampo(n,"coef-z",actuales[i]??"")).join("")}
function renderRestricciones(){document.querySelectorAll(".restriction").forEach(b=>{const viejos=[...b.querySelectorAll(".coef-r")].map(e=>e.value);b.querySelector(".r-coefs").innerHTML=nombres.slice(0,numeroVariables()).map((n,i)=>crearCampo(n,"coef-r",viejos[i]??"")).join("")})}
function agregarRestriccion(){const id=siguienteId++;const bloque=document.createElement("div");bloque.className="restriction";bloque.dataset.id=id;bloque.innerHTML=`<div class="d-flex justify-content-between align-items-center mb-2"><strong>Restricción</strong><button type="button" class="btn btn-sm btn-outline-danger quitar">Eliminar</button></div><div class="fields"><div class="r-coefs fields"></div><div><label class="form-label mb-1">Signo</label><select class="form-select signo" aria-label="Signo de restricción"><option value="<=">≤</option><option value=">=">≥</option><option value="=">=</option></select></div><div class="rhs-field"><label class="form-label mb-1">Resultado</label><input type="number" step="any" class="form-control rhs" placeholder="0" aria-label="Término independiente"></div></div>`;bloque.querySelector(".quitar").addEventListener("click",()=>{bloque.remove();renumerar()});$("restricciones").append(bloque);renderRestricciones();renumerar()}
function renumerar(){document.querySelectorAll(".restriction strong").forEach((e,i)=>e.textContent=`Restricción ${i+1}`)}
function leerNumeros(inputs,descripcion){return [...inputs].map((e,i)=>{const txt=e.value.trim();if(txt==="")throw Error(`${descripcion}: falta el coeficiente ${i+1}.`);const n=Number(txt);if(!Number.isFinite(n))throw Error(`${descripcion}: hay un número inválido.`);return n})}
function recopilar(){const n=numeroVariables(), objetivo=leerNumeros(document.querySelectorAll(".coef-z"),"Función objetivo");const bloques=[...document.querySelectorAll(".restriction")];if(bloques.length===0)throw Error("Agrega al menos una restricción.");const restricciones=bloques.map((b,i)=>{const coeficientes=leerNumeros(b.querySelectorAll(".coef-r"),`Restricción ${i+1}`);const rhs=b.querySelector(".rhs");if(rhs.value.trim()==="")throw Error(`Restricción ${i+1}: falta el término independiente.`);const termino_independiente=Number(rhs.value);if(!Number.isFinite(termino_independiente))throw Error(`Restricción ${i+1}: término independiente inválido.`);if(coeficientes.every(x=>x===0))throw Error(`Restricción ${i+1}: todos los coeficientes son cero.`);return {coeficientes,signo:b.querySelector(".signo").value,termino_independiente}});if(objetivo.length!==n)throw Error("Cantidad de coeficientes incorrecta.");return {tipo_optimizacion:$("tipo").value,variables:n,coeficientes_objetivo:objetivo,restricciones,no_negatividad:true}}
function expresion(coefs){return coefs.map((v,i)=>`${i===0?"":v<0?" − ":" + "}${Math.abs(v)}${nombres[i]}`).join("")}
function mensaje(txt,tipo="danger"){$("mensajes").innerHTML="";const alerta=document.createElement("div");alerta.className=`alert alert-${tipo}`;alerta.textContent=txt;$("mensajes").append(alerta)}
function validarYMostrar(){try{const modelo=recopilar();const lineas=[`<strong>${modelo.tipo_optimizacion==="max"?"Maximizar":"Minimizar"}</strong> Z = ${expresion(modelo.coeficientes_objetivo)}`,"<strong>Sujeto a:</strong>",...modelo.restricciones.map(r=>`${expresion(r.coeficientes)} ${r.signo==="<="?"≤":r.signo===">="?"≥":"="} ${r.termino_independiente}`),`${nombres.slice(0,modelo.variables).join(", ")} ≥ 0`];$("previa").innerHTML=lineas.map(l=>`<div>${l}</div>`).join("");$("json").textContent=JSON.stringify(modelo,null,2);mensaje("Modelo válido. Preparado para enviar al backend.","success");return modelo}catch(err){mensaje(err.message);return null}}
$("cantidad").addEventListener("change",()=>{renderObjetivo();renderRestricciones()});$("agregar").addEventListener("click",agregarRestriccion);$("vista").addEventListener("click",validarYMostrar);$("limpiar").addEventListener("click",()=>{$("cantidad").value="2";$("tipo").value="max";$("restricciones").innerHTML="";siguienteId=0;renderObjetivo();agregarRestriccion();$("previa").textContent="Ingresa los datos y pulsa «Validar y previsualizar».";$("json").textContent="—";$("mensajes").innerHTML=""});
renderObjetivo();agregarRestriccion();


// ===== Integración con la API de datos (Integrante 4) =====
// Dirección de la API de datos
const API = "http://localhost:8000";

// Convierte el modelo del formulario al formato que espera la API de datos
function aFormatoApi(modelo, nombre) {
  const vars = nombres.slice(0, modelo.variables);  // a, b, c...
  return {
    nombre,
    tipo: modelo.tipo_optimizacion.toUpperCase(),  // max -> MAX
    objetivo: Object.fromEntries(vars.map((v, i) => [v, modelo.coeficientes_objetivo[i]])),
    restricciones: modelo.restricciones.map(r => ({
      coeficientes: Object.fromEntries(vars.map((v, i) => [v, r.coeficientes[i]])),
      signo: r.signo,
      termino_independiente: r.termino_independiente
    }))
  };
}

// Hace una petición POST a la API y devuelve la respuesta en JSON (lanza error si falla)
async function enviarPost(url, cuerpo) {
  const resp = await fetch(API + url, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined
  });
  const datos = await resp.json().catch(() => ({}));
  if (!resp.ok) throw Error(typeof datos.detail === "string" ? datos.detail : JSON.stringify(datos.detail ?? datos));
  return datos;
}

// Botón "Resolver": valida, guarda en MySQL, resuelve y abre la pantalla de resultados
$("enviar").addEventListener("click", async () => {
  const modelo = validarYMostrar();  // Valida el formulario
  if (!modelo) return;
  const nombre = prompt("Nombre del problema:", "Modelo " + new Date().toLocaleString());
  if (!nombre) return;
  try {
    mensaje("Resolviendo el problema...", "info");
    const guardado = await enviarPost("/problemas", aFormatoApi(modelo, nombre));  // Guarda en MySQL
    await enviarPost(`/problemas/${guardado.id}/resolver`);  // API 2 + API 3 + guarda iteraciones
    location.href = `${API}/app/resultados.html?id=${guardado.id}`;  // Abre los resultados
  } catch (err) {
    mensaje(`No se pudo resolver: ${err.message}`);
  }
});