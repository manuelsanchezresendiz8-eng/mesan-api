const API="https://mesan-api.onrender.com";
let K="";

const saved=localStorage.getItem("mk");
if(saved){K=saved;init();}

function login(){
  K=document.getElementById("key").value.trim();
  if(!K){alert("Ingresa tu API Key");return;}
  localStorage.setItem("mk",K);
  init();
}

function init(){
  document.getElementById("login").style.display="none";
  document.getElementById("app").style.display="block";
  load();
}

function logout(){
  localStorage.removeItem("mk");
  location.reload();
}

async function load(){
  try{
    const r=await fetch(API+"/leads",{headers:{"api-key":K}});
    if(r.status===403){alert("API Key invalida");logout();return;}
    const d=await r.json();
    const leads=d.leads||[];
    document.getElementById("k1").innerText=leads.length;
    document.getElementById("k2").innerText=leads.filter(l=>(l.clasificacion||"").toUpperCase()==="ALTO").length;
    document.getElementById("k4").innerText=leads.filter(l=>l.estatus==="cerrado").length;
    const t=leads.reduce((s,l)=>s+(l.impacto_max||0),0);
    document.getElementById("k3").innerText=t>=1000000?"$"+(t/1000000).toFixed(1)+"M":"$"+(t/1000).toFixed(0)+"K";
    renderLeads(leads);
  }catch(e){console.error(e);}
}

function renderLeads(leads){
  const c=document.getElementById("leads");
  c.innerHTML="";
  if(!leads.length){c.innerHTML="<p style='color:#4A8FA8'>Sin leads aun</p>";return;}
  leads.sort((a,b)=>(b.impacto_max||0)-(a.impacto_max||0)).forEach(l=>{
    const cls=(l.clasificacion||"").toUpperCase()==="ALTO"?"alto":(l.clasificacion||"").toUpperCase()==="MEDIO"?"medio":"";
    const tel=(l.telefono||"").replace(/\D/g,"");
    const div=document.createElement("div");
    div.className="card "+cls;
    div.innerHTML=
      "<b>"+(l.nombre||"Sin nombre")+"</b>"+
      "<small>"+(l.giro||"—")+"</small>"+
      "<div class='imp'>$"+(l.impacto_max||0).toLocaleString()+" MXN</div>"+
      "<small>"+(l.clasificacion||"N/A")+" | "+(l.estatus||"nuevo")+"</small>"+
      "<div class='acciones'>"+
      (tel?"<button onclick='wa(\""+tel+"\")'>WA</button>":"")+
      "<button onclick='mover(\""+l.id+"\",\"contactado\")'>→</button>"+
      "<button onclick='mover(\""+l.id+"\",\"cerrado\")'>✔</button>"+
      "</div>";
    c.appendChild(div);
  });
}

async function diagnosticar(){
  const texto=document.getElementById("q").value;
  if(!texto)return;
  document.getElementById("out").innerHTML="<p style='color:#4A8FA8'>Analizando...</p>";
  try{
    const r=await fetch(API+"/ai/diagnostico",{
      method:"POST",
      headers:{"Content-Type":"application/json","api-key":K},
      body:JSON.stringify({texto:texto,respuestas:{}})
    });
    const d=await r.json();
    document.getElementById("out").innerHTML=
      "<b style='color:#00E5FF'>"+d.industria+" | "+d.riesgo+"</b><br>"+
      "Impacto: $"+(d.impacto_min||0).toLocaleString()+" - $"+(d.impacto_max||0).toLocaleString()+" MXN<br><br>"+
      (d.analisis_ai||"").replace(/\n/g,"<br>");
  }catch(e){
    document.getElementById("out").innerHTML="<p style='color:#FF3B3B'>Error al analizar</p>";
  }
}

async function mover(id,est){
  try{
    await fetch(API+"/lead/"+id,{
      method:"PUT",
      headers:{"Content-Type":"application/json","api-key":K},
      body:JSON.stringify({estatus:est})
    });
    load();
  }catch(e){console.error(e);}
}

function wa(tel){
  window.open("https://wa.me/52"+tel);
}

document.getElementById("key").onkeypress=function(e){
  if(e.key==="Enter")login();
};