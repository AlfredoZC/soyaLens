import os
import sys

# Asegurar que se puede importar desde el root del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.pipeline import detect_grains, summarize, generate_certificate

def main():
    # Usaremos una imagen de test del dataset para probar
    test_image_dir = os.path.join("ai", "dataset", "test", "images")
    
    # Buscar cualquier archivo .jpg en la carpeta de test
    if not os.path.exists(test_image_dir):
        print(f"Error: No se encontró la carpeta {test_image_dir}")
        return
        
    images = [f for f in os.listdir(test_image_dir) if f.endswith(".jpg")]
    if not images:
        print(f"Error: No hay imágenes JPG en {test_image_dir}")
        return
        
    test_image = os.path.join(test_image_dir, images[0])
    print(f"--- INICIANDO PRUEBA DEL PIPELINE CON {images[0]} ---")
    
    # 1. Detectar granos (Visión con SAHI)
    print("\n1. Ejecutando detect_grains()...")
    detections = detect_grains(test_image)
    print(f"✅ Se detectaron {len(detections)} granos.")
    if detections:
        print(f"   Ejemplo de detección: {detections[0]}")
        
    # 2. Resumir (Matemática)
    print("\n2. Ejecutando summarize()...")
    breakdown = summarize(detections)
    print(f"✅ Desglose: {breakdown}")
    
    # 3. Generar Certificado (Gemini + Tool Calling)
    print("\n3. Ejecutando generate_certificate()...")
    try:
        cert = generate_certificate(breakdown, lot_id="L-TEST-01", supplier="Granja Demo")
        print("\n✅ CERTIFICADO GENERADO CON ÉXITO:")
        print(f"   Veredicto: {cert.verdict.upper()}")
        print(f"   Descuento: {cert.discount_pct}%")
        print(f"   Justificación: {cert.justification}")
        print(f"   ID Muestra: {cert.sample_id}")
    except Exception as e:
        print(f"❌ Error al generar certificado: {e}")

if __name__ == "__main__":
    main()
