"""
Servicio de cálculo de riego outdoor basado en condiciones meteorológicas.

Este módulo ajusta la frecuencia de riego de plantas outdoor considerando:
- Temperatura ambiente
- Precipitación
- Humedad relativa
- Velocidad del viento
"""

from datetime import date


def calcular_ajuste_por_clima(planta, clima_dia):
    """
    Calcula el ajuste en días para el próximo riego basado en condiciones climáticas.
    
    Args:
        planta: Instancia del modelo Planta
        clima_dia: Dict con datos del clima del día
                   {
                       'temperatura_max': float,
                       'temperatura_min': float,
                       'humedad_promedio': float,
                       'precipitacion_mm': float,
                       'velocidad_viento_kmh': float
                   }
    
    Returns:
        dict: {
            'ajuste_dias': float,  # Días a ajustar (negativo = adelantar, positivo = atrasar)
            'resetear_riego': bool,  # Si debe considerarse como regado hoy
            'motivo': str  # Explicación del ajuste
        }
    """
    temp_max = clima_dia.get('temperatura_max', 25)
    temp_min = clima_dia.get('temperatura_min', 15)
    humedad = clima_dia.get('humedad_promedio', 50)
    precipitacion = clima_dia.get('precipitacion_mm', 0)
    viento = clima_dia.get('velocidad_viento_kmh', 0)
    
    ajuste_dias = 0
    motivos = []
    resetear = False
    
    # ==================== 1. PRECIPITACIÓN (factor más importante) ====================
    if precipitacion > 15:
        # Lluvia intensa: resetear como si se hubiera regado hoy
        resetear = True
        motivos.append(f"Lluvia intensa ({precipitacion:.1f}mm) - se considera como riego")
        return {
            'ajuste_dias': 0,
            'resetear_riego': True,
            'motivo': '; '.join(motivos)
        }
    elif precipitacion > 5:
        # Lluvia moderada: atrasar riego
        ajuste_dias += 1
        motivos.append(f"Lluvia moderada ({precipitacion:.1f}mm) +1 día")
    elif precipitacion > 2:
        # Lluvia leve: atrasar medio día
        ajuste_dias += 0.5
        motivos.append(f"Lluvia leve ({precipitacion:.1f}mm) +0.5 días")
    
    # ==================== 2. TEMPERATURA ====================
    if temp_max > 35:
        # Calor extremo: adelantar 2 días
        ajuste_dias -= 2
        motivos.append(f"Calor extremo ({temp_max:.1f}°C) -2 días")
    elif temp_max > 30:
        # Calor alto: adelantar 1 día
        ajuste_dias -= 1
        motivos.append(f"Calor alto ({temp_max:.1f}°C) -1 día")
    elif temp_max > 25:
        # Temperatura moderada-alta: adelantar medio día
        ajuste_dias -= 0.5
        motivos.append(f"Temperatura alta ({temp_max:.1f}°C) -0.5 días")
    elif temp_max < 15:
        # Frío: atrasar medio día
        ajuste_dias += 0.5
        motivos.append(f"Temperatura baja ({temp_max:.1f}°C) +0.5 días")
    
    # ==================== 3. HUMEDAD ====================
    if humedad < 30:
        # Humedad muy baja: más evaporación
        ajuste_dias -= 0.5
        motivos.append(f"Humedad baja ({humedad:.1f}%) -0.5 días")
    elif humedad > 80:
        # Humedad alta: menos evaporación
        ajuste_dias += 0.5
        motivos.append(f"Humedad alta ({humedad:.1f}%) +0.5 días")
    
    # ==================== 4. VIENTO ====================
    if viento > 25:
        # Viento fuerte: más evaporación
        ajuste_dias -= 0.5
        motivos.append(f"Viento fuerte ({viento:.1f}km/h) -0.5 días")
    elif viento > 40:
        # Viento muy fuerte: mucha más evaporación
        ajuste_dias -= 1
        motivos.append(f"Viento muy fuerte ({viento:.1f}km/h) -1 día")
    
    # Limitar ajuste máximo a ±3 días
    ajuste_dias = max(-3, min(3, ajuste_dias))
    
    if not motivos:
        motivos.append("Condiciones normales - sin ajuste")
    
    return {
        'ajuste_dias': ajuste_dias,
        'resetear_riego': resetear,
        'motivo': '; '.join(motivos)
    }


def recalcular_fecha_riego_outdoor(planta, registro_clima):
    """
    Recalcula la fecha del próximo riego para una planta outdoor.
    
    Args:
        planta: Instancia del modelo Planta
        registro_clima: Instancia del modelo RegistroClima con datos del día
    
    Returns:
        dict: {
            'dias_restantes': int,
            'fecha_proximo_riego': date,
            'ajuste_aplicado': float,
            'motivo': str,
            'reseteo_por_lluvia': bool
        }
    """
    from datetime import timedelta
    
    # Obtener datos del clima
    clima_dia = {
        'temperatura_max': registro_clima.temperatura_max,
        'temperatura_min': registro_clima.temperatura_min,
        'humedad_promedio': registro_clima.humedad_promedio,
        'precipitacion_mm': registro_clima.precipitacion_mm,
        'velocidad_viento_kmh': registro_clima.velocidad_viento_kmh,
    }
    
    # Calcular ajuste
    resultado_ajuste = calcular_ajuste_por_clima(planta, clima_dia)
    
    # Si hay que resetear por lluvia intensa
    if resultado_ajuste['resetear_riego']:
        planta.fecha_ultimo_riego = registro_clima.fecha
        planta.save()
        
        # Recalcular desde cero
        datos_riego = planta.calculos_riego()
        
        return {
            'dias_restantes': datos_riego['days_left'],
            'fecha_proximo_riego': datos_riego['next_watering_date'],
            'ajuste_aplicado': 0,
            'motivo': resultado_ajuste['motivo'],
            'reseteo_por_lluvia': True
        }
    
    # Obtener cálculo base actual
    datos_base = planta.calculos_riego()
    dias_base = datos_base['frequency_days']
    
    # Aplicar ajuste
    ajuste = resultado_ajuste['ajuste_dias']
    dias_ajustados = max(1, dias_base + ajuste)  # Mínimo 1 día entre riegos
    
    # Calcular nueva fecha de próximo riego
    dias_desde_ultimo = (date.today() - planta.fecha_ultimo_riego).days
    dias_restantes = max(0, int(dias_ajustados - dias_desde_ultimo))
    fecha_proximo = date.today() + timedelta(days=dias_restantes)
    
    return {
        'dias_restantes': dias_restantes,
        'fecha_proximo_riego': fecha_proximo,
        'ajuste_aplicado': ajuste,
        'motivo': resultado_ajuste['motivo'],
        'reseteo_por_lluvia': False,
        'frecuencia_ajustada': dias_ajustados
    }
