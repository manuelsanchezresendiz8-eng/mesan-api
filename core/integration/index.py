<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>MESAN Ω | Enterprise Risk Intelligence</title>
<meta name="description" content="MESAN Ω detecta riesgos fiscales, laborales, financieros y operativos antes de que se conviertan en pérdidas millonarias.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{font-family:'Inter',sans-serif;background:#08111d;color:#fff;line-height:1.6;overflow-x:hidden;}
body::before{content:"";position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle at top right,#143b6a 0%,transparent 45%),radial-gradient(circle at bottom left,#072544 0%,transparent 45%),linear-gradient(#08111d,#05080d);z-index:-2;}
body::after{content:"";position:fixed;width:100%;height:100%;background-image:linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);background-size:45px 45px;opacity:.30;z-index:-1;}
header{display:flex;justify-content:space-between;align-items:center;padding:22px 80px;position:sticky;top:0;background:rgba(8,17,29,.90);backdrop-filter:blur(14px);border-bottom:1px solid rgba(255,255,255,.06);z-index:999;transition:.3s;}
.logo{font-size:26px;font-weight:800;letter-spacing:1px;text-decoration:none;color:#fff;}
.logo span{color:#00D8FF;}
nav{display:flex;gap:32px;align-items:center;}
nav a{text-decoration:none;color:#bcc8d8;font-size:15px;font-weight:500;transition:.3s;position:relative;}
nav a::after{content:"";position:absolute;bottom:-4px;left:0;width:0;height:2px;background:#00D8FF;transition:.3s;}
nav a:hover{color:#fff;}
nav a:hover::after{width:100%;}
.btn-nav{padding:12px 24px;background:#00D8FF;color:#08111d;font-weight:700;font-size:14px;border-radius:8px;text-decoration:none;transition:.3s;white-space:nowrap;}
.btn-nav:hover{transform:translateY(-2px);box-shadow:0 8px 25px rgba(0,216,255,.40);}
.hamburger{display:none;flex-direction:column;gap:5px;cursor:pointer;padding:5px;}
.hamburger span{display:block;width:24px;height:2px;background:#fff;transition:.3s;}
.mobile-menu{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:#08111d;z-index:9999;flex-direction:column;justify-content:center;align-items:center;gap:40px;}
.mobile-menu.open{display:flex;}
.mobile-menu a{font-size:24px;font-weight:700;color:#fff;text-decoration:none;}
.mobile-menu .close{position:absolute;top:30px;right:30px;font-size:32px;cursor:pointer;color:#fff;}
main{min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;}
p.placeholder{color:#8da0b6;font-size:18px;}
@media(max-width:1000px){header{padding:18px 24px;}nav{display:none;}.hamburger{display:flex;}}
</style>
</head>
<body>

<header>
  <a class="logo" href="#">MESAN <span>Ω</span></a>
  <nav>
    <a href="#inicio">Inicio</a>
    <a href="#como-funciona">Cómo funciona</a>
    <a href="#motores">Motores</a>
    <a href="#sectores">Sectores</a>
    <a href="#war-room">War Room</a>
    <a href="#diagnostico">Diagnóstico</a>
    <a href="#contacto">Contacto</a>
    <a class="btn-nav" href="#contacto">Solicitar Diagnóstico</a>
  </nav>
  <div class="hamburger" onclick="toggleMenu()">
    <span></span><span></span><span></span>
  </div>
</header>

<div class="mobile-menu" id="mobileMenu">
  <span class="close" onclick="toggleMenu()">✕</span>
  <a href="#inicio" onclick="toggleMenu()">Inicio</a>
  <a href="#como-funciona" onclick="toggleMenu()">Cómo funciona</a>
  <a href="#motores" onclick="toggleMenu()">Motores</a>
  <a href="#sectores" onclick="toggleMenu()">Sectores</a>
  <a href="#war-room" onclick="toggleMenu()">War Room</a>
  <a href="#diagnostico" onclick="toggleMenu()">Diagnóstico</a>
  <a href="#contacto" onclick="toggleMenu()">Contacto</a>
  <a class="btn-nav" href="#contacto" onclick="toggleMenu()">Solicitar Diagnóstico</a>
</div>

<main id="inicio">
  <p class="placeholder">MESAN Ω — Módulos cargando...</p>
</main>

<script>
function toggleMenu(){
  document.getElementById('mobileMenu').classList.toggle('open');
}
</script>
</body>
</html>
 
 