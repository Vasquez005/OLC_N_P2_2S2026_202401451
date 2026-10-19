/* ==========================================================
   OxigenNative: lógica de la interfaz web.
   ========================================================== */

const $ = (id) => document.getElementById(id);

const editor = $('codigo');
const numeros = $('numeros');
const consola = $('consola');

const estado = {
  nombre: 'sin_titulo.rs',
  modificado: false,
  lineasConError: new Set(),
  zoomAst: 1,
};

const EJEMPLO = `fn main() {
    let nombre = String::from("OxigenNative");
    let mut total: i32 = 0;
    let mut i = 1;

    while i <= 5 {
        total += i;
        i += 1;
    }

    let promedio: f64 = total / 5.0;
    println!("Hola desde {}", nombre);
    println!("Suma: {}, promedio: {}", total, promedio);

    if total > 10 && promedio >= 3.0 {
        println!("Mayor que 10");
    } else {
        println!("Menor o igual a 10");
    }
}
`;

// ==========================================================
// Editor: números de línea, posición del cursor y teclado
// ==========================================================

function actualizarNumeros() {
  const total = editor.value.split('\n').length;
  const partes = [];
  for (let n = 1; n <= total; n++) {
    partes.push(estado.lineasConError.has(n)
      ? `<span class="linea-error">${n}</span>`
      : String(n));
  }
  // Líneas extra al final para que el desplazamiento coincida con el editor
  numeros.innerHTML = partes.join('\n') + '\n\n\n';
  numeros.scrollTop = editor.scrollTop;
}

function actualizarPosicion() {
  const antes = editor.value.slice(0, editor.selectionStart).split('\n');
  $('posicion').textContent = `Lín ${antes.length}, Col ${antes[antes.length - 1].length + 1}`;
}

function marcarModificado(valor) {
  estado.modificado = valor;
  $('nombre-archivo').textContent = estado.nombre + (valor ? ' •' : '');
}

function insertarTexto(texto) {
  // execCommand mantiene el historial de deshacer (Ctrl/Cmd + Z)
  if (!document.execCommand('insertText', false, texto)) {
    editor.setRangeText(texto, editor.selectionStart, editor.selectionEnd, 'end');
  }
}

editor.addEventListener('input', () => {
  marcarModificado(true);
  actualizarNumeros();
  actualizarPosicion();
  guardarBorrador();
});
editor.addEventListener('scroll', () => { numeros.scrollTop = editor.scrollTop; });
editor.addEventListener('click', actualizarPosicion);
editor.addEventListener('keyup', actualizarPosicion);

editor.addEventListener('keydown', (e) => {
  if (e.key === 'Tab') {                       // Tab inserta 4 espacios
    e.preventDefault();
    insertarTexto('    ');
  } else if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
    // Enter conserva la sangría de la línea actual
    e.preventDefault();
    const inicio = editor.value.lastIndexOf('\n', editor.selectionStart - 1) + 1;
    const sangria = editor.value.slice(inicio).match(/^[ \t]*/)[0];
    insertarTexto('\n' + sangria);
  }
});

function irALinea(linea) {
  const lineas = editor.value.split('\n');
  const n = Math.max(1, Math.min(linea, lineas.length));
  let inicio = 0;
  for (let i = 0; i < n - 1; i++) inicio += lineas[i].length + 1;
  editor.focus();
  editor.setSelectionRange(inicio, inicio + lineas[n - 1].length);
  const altoLinea = parseFloat(getComputedStyle(editor).lineHeight);
  editor.scrollTop = Math.max(0, (n - 4) * altoLinea);
  actualizarPosicion();
}

// ==========================================================
// Borrador local (si se recarga la página no se pierde el código)
// ==========================================================

function guardarBorrador() {
  try {
    localStorage.setItem('oxigen_codigo', editor.value);
    localStorage.setItem('oxigen_nombre', estado.nombre);
  } catch (e) { /* el navegador no permite guardar: no pasa nada */ }
}

function cargarBorrador() {
  try {
    const codigo = localStorage.getItem('oxigen_codigo');
    if (codigo !== null) {
      estado.nombre = localStorage.getItem('oxigen_nombre') || estado.nombre;
      return codigo;
    }
  } catch (e) { /* ignorar */ }
  return EJEMPLO;
}

// ==========================================================
// Archivos: nuevo, abrir y guardar
// ==========================================================

function ponerCodigo(texto, nombre) {
  editor.value = texto;
  estado.nombre = nombre;
  estado.lineasConError.clear();
  marcarModificado(false);
  actualizarNumeros();
  actualizarPosicion();
  guardarBorrador();
  editor.scrollTop = 0;
}

$('btn-nuevo').addEventListener('click', () => {
  if (estado.modificado && !confirm('Hay cambios sin guardar. ¿Crear un archivo nuevo de todos modos?')) return;
  ponerCodigo('fn main() {\n    \n}\n', 'sin_titulo.rs');
  editor.focus();
  editor.setSelectionRange(16, 16);
});

$('btn-abrir').addEventListener('click', () => $('entrada-archivo').click());

$('entrada-archivo').addEventListener('change', (e) => {
  const archivo = e.target.files[0];
  if (!archivo) return;
  if (estado.modificado && !confirm('Hay cambios sin guardar. ¿Abrir otro archivo de todos modos?')) {
    e.target.value = '';
    return;
  }
  const lector = new FileReader();
  lector.onload = () => {
    ponerCodigo(lector.result, archivo.name);
    escribirConsola(`Archivo "${archivo.name}" abierto.`, 'info');
  };
  lector.readAsText(archivo, 'utf-8');
  e.target.value = '';      // permite volver a abrir el mismo archivo
});

function guardarArchivo() {
  let nombre = prompt('Nombre del archivo:', estado.nombre);
  if (!nombre) return;
  if (!nombre.includes('.')) nombre += '.rs';
  const blob = new Blob([editor.value], { type: 'text/plain;charset=utf-8' });
  const enlace = document.createElement('a');
  enlace.href = URL.createObjectURL(blob);
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  setTimeout(() => URL.revokeObjectURL(enlace.href), 1000);
  estado.nombre = nombre;
  marcarModificado(false);
  guardarBorrador();
  escribirConsola(`Archivo guardado como "${nombre}".`, 'info');
}
$('btn-guardar').addEventListener('click', guardarArchivo);

// Atajos de teclado globales
document.addEventListener('keydown', (e) => {
  const mod = e.ctrlKey || e.metaKey;
  if (mod && e.key === 'Enter') { e.preventDefault(); ejecutar(); }
  if (mod && (e.key === 's' || e.key === 'S')) { e.preventDefault(); guardarArchivo(); }
});

// ==========================================================
// Consola
// ==========================================================

function escribirConsola(texto, clase = 'salida') {
  const linea = document.createElement('span');
  linea.className = clase;
  linea.textContent = texto.endsWith('\n') ? texto : texto + '\n';
  consola.appendChild(linea);
  consola.scrollTop = consola.scrollHeight;
}

$('btn-limpiar').addEventListener('click', () => { consola.textContent = ''; });

$('btn-copiar-asm').addEventListener('click', async () => {
  const texto = $('asm').classList.contains('vacio') ? '' : $('asm').textContent;
  if (!texto) return;
  try {
    await navigator.clipboard.writeText(texto);
    escribirConsola('Código ARM64 copiado al portapapeles.', 'info');
  } catch (e) {
    escribirConsola('No se pudo copiar el código ARM64.', 'error');
  }
});

// ==========================================================
// Ejecutar: llamar a la API y mostrar los resultados
// ==========================================================

async function ejecutar() {
  const boton = $('btn-ejecutar');
  if (boton.disabled) return;
  boton.disabled = true;
  boton.textContent = 'Ejecutando…';

  consola.textContent = '';
  escribirConsola(`> Compilando "${estado.nombre}"...`, 'info');

  try {
    const respuesta = await fetch('/api/compilar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ codigo: editor.value }),
    });
    const datos = await respuesta.json();
    mostrarResultado(datos);
  } catch (e) {
    escribirConsola('✖ No se pudo conectar con el servidor. ¿Está corriendo "python manage.py runserver"?', 'error');
  } finally {
    boton.disabled = false;
    boton.textContent = 'Ejecutar';
  }
}
$('btn-ejecutar').addEventListener('click', ejecutar);

function mostrarResultado(d) {
  if (d.error_interno) {
    escribirConsola('✖ ' + d.error_interno, 'error');
    return;
  }

  // ---- Resumen de errores ----
  const errores = d.errores || [];
  if (errores.length === 0) {
    escribirConsola('✔ Compilación exitosa.', 'exito');
  } else {
    const cuenta = { 'Léxico': 0, 'Sintáctico': 0, 'Semántico': 0 };
    errores.forEach((e) => { cuenta[e.tipo] = (cuenta[e.tipo] || 0) + 1; });
    escribirConsola(
      `✖ Se encontraron ${errores.length} error(es): ${cuenta['Léxico']} léxico(s), ` +
      `${cuenta['Sintáctico']} sintáctico(s), ${cuenta['Semántico']} semántico(s). ` +
      'Ver la pestaña "Errores".', 'error');
    if (d.asm) {
      escribirConsola('  El programa se ejecutó omitiendo las partes con error.', 'info');
    } else {
      escribirConsola('  No se generó código por los errores léxicos o sintácticos.', 'info');
    }
  }

  // ---- Salida del programa ----
  if (d.asm) {
    escribirConsola('──────── Salida del programa ────────', 'info');
    if (d.salida) escribirConsola(d.salida, 'salida');
  }
  if (d.error_ejecucion) escribirConsola('✖ ' + d.error_ejecucion, 'error');

  // ---- Tiempos ----
  const t = d.tiempos || {};
  escribirConsola(
    `Tiempo: análisis ${t.analisis} ms · generación ${t.generacion} ms · ` +
    `ensamblado ${t.ensamblado} ms · ejecución ${t.ejecucion} ms · total ${t.total} ms`, 'info');

  // ---- Paneles ----
  mostrarAsm(d.asm);
  mostrarErrores(errores);
  mostrarTabla(d.tabla || []);
  mostrarAst(d.ast_svg);

  if (errores.length > 0) activarPestana('errores');
}

function mostrarAsm(asm) {
  const panel = $('asm');
  if (asm) {
    panel.textContent = asm;
    panel.classList.remove('vacio');
  } else {
    panel.textContent = 'No se generó código ARM64.';
    panel.classList.add('vacio');
  }
}

// ==========================================================
// Reportes en pestañas
// ==========================================================

function crearTabla(columnas, filas, opciones = {}) {
  const tabla = document.createElement('table');
  const encabezado = tabla.createTHead().insertRow();
  columnas.forEach(([, titulo]) => {
    const th = document.createElement('th');
    th.textContent = titulo;
    encabezado.appendChild(th);
  });
  const cuerpo = tabla.createTBody();
  filas.forEach((fila) => {
    const tr = cuerpo.insertRow();
    columnas.forEach(([clave]) => {
      const td = tr.insertCell();
      td.textContent = fila[clave] ?? '';
      if (opciones.mono && opciones.mono.includes(clave)) td.className = 'mono';
    });
    if (opciones.alClic) {
      tr.className = 'clic';
      tr.title = 'Ir a la línea en el editor';
      tr.addEventListener('click', () => opciones.alClic(fila));
    }
  });
  return tabla;
}

function mostrarErrores(errores) {
  const contenedor = $('pestana-errores');
  contenedor.innerHTML = '';
  $('cuenta-errores').textContent = errores.length || '';

  estado.lineasConError = new Set(errores.map((e) => e.linea));
  actualizarNumeros();

  if (errores.length === 0) {
    contenedor.innerHTML = '<p class="vacio">No se encontraron errores.</p>';
    return;
  }
  contenedor.appendChild(crearTabla(
    [['no', 'No.'], ['tipo', 'Tipo'], ['descripcion', 'Descripción'],
     ['linea', 'Línea'], ['columna', 'Columna'], ['fragmento', 'Fragmento']],
    errores,
    { mono: ['fragmento'], alClic: (e) => irALinea(e.linea) }));
}

function mostrarTabla(filas) {
  const contenedor = $('pestana-tabla');
  contenedor.innerHTML = '';
  if (filas.length === 0) {
    contenedor.innerHTML = '<p class="vacio">No hay símbolos registrados.</p>';
    return;
  }
  contenedor.appendChild(crearTabla(
    [['no', 'No.'], ['identificador', 'Identificador'], ['categoria', 'Categoría'],
     ['tipo', 'Tipo'], ['ambito', 'Ámbito'], ['linea', 'Línea'],
     ['columna', 'Columna'], ['valor', 'Valor']],
    filas,
    { mono: ['identificador', 'tipo', 'valor'] }));
}

function mostrarAst(svg) {
  const contenedor = $('ast');
  if (!svg) {
    contenedor.innerHTML = '<p class="vacio">No se pudo generar el AST.</p>';
    return;
  }
  // El SVG lo genera Graphviz en el servidor (los textos ya vienen escapados)
  contenedor.innerHTML = svg.slice(svg.indexOf('<svg'));
  const imagen = contenedor.querySelector('svg');
  imagen.dataset.ancho = parseFloat(imagen.getAttribute('width'));
  imagen.dataset.alto = parseFloat(imagen.getAttribute('height'));
  aplicarZoom();
}

function aplicarZoom() {
  const imagen = $('ast').querySelector('svg');
  if (!imagen) return;
  imagen.setAttribute('width', imagen.dataset.ancho * estado.zoomAst + 'pt');
  imagen.setAttribute('height', imagen.dataset.alto * estado.zoomAst + 'pt');
}

document.querySelectorAll('[data-zoom]').forEach((boton) => {
  boton.addEventListener('click', () => {
    const paso = Number(boton.dataset.zoom);
    estado.zoomAst = paso === 0 ? 1
      : Math.min(3, Math.max(0.2, estado.zoomAst * (paso > 0 ? 1.25 : 0.8)));
    aplicarZoom();
  });
});

function activarPestana(nombre) {
  document.querySelectorAll('.pestana').forEach((p) =>
    p.classList.toggle('activa', p.dataset.pestana === nombre));
  document.querySelectorAll('.pestana-contenido').forEach((c) =>
    c.classList.toggle('activa', c.id === 'pestana-' + nombre));
}

document.querySelectorAll('.pestana').forEach((p) =>
  p.addEventListener('click', () => activarPestana(p.dataset.pestana)));

// Cerrar el menú de reportes al elegir una opción o hacer clic afuera
document.addEventListener('click', (e) => {
  const menu = document.querySelector('.menu');
  if (menu.open && (!menu.contains(e.target) || e.target.tagName === 'A')) {
    menu.open = false;
  }
});

// ==========================================================
// Inicio
// ==========================================================

editor.value = cargarBorrador();
marcarModificado(false);
actualizarNumeros();
actualizarPosicion();
escribirConsola('Listo. Escriba código y presione "Ejecutar" (Ctrl/Cmd + Enter).', 'info');
