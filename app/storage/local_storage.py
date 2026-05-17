# app/storage/local_storage.py — MESAN Ω
import os
import json
import hashlib
import uuid
from datetime import datetime

class LocalStorageManager:
    def __init__(self, base_data_dir="data"):
        self.base_dir = base_data_dir
        self._ensure_infrastructure()

    def _ensure_infrastructure(self):
        for folder in ["cotizaciones", "auditorias", "usmca", "logs"]:
            path = os.path.join(self.base_dir, folder)
            if not os.path.exists(path):
                os.makedirs(path)

    def guardar_registro_soberano(self, modulo: str, identificador: str, datos: dict) -> str:
        folder_path = os.path.join(self.base_dir, modulo)
        if not os.path.exists(folder_path):
            return "ERROR_MODULO_INEXISTENTE"

        payload_str = json.dumps(datos, ensure_ascii=False, sort_keys=True)
        checksum    = hashlib.sha256(payload_str.encode()).hexdigest()
        record_uuid = str(uuid.uuid4())

        datos["_meta_omega"] = {
            "uuid":            record_uuid,
            "checksum":        checksum,
            "timestamp":       datetime.now().isoformat(),
            "cloud_sync":      False,
            "origen_hardware": "LOCAL_CORE_M715S"
        }

        file_name = f"{identificador}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        full_path = os.path.join(folder_path, file_name)

        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)

        return full_path
