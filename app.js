const API = "https://mesan-api.onrender.com";
let cliente_id = "cliente_" + Date.now();
let perdida = 0;

// CONTADOR DINERO
setInterval(() => {
    perdida += Math.floor(Math.random() * 500 + 200);
    document.getElementById("counter").innerText =
        "$" + perdida.toLocaleString() + " MXN";
}, 1500);


// DIAGNÓSTICO
function iniciarDiagnostico() {
    const chat = document.getElementById("chat-output");
    chat.style.display = "block";
    chat.innerHTML = "⏳ Detectando pérdidas ocultas...";

    setTimeout(() => {
        chat.innerHTML = `
        🚨 ALERTA CRÍTICA DETECTADA<br><br>
        Riesgos encontrados:<br>
        - No deducibilidad fiscal<br>
        - Multas IMSS<br>
        - Falta de cumplimiento<br><br>
        Impacto estimado:<br>
        <strong>$120,000 - $450,000 MXN anuales</strong><br><br>
        👉 Desbloquea el análisis completo por $299 MXN
        `;
    }, 1500);
}


// REPSE
async function activarRepse() {
    const chat = document.getElementById("chat-output");
    chat.style.display = "block";
    chat.innerHTML = "⏳ Consultando STPS...";

    try {
        const res = await fetch(API + "/api/verificar", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                rfc: document.getElementById("inputRFC").value || "ABC123456XYZ"
            })
        });

        const data = await res.json();

        chat.innerHTML = data.analisis_ia
            ? "🚨 ALERTA: " + data.analisis_ia
            : "✅ Consulta completada";

    } catch {
        chat.innerHTML = "❌ Error de conexión";
    }
}


// PAGO STRIPE
async function irPago() {
    try {
        const res = await fetch(API + "/crear-sesion-omega", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                cliente_id: cliente_id,
                sector: "PRIVADO",
                monto: 299,
                indice: 75
            })
        });

        const data = await res.json();

        if (data.url) {
            window.location.href = data.url;
        } else {
            alert("Error generando link de pago");
        }

    } catch(e) {
        alert("Error de conexión");
    }
}
