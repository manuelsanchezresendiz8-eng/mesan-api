# app/agents/jarvis_market_agent.py
import json
from app.services.jarvis_core import JarvisCore

class JarvisMarketAgent:
    def __init__(self):
        self.core = JarvisCore()

    async def analizar_lead_y_generar_pitch(self, datos_empresa: dict) -> dict:
        prompt_sistema = (
            "Eres Jarvis, el estratega de IA de MESAN Enterprise. "
            "Analiza los datos de un lead corporativo y genera un angulo de venta "
            "basado en SOBERANIA TECNOLOGICA y reduccion de costos. "
            "Responde SOLO con JSON con las llaves: "
            "'punto_dolor_estimado', 'estrategia_aproximacion', 'asunto_correo_frio', 'cuerpo_correo_frio'."
        )
        prompt_usuario = f"""
Analiza el siguiente prospecto:
- Empresa: {datos_empresa.get('nombre')}
- Sector: {datos_empresa.get('sector')}
- Empleados: {datos_empresa.get('empleados')}
- Ubicacion: {datos_empresa.get('ubicacion')}
- Puesto contacto: {datos_empresa.get('puesto_contacto')}

Diseña el pitch demostrando por que la infraestructura local de MESAN Omega es superior a soluciones en la nube.
"""
        respuesta_raw = await self.core.ejecutar_comando(prompt_sistema, prompt_usuario)
        return json.loads(respuesta_raw)
