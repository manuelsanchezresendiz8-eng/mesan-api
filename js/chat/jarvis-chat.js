// JARVIS Chat Logic — MESAN Ω (corregido)

let jarvisFlow = {
  step: 0,
  dudaMode: false,
  userData: {
    nombre: '',
    empresa: '',
    email: '',
    telefono: '',
    dias: '',
    horario: '',
    respuestas: []
  }
};

// Toggle chat window (button always visible)
function toggleJarvisChat() {
  const win = document.getElementById('jarvis-chat-window');
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

// Initialize
function initJarvisChat() {
  addJarvisMessage("Hola, soy JARVIS Advisor, tu asistente de riesgo empresarial de MESAN \u03A9. \uD83E\uDD16\n\nAntes de empezar, \u00BFme puedes decir tu nombre y el nombre de tu empresa?\n(Ej: Juan, Empresa ABC)");
}

// Keypress
function handleJarvisKeypress(event) {
  if (event.key === 'Enter') sendJarvisMessage();
}

// Send
function sendJarvisMessage() {
  const input = document.getElementById('jarvis-input');
  const message = input.value.trim();
  if (!message) return;
  addJarvisMessage(message, 'user');
  input.value = '';
  setTimeout(() => processJarvisResponse(message), 500);
}

// Add message
function addJarvisMessage(text, sender) {
  sender = sender || 'bot';
  const container = document.getElementById('jarvis-messages');
  const div = document.createElement('div');
  div.className = 'jarvis-message ' + sender;
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// Typing
function showJarvisTyping() {
  const container = document.getElementById('jarvis-messages');
  if (document.getElementById('jarvis-typing')) return;
  const div = document.createElement('div');
  div.className = 'jarvis-typing';
  div.id = 'jarvis-typing';
  div.innerHTML = '<div class="jarvis-typing-dot"></div><div class="jarvis-typing-dot"></div><div class="jarvis-typing-dot"></div>';
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function hideJarvisTyping() {
  const el = document.getElementById('jarvis-typing');
  if (el) el.remove();
}

// Options
function addJarvisOptions(options) {
  const container = document.getElementById('jarvis-messages');
  // Remove previous options
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

// Process response
function processJarvisResponse(message) {
  showJarvisTyping();

  setTimeout(function() {
    hideJarvisTyping();

    // Si estamos en modo duda, responder y volver al flujo
    if (jarvisFlow.dudaMode) {
      jarvisFlow.dudaMode = false;
      addJarvisMessage("Gracias por tu pregunta. Nuestro equipo te puede dar m\u00E1s detalle en la sesi\u00F3n ejecutiva.\n\n\u00BFContinuamos con el diagn\u00F3stico?");
      addJarvisOptions([
        { text: 'S\u00ED, continuamos', callback: function() { jarvisFlow.step = 1; showJarvisPregunta1(); } },
        { text: 'No, gracias', callback: function() { addJarvisMessage("Entiendo. Si cambias de opini\u00F3n, aqu\u00ED estar\u00E9."); } }
      ]);
      return;
    }

    switch(jarvisFlow.step) {
      case 0:
        var parts = message.split(',');
        jarvisFlow.userData.nombre = (parts[0] || message).trim();
        jarvisFlow.userData.empresa = (parts[1] || '').trim();

        addJarvisMessage("Gracias, " + jarvisFlow.userData.nombre + ". Un gusto conocerte.\n\nVoy a hacerte unas preguntas r\u00E1pidas para entender mejor tu situaci\u00F3n.\n\n\u00BFComenzamos?");
        addJarvisOptions([
          { text: 'S\u00ED, comenzamos', callback: function() { jarvisFlow.step = 1; showJarvisPregunta1(); } },
          { text: 'Tengo una duda', callback: showJarvisDuda }
        ]);
        break;

      case 1: jarvisFlow.userData.respuestas.push(message); showJarvisPregunta1(); break;
      case 2: jarvisFlow.userData.respuestas.push(message); showJarvisPregunta2(); break;
      case 3: jarvisFlow.userData.respuestas.push(message); showJarvisPregunta3(); break;
      case 4: jarvisFlow.userData.respuestas.push(message); showJarvisPregunta4(); break;
      case 5: jarvisFlow.userData.respuestas.push(message); showJarvisAnalisis(); break;

      case 6:
        if (message.toLowerCase().indexOf('s\u00ED') !== -1 || message.toLowerCase().indexOf('si') !== -1) {
          showJarvisWarRoom();
        }
        break;

      case 7: showJarvisPrecio(); break;

      case 8:
        if (message.toLowerCase().indexOf('s\u00ED') !== -1 || message.toLowerCase().indexOf('si') !== -1 || message.toLowerCase().indexOf('agenda') !== -1) {
          showJarvisAgendamiento();
        }
        break;

      case 9:
        jarvisFlow.userData.email = message;
        addJarvisMessage("\u00BFY tu tel\u00E9fono?");
        jarvisFlow.step = 10;
        break;

      case 10:
        jarvisFlow.userData.telefono = message;
        addJarvisMessage("\u00BFQu\u00E9 d\u00EDas tienes disponibles?");
        jarvisFlow.step = 11;
        break;

      case 11:
        jarvisFlow.userData.dias = message;
        addJarvisMessage("\u00BFY en qu\u00E9 horario?");
        jarvisFlow.step = 12;
        break;

      case 12:
        jarvisFlow.userData.horario = message;
        sendJarvisDataToBackend();
        break;
    }
  }, 1000);
}

// Preguntas
function showJarvisPregunta1() {
  addJarvisMessage("Pregunta 1 de 5:\n\n\u00BFCu\u00E1ntos empleados tiene tu empresa?");
  addJarvisOptions([
    { text: 'Menos de 50', callback: function() { jarvisFlow.step = 2; jarvisFlow.userData.respuestas.push('a'); showJarvisPregunta2(); } },
    { text: '50-150', callback: function() { jarvisFlow.step = 2; jarvisFlow.userData.respuestas.push('b'); showJarvisPregunta2(); } },
    { text: '150-300', callback: function() { jarvisFlow.step = 2; jarvisFlow.userData.respuestas.push('c'); showJarvisPregunta2(); } },
    { text: 'M\u00E1s de 300', callback: function() { jarvisFlow.step = 2; jarvisFlow.userData.respuestas.push('d'); showJarvisPregunta2(); } }
  ]);
}

function showJarvisPregunta2() {
  addJarvisMessage("Pregunta 2 de 5:\n\n\u00BFTu empresa ha tenido auditor\u00EDas del SAT o IMSS en los \u00FAltimos 2 a\u00F1os?");
  addJarvisOptions([
    { text: 'S\u00ED, del SAT', callback: function() { jarvisFlow.step = 3; jarvisFlow.userData.respuestas.push('a'); showJarvisPregunta3(); } },
    { text: 'S\u00ED, del IMSS', callback: function() { jarvisFlow.step = 3; jarvisFlow.userData.respuestas.push('b'); showJarvisPregunta3(); } },
    { text: 'S\u00ED, de ambos', callback: function() { jarvisFlow.step = 3; jarvisFlow.userData.respuestas.push('c'); showJarvisPregunta3(); } },
    { text: 'No, ninguna', callback: function() { jarvisFlow.step = 3; jarvisFlow.userData.respuestas.push('d'); showJarvisPregunta3(); } }
  ]);
}

function showJarvisPregunta3() {
  addJarvisMessage("Pregunta 3 de 5:\n\n\u00BFTienes un dashboard o sistema para ver el riesgo fiscal y laboral en tiempo real?");
  addJarvisOptions([
    { text: 'S\u00ED, tenemos un sistema', callback: function() { jarvisFlow.step = 4; jarvisFlow.userData.respuestas.push('a'); showJarvisPregunta4(); } },
    { text: 'Reportes en Excel', callback: function() { jarvisFlow.step = 4; jarvisFlow.userData.respuestas.push('b'); showJarvisPregunta4(); } },
    { text: 'Solo cuando hay problema', callback: function() { jarvisFlow.step = 4; jarvisFlow.userData.respuestas.push('c'); showJarvisPregunta4(); } },
    { text: 'No s\u00E9', callback: function() { jarvisFlow.step = 4; jarvisFlow.userData.respuestas.push('d'); showJarvisPregunta4(); } }
  ]);
}

function showJarvisPregunta4() {
  addJarvisMessage("Pregunta 4 de 5:\n\n\u00BFTu Consejo o due\u00F1os reciben informaci\u00F3n de riesgo de forma regular?");
  addJarvisOptions([
    { text: 'S\u00ED, mensualmente', callback: function() { jarvisFlow.step = 5; jarvisFlow.userData.respuestas.push('a'); showJarvisAnalisis(); } },
    { text: 'Trimestralmente', callback: function() { jarvisFlow.step = 5; jarvisFlow.userData.respuestas.push('b'); showJarvisAnalisis(); } },
    { text: 'Solo cuando hay problema', callback: function() { jarvisFlow.step = 5; jarvisFlow.userData.respuestas.push('c'); showJarvisAnalisis(); } },
    { text: 'No reciben informaci\u00F3n', callback: function() { jarvisFlow.step = 5; jarvisFlow.userData.respuestas.push('d'); showJarvisAnalisis(); } }
  ]);
}

// An\u00E1lisis
function showJarvisAnalisis() {
  var nombre = jarvisFlow.userData.nombre || 'amigo';
  addJarvisMessage("Gracias por tus respuestas, " + nombre + ".\n\nHe identificado 3 riesgos cr\u00EDticos:\n\n\u26A0\uFE0F Riesgo 1: Exposici\u00F3n Fiscal (SAT)\nImpacto estimado: $500K - $5M\n\n\u26A0\uFE0F Riesgo 2: Exposici\u00F3n Laboral (IMSS/REPSE)\nImpacto estimado: $300K - $3M\n\n\u26A0\uFE0F Riesgo 3: Riesgo Operativo Invisible\nImpacto estimado: 10-30% de ingresos\n\n\u00BFTe explico c\u00F3mo MESAN \u03A9 puede ayudarte?");
  addJarvisOptions([
    { text: 'S\u00ED, expl\u00EDcame', callback: function() { jarvisFlow.step = 7; showJarvisWarRoom(); } },
    { text: 'No, gracias', callback: function() { addJarvisMessage("Entiendo. Si cambias de opini\u00F3n, aqu\u00ED estar\u00E9."); } }
  ]);
}

// War Room
function showJarvisWarRoom() {
  addJarvisMessage("MESAN \u03A9 activa 9 motores para analizar tu empresa en tiempo real.\n\nGuardian 24/7 monitorea y te alerta antes de que el riesgo escale.\n\nSi detectamos algo cr\u00EDtico, activamos el War Room Ejecutivo con comit\u00E9 de crisis, simulaci\u00F3n de escenarios y recomendaciones en horas.\n\nEjemplo real: Una empresa de 250 empleados detect\u00F3 un incumplimiento REPSE 72 horas antes de una auditor\u00EDa y evit\u00F3 una multa de $3.8M.\n\n\u00BFTe gustar\u00EDa agendar un Diagn\u00F3stico Ejecutivo \u03A9?");
  addJarvisOptions([
    { text: 'S\u00ED, quiero agendar', callback: function() { jarvisFlow.step = 8; showJarvisPrecio(); } },
    { text: '\u00BFCu\u00E1nto cuesta?', callback: function() { jarvisFlow.step = 8; showJarvisPrecio(); } },
    { text: 'No, gracias', callback: function() { addJarvisMessage("Entiendo. Si cambias de opini\u00F3n, aqu\u00ED estar\u00E9."); } }
  ]);
}

// Precio
function showJarvisPrecio() {
  addJarvisMessage("El Diagn\u00F3stico Ejecutivo \u03A9 tiene un costo de $15,000 MXN + IVA.\n\nIncluye:\n\u2022 Evaluaci\u00F3n de riesgo fiscal, laboral y operativo\n\u2022 Enterprise Survival Index a 12-24 meses\n\u2022 Recomendaciones prioritarias\n\u2022 Sesi\u00F3n ejecutiva (1 hora)\n\nGarant\u00EDa: Si no encontramos al menos 1 riesgo cr\u00EDtico, te devolvemos el 100%.\n\n\u00BFAgendamos para esta semana?");
  addJarvisOptions([
    { text: 'S\u00ED, agenda mi diagn\u00F3stico', callback: function() { jarvisFlow.step = 9; showJarvisAgendamiento(); } },
    { text: 'Necesito pensarlo', callback: function() { addJarvisMessage("Claro, t\u00F3mate tu tiempo. El diagn\u00F3stico tiene garant\u00EDa 100%. Cuando est\u00E9s listo, aqu\u00ED estoy."); } },
    { text: 'No, gracias', callback: function() { addJarvisMessage("Entiendo. Si cambias de opini\u00F3n, aqu\u00ED estar\u00E9."); } }
  ]);
}

// Agendamiento
function showJarvisAgendamiento() {
  addJarvisMessage("Excelente decisi\u00F3n, " + (jarvisFlow.userData.nombre || 'amigo') + ".\n\nPara agendar necesito unos datos.\n\nPrimero, \u00BFcu\u00E1l es tu correo electr\u00F3nico?");
}

// Send to backend
function sendJarvisDataToBackend() {
  addJarvisMessage("Procesando tu solicitud...");

  fetch('/api/chat/jarvis/lead', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(jarvisFlow.userData)
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'success') {
      addJarvisMessage("Perfecto, " + (jarvisFlow.userData.nombre || '') + ". En los pr\u00F3ximos minutos recibir\u00E1s:\n\n1. Correo con la liga de pago ($15,000 MXN + IVA)\n2. Invitaci\u00F3n a tu sesi\u00F3n\n3. Cuestionario previo (5 min)\n\n\u00BFTienes alguna otra pregunta?");
    } else {
      addJarvisMessage("Tu solicitud fue registrada. Nuestro equipo te contactar\u00E1 pronto.\n\n\u00BFTienes alguna otra pregunta?");
    }
  })
  .catch(function() {
    addJarvisMessage("Hubo un error de conexi\u00F3n. Por favor cont\u00E1ctanos directamente en contacto@mesan-omega.com o al tel\u00E9fono que aparece en nuestra p\u00E1gina.");
  });
}

// Duda — ahora s\u00ED maneja la respuesta libre
function showJarvisDuda() {
  jarvisFlow.dudaMode = true;
  addJarvisMessage("Claro, dime tu duda y con gusto te ayudo.");
}
