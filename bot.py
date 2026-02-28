import requests
import json

BASE_URL = "http://localhost:8008"
CREDENCIALES = ('admin', 'admin')

def motor_decisiones_dinamico():
    print("="*60)
    print(" MOTOR DE DECISIONES AUTONOMO (HackUDC) ")
    print("="*60)
    
    problema_usuario = input("\nIntroduce el problema de negocio a resolver:\n> ")
    
    print("\nFASE 1: Descubriendo el entorno de datos y metricas...")
    payload_meta = {
        "question": f"Actuas como un analista de datos. El usuario tiene este problema de negocio: '{problema_usuario}'. Identifica que tablas en el catalogo contienen la informacion necesaria para resolverlo."
    }
    
    try:
        respuesta_meta = requests.post(f"{BASE_URL}/answerMetadataQuestion", json=payload_meta, auth=CREDENCIALES)
        respuesta_meta.raise_for_status()
        datos_meta = respuesta_meta.json()
        
        tablas_usadas = datos_meta.get('tables_used', [])
        tabla_descubierta = tablas_usadas[0] if tablas_usadas else "las tablas musicales del catalogo"
        
        print(f"Entorno analizado. Tabla seleccionada por la IA: {tabla_descubierta}\n")
        
    except Exception as e:
        print(f"Error en Fase 1: {e}")
        return

    print("FASE 2: Ejecutando consultas SQL y tomando la decision...")
    payload_datos = {
        "question": f"El problema de negocio a resolver es este: '{problema_usuario}'. Usando exclusivamente la tabla {tabla_descubierta}, genera una consulta SQL para encontrar el top 3 de canciones que mejor se adapten a los requisitos. Ejecutala y devuelveme una recomendacion final justificada explicando por que ese artista es la mejor opcion."
    }
    
    try:
        respuesta_datos = requests.post(f"{BASE_URL}/answerDataQuestion", json=payload_datos, auth=CREDENCIALES)
        respuesta_datos.raise_for_status()
        datos_finales = respuesta_datos.json()
        
        print("\n=== CONCLUSION Y RECOMENDACION ===\n")
        print(datos_finales.get('answer', 'Error al generar la respuesta.'))
        
        print("\n(Consulta SQL generada y ejecutada de forma autonoma:)")
        print(datos_finales.get('sql_query', 'N/A'))
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"Error en Fase 2: {e}")

if __name__ == "__main__":
    motor_decisiones_dinamico()
