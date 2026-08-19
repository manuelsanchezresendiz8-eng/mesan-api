// JARVIS Chat Logic — MESAN Omega — Embudo Comercial v2.0
// Flujo: Conocer > Diagnosticar > Demostrar valor > Membresía > Escalar

var jarvisFlow = {
  step: 0,
  dudaMode: false,
  userData: {
    nombre: '',
    empresa: '',
    sector: '',
    tamano: '',
    email: '',
    telefono: '',
    dias: '',
    horario: '',
    preocupacion: '',
    respuestas: [],
    producto_interes: 'diagnostico_entrada',
    fuente: 'jarvis_chat'
  }
};

function toggleJarvisChat() {
  var win = document.getElementById('jarvis-chat-window');
  if (win.classList.contains('open')) {
    win.classList.remove('open');
  } else {
    win.classList.add('open');
    if (!win.getAttribute('data-initialized')) {
      initJarvisChat();
      win.setAttribute('data-initialized', 'true');
    }
  }
}

function initJarvisChat() {
  addJarvisMessage("Hola, soy JARVIS, asistente de riesgo empresarial de MESAN \u03A9.\n\n\u00BFCu\u00E1l es tu nombre y el de tu empresa?\n(Ej: Juan, Empresa ABC)");
}

function handleJarvisKeypress(event) {
  if (event.key === 'Enter') sendJarvisMessage();
}

function sendJarvisMessage() {
  var input = document.getElementById('jarvis-input');
  var message = input.value.trim();
  if (!message) return;
  addJarvisMessage(message, 'user');
  input.value = '';
  setTimeout(function() { processJarvisResponse(message); }, 500);
}

function addJarvisMessage(text, sender) {
  sender = sender || 'bot';
  var container = document.getElementById('jarvis-messages');
  var div = document.createElement('div');
  div.className = 'jarvis-message ' + sender;
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function showJarvisTyping() {
  var container = document.getElementById('jarvis-messages');
  if (document.getElementById('jarvis-typing')) return;
  var div = document.createElement('div');
  div.className = 'jarvis-typing';
  div.id = 'jarvis-typing';
  div.innerHTML = '<div class="jarvis-typing-dot"></div><div class="jarvis-typing-dot"></div><div class="jarvis-typing-dot"></div>';
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function hideJarvisTyping() {
  var el = document.getElementById('jarvis-typing');
  if (el) el.remove();
}

function addJarvisOptions(options) {
  var container = document.getElementById('jarvis-messages');
  var old = container.querySelector('.jarvis-options');
  if (old) old.remove();
  var div = document.createElement('div');
  div.className = 'jarvis-options';
  options.forEach(function(opt) {
    var btn = document.createElement('button');
    btn.className = 'jarvis-option-btn';
    btn.textContent = opt.text;
    btn.onclick = function() {
      addJarvisMessage(opt.text, 'user');
      div.remove();
      opt.callback();
    };
    div.appendChild(btn);
  });
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// ============================================================
// FLUJO PRINCIPAL
// ============================================================
function processJarvisResponse(message) {
  showJarvisTyping();
  setTimeout(function() {
    hideJarvisTyping();

    if (jarvisFlow.dudaMode) {
      jarvisFlow.dudaMode = false;
      addJarvisMessage("Buena pregunta. Nuestro equipo puede darte m\u00E1s detalle, pero primero identifiquemos tus riesgos principales.\n\n\u00BFContinuamos?");
      addJarvisOptions([
        { text: 'S\u00ED, continuamos', callback: function() { showSector(); } },
        { text: 'No por ahora', callback: function() { addJarvisMessage("Entendido. Cuando quieras retomar, aqu\u00ED estoy."); } }
      ]);
      return;
    }

    switch(jarvisFlow.step) {
      case 0:
        var parts = message.split(',');
        jarvisFlow.userData.nombre = (parts[0] || message).trim();
        jarvisFlow.userData.empresa = (parts[1] || '').trim();
        addJarvisMessage("Mucho gusto, " + jarvisFlow.userData.nombre + ".\n\nAntes de cualquier cosa, quiero entender tu situaci\u00F3n. Voy a hacerte unas preguntas r\u00E1pidas para identificar d\u00F3nde podr\u00EDa estar expuesta tu empresa.\n\n\u00BFComenzamos?");
        addJarvisOptions([
          { text: 'S\u00ED, comenzamos', callback: function() { showSector(); } },
          { text: 'Tengo una duda primero', callback: showJarvisDuda }
        ]);
        break;

      case 9:
        jarvisFlow.userData.email = message;
        addJarvisMessage("\u00BFY tu tel\u00E9fono? (para enviarte el resultado)");
        jarvisFlow.step = 10;
        break;

      case 10:
        jarvisFlow.userData.telefono = message;
        addJarvisMessage("\u00BFQu\u00E9 d\u00EDas tienes disponibles para revisar los resultados?");
        jarvisFlow.step = 11;
        break;

      case 11:
        jarvisFlow.userData.dias = message;
        addJarvisMessage("\u00BFEn qu\u00E9 horario te queda mejor?");
        jarvisFlow.step = 12;
        break;

      case 12:
        jarvisFlow.userData.horario = message;
        sendJarvisDataToBackend();
        break;

      default:
        addJarvisMessage("Dame un momento...");
        break;
    }
  }, 1000);
}

// ============================================================
// ETAPA 1: CONOCER
// ============================================================
function showSector() {
  jarvisFlow.step = 1;
  addJarvisMessage("\u00BFEn qu\u00E9 sector opera tu empresa?");
  addJarvisOptions([
    { text: 'Manufactura', callback: function() { jarvisFlow.userData.sector = 'Manufactura'; showTamano(); } },
    { text: 'Servicios / Consultor\u00EDa', callback: function() { jarvisFlow.userData.sector = 'Servicios'; showTamano(); } },
    { text: 'Comercio / Retail', callback: function() { jarvisFlow.userData.sector = 'Comercio'; showTamano(); } },
    { text: 'Otro sector', callback: function() { jarvisFlow.userData.sector = 'Otro'; showTamano(); } }
  ]);
}

function showTamano() {
  jarvisFlow.step = 2;
  addJarvisMessage("\u00BFCu\u00E1ntos empleados tiene " + (jarvisFlow.userData.empresa || 'tu empresa') + "?");
  addJarvisOptions([
    { text: 'Menos de 50', callback: function() { jarvisFlow.userData.tamano = '<50'; jarvisFlow.userData.respuestas.push('a'); showPreocupacion(); } },
    { text: '50 a 150', callback: function() { jarvisFlow.userData.tamano = '50-150'; jarvisFlow.userData.respuestas.push('b'); showPreocupacion(); } },
    { text: '150 a 300', callback: function() { jarvisFlow.userData.tamano = '150-300'; jarvisFlow.userData.respuestas.push('c'); showPreocupacion(); } },
    { text: 'M\u00E1s de 300', callback: function() { jarvisFlow.userData.tamano = '300+'; jarvisFlow.userData.respuestas.push('d'); showPreocupacion(); } }
  ]);
}

function showPreocupacion() {
  jarvisFlow.step = 3;
  addJarvisMessage("\u00BFCu\u00E1l es tu principal preocupaci\u00F3n hoy?");
  addJarvisOptions([
    { text: 'Riesgo fiscal (SAT, IVA, ISR)', callback: function() { jarvisFlow.userData.preocupacion = 'fiscal'; jarvisFlow.userData.respuestas.push('fiscal'); showAuditoria(); } },
    { text: 'Riesgo laboral (IMSS, REPSE)', callback: function() { jarvisFlow.userData.preocupacion = 'laboral'; jarvisFlow.userData.respuestas.push('laboral'); showAuditoria(); } },
    { text: 'No tengo visibilidad de riesgos', callback: function() { jarvisFlow.userData.preocupacion = 'visibilidad'; jarvisFlow.userData.respuestas.push('visibilidad'); showAuditoria(); } },
    { text: 'Quiero prevenir problemas', callback: function() { jarvisFlow.userData.preocupacion = 'prevencion'; jarvisFlow.userData.respuestas.push('prevencion'); showAuditoria(); } }
  ]);
}

function showAuditoria() {
  jarvisFlow.step = 4;
  addJarvisMessage("\u00BFHan tenido auditor\u00EDas del SAT o IMSS en los \u00FAltimos 2 a\u00F1os?");
  addJarvisOptions([
    { text: 'S\u00ED', callback: function() { jarvisFlow.userData.respuestas.push('si_auditoria'); showMonitoreo(); } },
    { text: 'No', callback: function() { jarvisFlow.userData.respuestas.push('no_auditoria'); showMonitoreo(); } },
    { text: 'No estoy seguro', callback: function() { jarvisFlow.userData.respuestas.push('no_seguro_auditoria'); showMonitoreo(); } }
  ]);
}

function showMonitoreo() {
  jarvisFlow.step = 5;
  addJarvisMessage("\u00BFActualmente tienen alg\u00FAn sistema para monitorear riesgos?");
  addJarvisOptions([
    { text: 'S\u00ED, tenemos un sistema', callback: function() { jarvisFlow.userData.respuestas.push('tiene_sistema'); showResultadoInicial(); } },
    { text: 'Solo reportes en Excel', callback: function() { jarvisFlow.userData.respuestas.push('excel'); showResultadoInicial(); } },
    { text: 'Lo revisamos cuando hay problema', callback: function() { jarvisFlow.userData.respuestas.push('reactivo'); showResultadoInicial(); } },
    { text: 'No tenemos nada', callback: function() { jarvisFlow.userData.respuestas.push('nada'); showResultadoInicial(); } }
  ]);
}

// ============================================================
// ETAPA 2: DIAGNOSTICAR
// ============================================================
function showResultadoInicial() {
  jarvisFlow.step = 6;
  var nombre = jarvisFlow.userData.nombre || 'amigo';
  var preocupacion = jarvisFlow.userData.preocupacion;
  var riesgo1 = '', riesgo2 = '', riesgo3 = '';

  if (preocupacion === 'fiscal') {
    riesgo1 = '\u26A0\uFE0F Exposici\u00F3n Fiscal (SAT): posibles diferencias en IVA/ISR que podr\u00EDan generar multas del 55% + recargos.';
    riesgo2 = '\u26A0\uFE0F Riesgo Laboral (IMSS): cuotas o registros que podr\u00EDan no estar al d\u00EDa.';
    riesgo3 = '\u26A0\uFE0F Visibilidad limitada: sin monitoreo continuo, los riesgos se acumulan.';
  } else if (preocupacion === 'laboral') {
    riesgo1 = '\u26A0\uFE0F Exposici\u00F3n Laboral (IMSS/REPSE): irregularidades que podr\u00EDan generar multas y embargos.';
    riesgo2 = '\u26A0\uFE0F Riesgo Fiscal asociado: la exposici\u00F3n laboral suele acompa\u00F1arse de contingencias fiscales.';
    riesgo3 = '\u26A0\uFE0F Sin sistema de alerta: los problemas se detectan cuando ya son multas.';
  } else {
    riesgo1 = '\u26A0\uFE0F Riesgo Fiscal: sin visibilidad clara de tu situaci\u00F3n ante el SAT.';
    riesgo2 = '\u26A0\uFE0F Riesgo Laboral: posible exposici\u00F3n ante IMSS/REPSE sin detecci\u00F3n.';
    riesgo3 = '\u26A0\uFE0F Riesgo Operativo: sin monitoreo, los problemas se vuelven crisis.';
  }

  addJarvisMessage("Gracias, " + nombre + ". Con base en lo que me compartes, detecto indicadores de riesgo en 3 \u00E1reas:\n\n" + riesgo1 + "\n\n" + riesgo2 + "\n\n" + riesgo3 + "\n\nLa buena noticia: podemos empezar de forma sencilla.");

  setTimeout(function() { showOfertaDiagnostico(); }, 1500);
}

// ============================================================
// ETAPA 3: OFERTA ACCESIBLE
// ============================================================
function showOfertaDiagnostico() {
  addJarvisMessage("Primero realizamos un Diagn\u00F3stico MESAN \u03A9 para identificar tus principales riesgos y darte claridad sobre d\u00F3nde est\u00E1s expuesto.\n\nEs r\u00E1pido, sin compromiso de membres\u00EDa, y te da un mapa claro de tu situaci\u00F3n.\n\n\u00BFTe interesa?");
  addJarvisOptions([
    { text: 'S\u00ED, quiero el diagn\u00F3stico', callback: function() { jarvisFlow.userData.producto_interes = 'diagnostico_entrada'; showCapturaContacto(); } },
    { text: '\u00BFQu\u00E9 incluye?', callback: showDetalleDiagnostico },
    { text: 'Necesito algo m\u00E1s profundo', callback: showOpcionPremium },
    { text: 'No por ahora', callback: function() { addJarvisMessage("Entendido, " + (jarvisFlow.userData.nombre || '') + ". Cuando quieras retomar, aqu\u00ED estoy. Tambi\u00E9n puedes solicitar info desde el formulario de la p\u00E1gina."); } }
  ]);
}

function showDetalleDiagnostico() {
  addJarvisMessage("El Diagn\u00F3stico MESAN \u03A9 incluye:\n\n\u2022 Evaluaci\u00F3n de riesgo fiscal y laboral\n\u2022 Omega Score (tu \u00EDndice de exposici\u00F3n)\n\u2022 Mapa de riesgos prioritarios\n\u2022 Recomendaciones iniciales\n\nDespu\u00E9s del diagn\u00F3stico, si quieres mantener tus riesgos monitoreados, podemos activar MESAN \u03A9 Monitor con una membres\u00EDa mensual.\n\n\u00BFAgendamos tu diagn\u00F3stico?");
  addJarvisOptions([
    { text: 'S\u00ED, agendar', callback: function() { jarvisFlow.userData.producto_interes = 'diagnostico_entrada'; showCapturaContacto(); } },
    { text: 'Cu\u00E9ntame de la membres\u00EDa', callback: showMembresia },
    { text: 'No por ahora', callback: function() { addJarvisMessage("Sin problema. Aqu\u00ED estoy cuando lo necesites."); } }
  ]);
}

// ============================================================
// ETAPA 4: MEMBRES\u00CDA
// ============================================================
function showMembresia() {
  addJarvisMessage("MESAN \u03A9 Monitor es membres\u00EDa mensual:\n\n\u2022 Monitoreo continuo de riesgos fiscales y laborales\n\u2022 Alertas autom\u00E1ticas antes de que escalen\n\u2022 Dashboard con tu Omega Score en tiempo real\n\u2022 Guardian 24/7 vigilando tu empresa\n\nPrimero hacemos el diagn\u00F3stico para saber exactamente qu\u00E9 monitorear. \u00BFEmpezamos por ah\u00ED?");
  addJarvisOptions([
    { text: 'S\u00ED, empecemos con el diagn\u00F3stico', callback: function() { jarvisFlow.userData.producto_interes = 'diagnostico_entrada'; showCapturaContacto(); } },
    { text: 'Quiero la membres\u00EDa directa', callback: function() { jarvisFlow.userData.producto_interes = 'membresia'; showCapturaContacto(); } },
    { text: 'No por ahora', callback: function() { addJarvisMessage("Entendido. Cuando est\u00E9s listo, aqu\u00ED estoy."); } }
  ]);
}

// ============================================================
// ETAPA 5: PREMIUM
// ============================================================
function showOpcionPremium() {
  jarvisFlow.step = 7;
  addJarvisMessage("Para empresas que necesitan una revisi\u00F3n profunda, tenemos el Diagn\u00F3stico Ejecutivo \u03A9:\n\n\u2022 Revisi\u00F3n exhaustiva de 10 dimensiones de riesgo\n\u2022 Enterprise Survival Index a 12-24 meses\n\u2022 Sesi\u00F3n ejecutiva de 1 hora con especialistas\n\u2022 Plan de acci\u00F3n CEO personalizado\n\nInversi\u00F3n: $15,000 MXN + IVA\nGarant\u00EDa: si no encontramos al menos 1 riesgo cr\u00EDtico, devoluci\u00F3n del 100%.\n\n\u00BFQu\u00E9 prefieres?");
  addJarvisOptions([
    { text: 'Quiero el Diagn\u00F3stico Ejecutivo', callback: function() { jarvisFlow.userData.producto_interes = 'diagnostico_ejecutivo'; showCapturaContacto(); } },
    { text: 'Mejor empiezo con el b\u00E1sico', callback: function() { jarvisFlow.userData.producto_interes = 'diagnostico_entrada'; showCapturaContacto(); } },
    { text: 'Necesito pensarlo', callback: function() { addJarvisMessage("Claro. El diagn\u00F3stico b\u00E1sico siempre est\u00E1 disponible para empezar sin compromiso. Aqu\u00ED estoy."); } }
  ]);
}

// ============================================================
// CAPTURA DE CONTACTO
// ============================================================
function showCapturaContacto() {
  jarvisFlow.step = 9;
  var nombre = jarvisFlow.userData.nombre || 'amigo';
  var producto = jarvisFlow.userData.producto_interes;
  var desc = 'diagn\u00F3stico';
  if (producto === 'membresia') desc = 'membres\u00EDa';
  if (producto === 'diagnostico_ejecutivo') desc = 'Diagn\u00F3stico Ejecutivo';
  addJarvisMessage("Perfecto, " + nombre + ". Para agendar tu " + desc + " necesito unos datos.\n\n\u00BFCu\u00E1l es tu correo electr\u00F3nico?");
}

// ============================================================
// ENVIAR AL BACKEND
// ============================================================
function sendJarvisDataToBackend() {
  showJarvisTyping();

  fetch('https://mesan-api.onrender.com/api/chat/jarvis/lead', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(jarvisFlow.userData)
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    hideJarvisTyping();
    var nombre = jarvisFlow.userData.nombre || '';
    var producto = jarvisFlow.userData.producto_interes;

    if (data.status === 'success') {
      var msgConfirm = '';
      if (producto === 'diagnostico_ejecutivo') {
        msgConfirm = "Tu solicitud de Diagn\u00F3stico Ejecutivo \u03A9 ha sido registrada.\n\nNuestro equipo te contactar\u00E1 en las pr\u00F3ximas horas para confirmar fecha y enviarte la liga de pago.\n\n";
      } else if (producto === 'membresia') {
        msgConfirm = "Tu inter\u00E9s en MESAN \u03A9 Monitor ha sido registrado.\n\nTe contactaremos para activar tu membres\u00EDa y programar el diagn\u00F3stico inicial.\n\n";
      } else {
        msgConfirm = "Tu diagn\u00F3stico MESAN \u03A9 ha sido agendado.\n\nTe enviaremos confirmaci\u00F3n por correo con los siguientes pasos.\n\n";
      }

      if (data.smtp_status === 'SENT') {
        msgConfirm += "Ya te enviamos un correo de confirmaci\u00F3n a " + (jarvisFlow.userData.email || 'tu correo') + ".";
      } else {
        msgConfirm += "La confirmaci\u00F3n por correo est\u00E1 pendiente. No te preocupes, tu solicitud ya qued\u00F3 registrada y nuestro equipo te contactar\u00E1.";
      }

      addJarvisMessage(msgConfirm + "\n\nGracias por confiar en MESAN \u03A9, " + nombre + ".");
    } else {
      addJarvisMessage("Tu solicitud fue registrada, " + nombre + ". Nuestro equipo te contactar\u00E1 pronto para confirmar.\n\n\u00BFTienes alguna otra pregunta?");
    }
  })
  .catch(function() {
    hideJarvisTyping();
    var fallbackUrl = 'https://mesan-api.onrender.com/api/chat/jarvis/lead-fallback?nombre=' + encodeURIComponent(jarvisFlow.userData.nombre) +
      '&empresa=' + encodeURIComponent(jarvisFlow.userData.empresa) +
      '&email=' + encodeURIComponent(jarvisFlow.userData.email) +
      '&telefono=' + encodeURIComponent(jarvisFlow.userData.telefono) +
      '&producto=' + encodeURIComponent(jarvisFlow.userData.producto_interes);

    fetch(fallbackUrl).then(function() {
      addJarvisMessage("Tu solicitud fue registrada, " + (jarvisFlow.userData.nombre || '') + ". La confirmaci\u00F3n por correo est\u00E1 pendiente, pero tu solicitud ya qued\u00F3 guardada.\n\nNuestro equipo te contactar\u00E1 pronto.");
    }).catch(function() {
      addJarvisMessage("Tuvimos un problema t\u00E9cnico, pero no te preocupes. Env\u00EDanos un correo a contacto@mesanomega.com con tu nombre y empresa, y te contactamos de inmediato.\n\nDisculpa la molestia, " + (jarvisFlow.userData.nombre || '') + ".");
    });
  });
}

function showJarvisDuda() {
  jarvisFlow.dudaMode = true;
  addJarvisMessage("Claro, dime tu duda y con gusto te ayudo.");
}
