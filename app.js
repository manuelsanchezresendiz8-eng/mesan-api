// ============================================================
// MESAN Omega -- app.js
// Landing Intelligence Engine
// ============================================================

const API = "https://mesan-api.onrender.com";

async function analizar() {

    const texto = document.getElementById("empresaInput").value.trim();
    const box   = document.getElementById("resultadoBox");

    if (!texto || texto.length < 20) {
        box.innerHTML = `<div class="placeholder" style="color:var(--warn);">
            Describe tu situacion con mas detalle para obtener un diagnostico preciso.<br><br>
            Incluye: sector, montos, entidades involucradas y fechas.
        </div>`;
        return;
    }

    box.innerHTML = `
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--cyan);letter-spacing:2px;">
            <div class="live-dot"></div> MESAN Omega Intelligence Engine
        </div>
        <div style="margin-top:16px;">
            <div id="step-1" style="color:var(--muted);font-size:12px;margin-bottom:8px;">&#x2192; Analizando normativa aplicable...</div>
            <div id="step-2" style="color:var(--muted);font-size:12px;margin-bottom:8px;opacity:0;">&#x2192; Evaluando impacto financiero...</div>
            <div id="step-3" style="color:var(--muted);font-size:12px;margin-bottom:8px;opacity:0;">&#x2192; Correlacionando riesgos operativos...</div>
            <div id="step-4" style="color:var(--muted);font-size:12px;margin-bottom:8px;opacity:0;">&#x2192; Generando plan de contingencia...</div>
        </div>
        <div style="margin-top:20px;background:rgba(0,212,255,.05);border-radius:4px;height:3px;">
            <div id="lp-bar" style="background:var(--cyan);height:3px;border-radius:4px;width:0%;transition:width 0.5s;"></div>
        </div>
    `;

    const steps = ["step-2","step-3","step-4"];
    const pcts  = [30, 60, 85];
    steps.forEach((id, i) => {
        setTimeout(() => {
            const el = document.getElementById(id);
            if (el) el.style.opacity = "1";
            const bar = document.getElementById("lp-bar");
            if (bar) bar.style.width = pcts[i] + "%";
        }, (i+1) * 700);
    });

    try {
        const res  = await fetch(API + "/ai/diagnostico", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ texto, respuestas: {} })
        });

        const d = await res.json();
        const bar = document.getElementById("lp-bar");
        if (bar) bar.style.width = "100%";

        setTimeout(() => renderResultado(d, box), 300);

    } catch(e) {
        box.innerHTML = `<div style="color:var(--alert);font-size:13px;">
            Error de conexion con el motor MESAN Omega.<br>
            <span style="color:var(--muted);font-size:11px;">Verifica tu conexion e intenta de nuevo.</span>
        </div>`;
    }
}

function renderResultado(d, box) {

    const riesgo    = (d.riesgo || "MEDIO").toUpperCase().replace(/[ÁÉÍÓÚ]/g, c => ({Á:"A",É:"E",Í:"I",Ó:"O",Ú:"U"}[c]||c));
    const score     = d.indice_riesgo || 0;
    const impactoMax = (d.impacto_max || 0).toLocaleString("es-MX");
    const impactoMin = (d.impacto_min || 0).toLocaleString("es-MX");

    const colores = { CRITICO: "#EF4444", ALTO: "#F97316", MEDIO: "#00D4FF", BAJO: "#00FF9D" };
    const color   = colores[riesgo] || "#00D4FF";

    const pulseStyle = riesgo === "CRITICO" ? "animation:pulse-ring 1.8s infinite;" : "";

    box.innerHTML = `
        <div style="animation:slideUp 0.4s ease forwards;">

            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;">
                <div>
                    <div style="font-size:10px;color:var(--muted);letter-spacing:2px;margin-bottom:6px;font-family:'JetBrains Mono',monospace;">
                        RIESGO OPERATIVO
                    </div>
                    <div style="font-size:3.5rem;font-weight:800;color:${color};font-family:'JetBrains Mono',monospace;${pulseStyle}">
                        ${score}%
                    </div>
                    <div style="font-size:12px;color:${color};letter-spacing:1px;">${riesgo}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:10px;color:var(--muted);margin-bottom:6px;">EXPOSICION</div>
                    <div style="font-size:1.4rem;font-weight:700;color:var(--alert);font-family:'JetBrains Mono',monospace;">
                        $${impactoMin} – $${impactoMax}
                    </div>
                    <div style="font-size:10px;color:var(--muted);">MXN</div>
                </div>
            </div>

            <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:18px;margin-bottom:16px;">
                <div style="font-size:9px;color:var(--cyan);letter-spacing:2px;margin-bottom:12px;font-family:'JetBrains Mono',monospace;">
                    FACTORES CRITICOS
                </div>
                ${(d.causas||[]).map(c => `
                    <div style="font-size:12px;color:#CBD5E1;margin-bottom:8px;padding-left:12px;border-left:2px solid var(--alert);">
                        ${c}
                    </div>`).join("")}
            </div>

            ${d.analisis_ai ? `
            <div style="background:rgba(0,212,255,.03);border:1px solid rgba(0,212,255,.12);border-radius:14px;padding:18px;margin-bottom:16px;">
                <div style="font-size:9px;color:var(--cyan);letter-spacing:2px;margin-bottom:12px;font-family:'JetBrains Mono',monospace;">
                    ANALISIS ESTRATEGICO IA
                </div>
                <div style="font-size:12px;color:#94A3B8;line-height:1.8;white-space:pre-wrap;">
                    ${d.analisis_ai}
                </div>
            </div>` : ""}

            <div style="text-align:center;margin-top:20px;">
                <div style="font-size:10px;color:var(--muted);margin-bottom:10px;">
                    ¿Prefieres una validacion humana inmediata?
                </div>
                <button onclick="solicitarConsultor()" style="background:transparent;border:1px solid var(--cyan);color:var(--cyan);padding:12px 24px;border-radius:10px;font-size:12px;cursor:pointer;letter-spacing:1px;font-family:'JetBrains Mono',monospace;">
                    HABLAR CON CONSULTOR
                </button>
            </div>

        </div>
    `;
}

function solicitarConsultor() {
    const texto = document.getElementById("empresaInput")?.value || "";
    const msg = encodeURIComponent(`MESAN Omega -- Solicito validacion humana de mi diagnostico.\n\nSituacion: ${texto.substring(0,200)}`);
    window.open(`https://wa.me/526861234567?text=${msg}`, "_blank");
}

// Animaciones CSS dinamicas
const style = document.createElement("style");
style.innerHTML = `
@keyframes slideUp {
    from { opacity:0; transform:translateY(16px); }
    to   { opacity:1; transform:translateY(0); }
}
@keyframes pulse-ring {
    0%   { text-shadow: 0 0 0 rgba(239,68,68,.4); }
    70%  { text-shadow: 0 0 20px rgba(239,68,68,.2); }
    100% { text-shadow: 0 0 0 rgba(239,68,68,0); }
}
`;
document.head.appendChild(style);
