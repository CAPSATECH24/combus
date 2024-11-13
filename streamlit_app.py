import streamlit as st 
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from datetime import datetime

# Funciones auxiliares
def parse_time_string(time_str):
    """
    Extrae días, horas y minutos de una cadena de texto en el formato (XD, YH, ZM).
    
    Args:
        time_str (str): Cadena de texto con el tiempo en el formato especificado.
        
    Returns:
        int or None: Total de minutos si el formato es correcto, de lo contrario None.
    """
    pattern = r'\((\d+)D,\s*(\d+)H,\s*(\d+)M\)'
    match = re.search(pattern, time_str)
    if match:
        days, hours, minutes = map(int, match.groups())
        return days * 24 * 60 + hours * 60 + minutes
    return None

def color_merma(row):
    """
    Función para colorear la fila de 'Ralentí Real' en la tabla.
    
    Args:
        row (pd.Series): Fila de la tabla.
        
    Returns:
        list: Lista de estilos para cada celda de la fila.
    """
    if row['Concepto'] == 'Ralentí Real':
        return ['background-color: #FFCCCC'] * len(row)
    else:
        return [''] * len(row)

def highlight_positivo(val):
    """
    Resalta valores positivos en verde y negativos en rojo.
    
    Args:
        val (str): Valor de la celda.
        
    Returns:
        str: Estilo CSS para la celda.
    """
    try:
        val_float = float(val.replace(',', '').replace('$', ''))
        color = 'green' if val_float > 0 else 'red' if val_float < 0 else 'black'
    except:
        color = 'black'
    return f'color: {color}'

def create_metric_card(title, value, subtitle, color):
    """
    Crea un recuadro (card) estilizado para mostrar métricas clave.
    
    Args:
        title (str): Título de la métrica.
        value (str): Valor principal de la métrica.
        subtitle (str): Información adicional o descripción.
        color (str): Color de borde y título.
    """
    card_html = f"""
    <div style="
        background-color: #FFFFFF;
        border-left: 5px solid {color};
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    ">
        <h4 style="color: {color}; margin-bottom: 5px;">{title}</h4>
        <h2 style="color: #333333; margin-bottom: 5px;">{value}</h2>
        <p style="color: #666666;">{subtitle}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# Inicializar variables en session_state si no existen
if 'calculado' not in st.session_state:
    st.session_state.calculado = False

    # Variables de cálculo inicial
    st.session_state.idle_minutes = 0
    st.session_state.moving_minutes = 0
    st.session_state.total_minutes = 0
    st.session_state.idle_percentage = 0.0
    st.session_state.moving_percentage = 0.0
    st.session_state.combustible_ralenti = 0.0
    st.session_state.combustible_movimiento = 0.0
    st.session_state.costo_ralenti = 0.0
    st.session_state.costo_movimiento = 0.0
    st.session_state.costo_total = 0.0
    st.session_state.merma_total = 0.0
    st.session_state.merma_diaria = 0.0
    st.session_state.merma_semanal = 0.0
    st.session_state.merma_mensual = 0.0
    st.session_state.merma_anual = 0.0
    st.session_state.merma_total_unit = 0.0
    st.session_state.merma_diaria_unit = 0.0
    st.session_state.merma_semanal_unit = 0.0
    st.session_state.merma_mensual_unit = 0.0
    st.session_state.merma_anual_unit = 0.0
    st.session_state.ahorro_anual = 0.0
    st.session_state.costo_total_barras = 0.0
    st.session_state.neto_mensual = 0.0
    st.session_state.neto_anual = 0.0
    st.session_state.ahorro_mensual = 0.0  # Asegurarse de que esté inicializado
    st.session_state.meses_para_recuperar = 0.0
    st.session_state.roi_days = 0.0
    st.session_state.combustible_total = 0.0
    st.session_state.real_idle_percentage = 100.0  # Valor inicial, ahora ajustable por el usuario
    st.session_state.costo_ralenti_real_unit = 0.0
    st.session_state.merma_diaria_real_unit = 0.0
    st.session_state.merma_semanal_real_unit = 0.0
    st.session_state.merma_mensual_real_unit = 0.0
    st.session_state.merma_anual_real_unit = 0.0
    st.session_state.costo_ralenti_real_fleet = 0.0
    st.session_state.merma_diaria_real_fleet = 0.0
    st.session_state.merma_semanal_real_fleet = 0.0
    st.session_state.merma_mensual_real_fleet = 0.0
    st.session_state.merma_anual_real_fleet = 0.0
    st.session_state.renta_mensual = 999.00  # Valor por defecto

# Configuración de la página
st.set_page_config(page_title="Análisis de Ralentí vs Movimiento", layout="wide")
st.title("📊 Análisis de Ralentí vs Movimiento 🚚")

st.markdown("""
Este análisis te permite comprender las pérdidas económicas y de combustible debido al tiempo en ralentí de tu flota.
Introduce los datos a continuación para obtener una visión detallada.
""")

# Barra Lateral para Parámetros de Empresa
st.sidebar.header("🔧 Parámetros de la Empresa")

# Entrada del costo por pieza de las barras de combustible
costo_por_pieza = st.sidebar.number_input(
    "💲 Costo por unidad con las barras de combustible ($)",
    min_value=0.0,
    value=0.00,
    step=0.0,
    help="Ingrese el costo de una pieza de la barra de combustible."
)

# Entrada de la renta mensual por el servicio de monitoreo
renta_mensual = st.sidebar.number_input(
    "📈 Renta mensual por unidad del servicio de monitoreo ($)",
    min_value=0.0,
    value=st.session_state.renta_mensual,  # Utilizar valor de session_state
    step=10.0,
    help="Ingrese la renta mensual que se pagaría por unidad por el servicio de monitoreo de combustible."
)

# Entrada del porcentaje de reducción de merma de ralentí
porcentaje_reduccion = st.sidebar.slider(
    "🔻 Porcentaje de reducción de merma de ralentí (%)",
    min_value=0,
    max_value=100,
    value=20,
    step=1,
    help="Seleccione el porcentaje de reducción de la merma de ralentí que espera lograr con el monitoreo."
)

# Entrada del porcentaje de ralentí real
porcentaje_ralenti_real = st.sidebar.slider(
    "📊 % de ralentí real considerado como merma",
    min_value=0,
    max_value=100,
    value=100,
    step=1,
    help="Ajusta el porcentaje del tiempo en ralentí que consideras realmente como merma."
)

st.sidebar.markdown("---")

# Entrada de rango de fechas
st.header("📅 Rango de Fechas de los Datos")
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Fecha de Inicio", value=datetime.today())
with col_date2:
    end_date = st.date_input("Fecha de Fin", value=datetime.today())

# Validación de las fechas
if start_date > end_date:
    st.error("⚠️ La fecha de inicio no puede ser posterior a la fecha de fin.")
    st.stop()

# Cálculo de la duración del período en días
duration_days = (end_date - start_date).days + 1  # +1 para incluir ambos días
st.info(f"**Duración del Período**: {duration_days} días")

st.markdown("---")

# Entrada de datos de tiempo
st.header("⏱️ Ingreso de Datos de Tiempo")
col1, col2 = st.columns(2)
with col1:
    idle_time = st.text_area(
        "⏱️ Tiempo en ralentí (formato: (XD, YH, ZM))",
        placeholder="Ejemplo: (1D, 22H, 8M)",
        help="Ingrese el tiempo en el formato especificado: D=días, H=horas, M=minutos"
    )

with col2:
    moving_time = st.text_area(
        "🚗 Tiempo en movimiento (formato: (XD, YH, ZM))",
        placeholder="Ejemplo: (1D, 15H, 32M)",
        help="Ingrese el tiempo en el formato especificado: D=días, H=horas, M=minutos"
    )

st.markdown("---")

# Entrada de combustible, precio y unidades de la flota
st.header("⛽ Ingreso de Datos de Combustible y Flota")
col3, col4, col5 = st.columns(3)
with col3:
    combustible_total = st.number_input(
        "⛽ Combustible total consumido por unidad (L)",
        min_value=0.0,
        value=1419.00,
        step=0.1,
        help="Ingrese el total de combustible consumido en litros por unidad"
    )
with col4:
    precio_litro = st.number_input(
        "💲 Precio por litro ($)",
        min_value=0.0,
        value=25.00,
        step=0.01,
        help="Ingrese el precio por litro de combustible"
    )
with col5:
    num_unidades = st.number_input(
        "🚛 Cantidad de unidades en la flota",
        min_value=1,
        value=30,
        step=1,
        help="Ingrese el número total de unidades en su flota"
    )

st.markdown("---")

# Botón para calcular
if st.button("✅ Calcular"):

    # Validación de entradas de tiempo
    idle_minutes = parse_time_string(idle_time)
    moving_minutes = parse_time_string(moving_time)

    if idle_minutes is None:
        st.error("⚠️ Formato incorrecto para 'Tiempo en ralentí'. Por favor, siga el formato especificado.")
    elif moving_minutes is None:
        st.error("⚠️ Formato incorrecto para 'Tiempo en movimiento'. Por favor, siga el formato especificado.")
    elif combustible_total <= 0:
        st.error("⚠️ El combustible total consumido debe ser mayor que cero.")
    elif precio_litro <= 0:
        st.error("⚠️ El precio por litro debe ser mayor que cero.")
    else:
        total_minutes = idle_minutes + moving_minutes

        if total_minutes == 0:
            st.error("⚠️ El tiempo total no puede ser cero.")
        else:
            # Cálculo de porcentajes de tiempo
            idle_percentage = (idle_minutes / total_minutes) * 100
            moving_percentage = (moving_minutes / total_minutes) * 100

            # Cálculo de consumo de combustible proporcional
            combustible_ralenti = (idle_percentage / 100) * combustible_total
            combustible_movimiento = (moving_percentage / 100) * combustible_total

            # Cálculo de costos
            costo_ralenti = combustible_ralenti * precio_litro
            costo_movimiento = combustible_movimiento * precio_litro
            costo_total = combustible_total * precio_litro

            # Cálculo de merma total por todas las unidades
            merma_total = costo_ralenti * num_unidades

            # Escalado de merma según la duración del período
            merma_diaria = merma_total / duration_days
            merma_semanal = merma_diaria * 7
            merma_mensual = merma_diaria * 30
            merma_anual = merma_diaria * 365

            # Cálculo de merma por unidad
            merma_total_unit = costo_ralenti
            merma_diaria_unit = merma_total_unit / duration_days
            merma_semanal_unit = merma_diaria_unit * 7
            merma_mensual_unit = merma_diaria_unit * 30
            merma_anual_unit = merma_diaria_unit * 365

            # Cálculo del ahorro potencial con reducción de merma
            # Incorporar el % de ralentí real
            ahorro_anual = merma_anual * (porcentaje_reduccion / 100) * (porcentaje_ralenti_real / 100)

            # Cálculo del costo total de las barras de combustible
            costo_total_barras = costo_por_pieza * num_unidades

            # Cálculo del ahorro mensual
            ahorro_mensual = ahorro_anual / 12

            # **[Corrección] Almacenar 'ahorro_mensual' en session_state**
            st.session_state.ahorro_mensual = ahorro_mensual

            # Cálculo del ahorro neto mensual (Ahorro mensual - Renta mensual total)
            neto_mensual = ahorro_mensual - (renta_mensual * num_unidades)

            # Cálculo del Retorno de Inversión (ROI) en meses
            if neto_mensual > 0:
                meses_para_recuperar = costo_total_barras / neto_mensual
            else:
                meses_para_recuperar = float('inf')  # No recuperable

            # Cálculo del Retorno de Inversión (ROI) en días
            if neto_mensual > 0:
                ahorro_neto_diario = neto_mensual / 30  # Asumiendo 30 días por mes
                roi_days = costo_total_barras / ahorro_neto_diario
            else:
                roi_days = float('inf')  # No recuperable

            # Cálculo del neto mensual y anual (ahorro - renta mensual total)
            neto_anual = ahorro_anual - (renta_mensual * 12 * num_unidades)

            # Almacenar los resultados en session_state
            st.session_state.calculado = True
            st.session_state.idle_minutes = idle_minutes
            st.session_state.moving_minutes = moving_minutes
            st.session_state.total_minutes = total_minutes
            st.session_state.idle_percentage = idle_percentage
            st.session_state.moving_percentage = moving_percentage
            st.session_state.combustible_ralenti = combustible_ralenti
            st.session_state.combustible_movimiento = combustible_movimiento
            st.session_state.costo_ralenti = costo_ralenti
            st.session_state.costo_movimiento = costo_movimiento
            st.session_state.costo_total = costo_total
            st.session_state.merma_total = merma_total
            st.session_state.merma_diaria = merma_diaria
            st.session_state.merma_semanal = merma_semanal
            st.session_state.merma_mensual = merma_mensual
            st.session_state.merma_anual = merma_anual
            st.session_state.merma_total_unit = merma_total_unit
            st.session_state.merma_diaria_unit = merma_diaria_unit
            st.session_state.merma_semanal_unit = merma_semanal_unit
            st.session_state.merma_mensual_unit = merma_mensual_unit
            st.session_state.merma_anual_unit = merma_anual_unit
            st.session_state.ahorro_anual = ahorro_anual
            st.session_state.costo_total_barras = costo_total_barras
            st.session_state.neto_mensual = neto_mensual  # Cambio: 'ahorro_neto_mensual' ya no se usa
            st.session_state.neto_anual = neto_anual
            st.session_state.meses_para_recuperar = meses_para_recuperar
            st.session_state.roi_days = roi_days  # Almacenar ROI en días
            st.session_state.combustible_total = combustible_total
            st.session_state.renta_mensual = renta_mensual  # Actualizar renta_mensual

            # Actualizar el porcentaje de ralentí real con el valor del slider
            st.session_state.real_idle_percentage = porcentaje_ralenti_real

            # Cálculos Real Ralentí (usando el porcentaje ajustado por el usuario)
            costo_ralenti_real_unit = st.session_state.costo_ralenti * (st.session_state.real_idle_percentage / 100)
            merma_total_real_unit = costo_ralenti_real_unit
            merma_diaria_real_unit = merma_total_real_unit / duration_days
            merma_semanal_real_unit = merma_diaria_real_unit * 7
            merma_mensual_real_unit = merma_diaria_real_unit * 30
            merma_anual_real_unit = merma_diaria_real_unit * 365

            # Cálculos Real Ralentí para Flota
            costo_ralenti_real_fleet = costo_ralenti_real_unit * num_unidades
            merma_total_real_fleet = costo_ralenti_real_fleet
            merma_diaria_real_fleet = merma_total_real_fleet / duration_days
            merma_semanal_real_fleet = merma_diaria_real_fleet * 7
            merma_mensual_real_fleet = merma_diaria_real_fleet * 30
            merma_anual_real_fleet = merma_diaria_real_fleet * 365

            # Actualizar session_state con los cálculos real ralenti
            st.session_state.costo_ralenti_real_unit = costo_ralenti_real_unit
            st.session_state.merma_diaria_real_unit = merma_diaria_real_unit
            st.session_state.merma_semanal_real_unit = merma_semanal_real_unit
            st.session_state.merma_mensual_real_unit = merma_mensual_real_unit
            st.session_state.merma_anual_real_unit = merma_anual_real_unit
            st.session_state.costo_ralenti_real_fleet = costo_ralenti_real_fleet
            st.session_state.merma_diaria_real_fleet = merma_diaria_real_fleet
            st.session_state.merma_semanal_real_fleet = merma_semanal_real_fleet
            st.session_state.merma_mensual_real_fleet = merma_mensual_real_fleet
            st.session_state.merma_anual_real_fleet = merma_anual_real_fleet

        # Definir las pestañas (Renombradas)
        tabs = st.tabs(["📦 Unidad Individual", "🚛 Flota Completa", "🔍 Detalles de Cálculos", "Datos Recopilados", "💡 Análisis Económico"])

        # Pestaña 1: Unidad Individual
        with tabs[0]:
            st.subheader("📈 Resumen de Análisis - Unidad Individual")
            data_unit = {
                'Concepto': ['Ralentí Real', 'Movimiento', 'Total'],
                'Tiempo (min)': [st.session_state.idle_minutes, st.session_state.moving_minutes, st.session_state.total_minutes],
                'Tiempo (hrs)': [round(st.session_state.idle_minutes / 60, 2), round(st.session_state.moving_minutes / 60, 2), round(st.session_state.total_minutes / 60, 2)],
                'Porcentaje Tiempo': [round(st.session_state.idle_percentage, 1), round(st.session_state.moving_percentage, 1), 100.0],
                'Consumo Combustible (L)': [round(st.session_state.combustible_ralenti, 2), round(st.session_state.combustible_movimiento, 2), round(st.session_state.combustible_total, 2)],
                'Costo ($)': [st.session_state.costo_ralenti, st.session_state.costo_movimiento, st.session_state.costo_total]
            }
            df_unit = pd.DataFrame(data_unit)

            st.dataframe(df_unit.style
                .format({
                    'Tiempo (min)': '{:,.0f}',
                    'Tiempo (hrs)': '{:,.2f}',
                    'Porcentaje Tiempo': '{:,.1f}%',
                    'Consumo Combustible (L)': '{:,.2f}',
                    'Costo ($)': '${:,.2f}'
                })
                .apply(color_merma, axis=1)
            )

            # Visualizaciones para Unidad
            col6, col7 = st.columns(2)
            with col6:
                st.markdown("### 🕒 Distribución del Tiempo - Unidad")
                fig_tiempo_unit = px.bar(
                    df_unit[df_unit['Concepto'] != 'Total'],
                    x='Concepto',
                    y='Tiempo (min)',
                    title='Distribución del Tiempo: Ralentí vs Movimiento',
                    labels={'Tiempo (min)': 'Tiempo (min)', 'Concepto': 'Actividad'},
                    color='Concepto',
                    color_discrete_sequence=['#28a745', '#66B2FF'],  # Verde para Ralentí Real y azul para Movimiento
                    text='Tiempo (min)',
                    hover_data={'Consumo Combustible (L)': True, 'Costo ($)': True}
                )
                fig_tiempo_unit.update_traces(
                    texttemplate='%{y:,.0f}',
                    textposition='outside',
                    textfont_color='green'  # Texto en verde
                )
                fig_tiempo_unit.update_layout(
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    xaxis_title='Actividad',
                    yaxis_title='Tiempo (min)',
                    font=dict(size=12),
                    hovermode='closest'  # Mostrar solo el trazo más cercano
                )
                st.plotly_chart(fig_tiempo_unit, use_container_width=True)

            with col7:
                st.markdown("### 💰 Distribución del Costo - Unidad")
                fig_costo_unit = px.bar(
                    df_unit[df_unit['Concepto'] != 'Total'],
                    x='Concepto',
                    y='Costo ($)',
                    title='Distribución del Costo: Ralentí vs Movimiento',
                    labels={'Costo ($)': 'Costo ($)', 'Concepto': 'Actividad'},
                    color='Concepto',
                    color_discrete_sequence=['#28a745', '#66B2FF'],  # Verde para Ralentí Real y azul para Movimiento
                    text='Costo ($)',
                    hover_data={'Tiempo (min)': True, 'Consumo Combustible (L)': True}
                )
                fig_costo_unit.update_traces(
                    texttemplate='$%{y:,.2f}',
                    textposition='outside',
                    textfont_color='green'  # Texto en verde
                )
                fig_costo_unit.update_layout(
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    xaxis_title='Actividad',
                    yaxis_title='Costo ($)',
                    font=dict(size=12),
                    hovermode='closest'  # Mostrar solo el trazo más cercano
                )
                st.plotly_chart(fig_costo_unit, use_container_width=True)

            # Métricas Clave por Unidad con "Cards"
            st.subheader("📊 Métricas Clave - Unidad Individual")
            col8, col9, col10, col11 = st.columns(4)

            with col8:
                create_metric_card(
                    title="💸 Merma Diaria",
                    value=f"${st.session_state.merma_diaria_unit:,.2f}",
                    subtitle="Merma diaria por unidad",
                    color="#FF6666"
                )
            with col9:
                create_metric_card(
                    title="💸 Merma Semanal",
                    value=f"${st.session_state.merma_semanal_unit:,.2f}",
                    subtitle="Merma semanal por unidad",
                    color="#FF6666"
                )
            with col10:
                create_metric_card(
                    title="💸 Merma Mensual",
                    value=f"${st.session_state.merma_mensual_unit:,.2f}",
                    subtitle="Merma mensual por unidad",
                    color="#FF6666"
                )
            with col11:
                create_metric_card(
                    title="💸 Merma Anual",
                    value=f"${st.session_state.merma_anual_unit:,.2f}",
                    subtitle="Merma anual por unidad",
                    color="#FF6666"
                )

            st.markdown("---")

            # Detalles de las métricas clave
            st.subheader("🔍 Detalles de las Métricas Clave - Unidad Individual")
            col12, col13, col14 = st.columns(3)

            with col12:
                create_metric_card(
                    title="Ralentí (MERMA)",
                    value=f"${st.session_state.costo_ralenti:,.2f}",
                    subtitle=f"{st.session_state.combustible_ralenti:.1f} L ({st.session_state.idle_percentage:.1f}%)",
                    color="#FF6666"
                )
            with col13:
                create_metric_card(
                    title="Movimiento",
                    value=f"${st.session_state.costo_movimiento:,.2f}",
                    subtitle=f"{st.session_state.combustible_movimiento:.1f} L ({st.session_state.moving_percentage:.1f}%)",
                    color="#66B2FF"
                )
            with col14:
                create_metric_card(
                    title="Total",
                    value=f"${st.session_state.costo_total:,.2f}",
                    subtitle=f"{st.session_state.combustible_total:.1f} L (100%)",
                    color="#28a745"
                )

            # Mensaje de alerta sobre la merma
            st.warning(f"⚠️ **MERMA POR RALENTÍ:** ${st.session_state.costo_ralenti:,.2f} - Este monto representa pérdidas por tiempo en ralentí excesivo")

            # Sección de Beneficios Clave
            st.markdown("---")
            st.subheader("🎯 **Beneficios Clave de Implementar Nuestro Servicio**")

            benefits = [
                {"icon": "💰", "title": "Reducción de Costos", "description": "Disminuye los gastos en combustible al optimizar el tiempo en ralentí."},
                {"icon": "📉", "title": "Ahorro Continuo", "description": "Genera ahorros mensuales y anuales significativos."},
                {"icon": "⏳", "title": "Retorno de Inversión Rápido", "description": f"Recupera tu inversión en {round(st.session_state.meses_para_recuperar, 2)} meses ({round(st.session_state.roi_days, 2)} días)." if st.session_state.meses_para_recuperar != float('inf') else "No es recuperable con el ahorro actual."},
                {"icon": "🔧", "title": "Mejora Operativa", "description": "Optimiza el uso de combustible y mejora la eficiencia de tu flota."},
            ]

            cols_benefits = st.columns(len(benefits))
            for idx, benefit in enumerate(benefits):
                with cols_benefits[idx]:
                    st.markdown(f"### {benefit['icon']} **{benefit['title']}**")
                    st.markdown(f"{benefit['description']}")

        # Pestaña 2: Flota Completa
        with tabs[1]:
            st.subheader("🚛 Resumen de Análisis - Flota Completa")
            data_fleet = {
                'Concepto': ['Ralentí Real', 'Movimiento', 'Total'],
                'Tiempo (min)': [st.session_state.idle_minutes * num_unidades, st.session_state.moving_minutes * num_unidades, st.session_state.total_minutes * num_unidades],
                'Tiempo (hrs)': [round(st.session_state.idle_minutes / 60 * num_unidades, 2), round(st.session_state.moving_minutes / 60 * num_unidades, 2), round(st.session_state.total_minutes / 60 * num_unidades, 2)],
                'Porcentaje Tiempo': [round(st.session_state.idle_percentage, 1), round(st.session_state.moving_percentage, 1), 100.0],
                'Consumo Combustible (L)': [round(st.session_state.combustible_ralenti * num_unidades, 2), round(st.session_state.combustible_movimiento * num_unidades, 2), round(st.session_state.combustible_total * num_unidades, 2)],
                'Costo ($)': [st.session_state.costo_ralenti * num_unidades, st.session_state.costo_movimiento * num_unidades, st.session_state.costo_total * num_unidades]
            }
            df_fleet = pd.DataFrame(data_fleet)

            st.dataframe(df_fleet.style
                .format({
                    'Tiempo (min)': '{:,.0f}',
                    'Tiempo (hrs)': '{:,.2f}',
                    'Porcentaje Tiempo': '{:,.1f}%',
                    'Consumo Combustible (L)': '{:,.2f}',
                    'Costo ($)': '${:,.2f}'
                })
                .apply(color_merma, axis=1)
            )

            # Visualizaciones para Flota
            col6_fleet, col7_fleet = st.columns(2)
            with col6_fleet:
                st.markdown("### 🕒 Distribución del Tiempo - Flota")
                fig_tiempo_fleet = px.bar(
                    df_fleet[df_fleet['Concepto'] != 'Total'],
                    x='Concepto',
                    y='Tiempo (min)',
                    title='Distribución del Tiempo: Ralentí vs Movimiento',
                    labels={'Tiempo (min)': 'Tiempo (min)', 'Concepto': 'Actividad'},
                    color='Concepto',
                    color_discrete_sequence=['#28a745', '#66B2FF'],  # Verde para Ralentí Real y azul para Movimiento
                    text='Tiempo (min)',
                    hover_data={'Consumo Combustible (L)': True, 'Costo ($)': True}
                )
                fig_tiempo_fleet.update_traces(
                    texttemplate='%{y:,.0f}',
                    textposition='outside',
                    textfont_color='green'  # Texto en verde
                )
                fig_tiempo_fleet.update_layout(
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    xaxis_title='Actividad',
                    yaxis_title='Tiempo (min)',
                    font=dict(size=12),
                    hovermode='closest'  # Mostrar solo el trazo más cercano
                )
                st.plotly_chart(fig_tiempo_fleet, use_container_width=True)

            with col7_fleet:
                st.markdown("### 💰 Distribución del Costo - Flota")
                fig_costo_fleet = px.bar(
                    df_fleet[df_fleet['Concepto'] != 'Total'],
                    x='Concepto',
                    y='Costo ($)',
                    title='Distribución del Costo: Ralentí vs Movimiento',
                    labels={'Costo ($)': 'Costo ($)', 'Concepto': 'Actividad'},
                    color='Concepto',
                    color_discrete_sequence=['#28a745', '#66B2FF'],  # Verde para Ralentí Real y azul para Movimiento
                    text='Costo ($)',
                    hover_data={'Tiempo (min)': True, 'Consumo Combustible (L)': True}
                )
                fig_costo_fleet.update_traces(
                    texttemplate='$%{y:,.2f}',
                    textposition='outside',
                    textfont_color='green'  # Texto en verde
                )
                fig_costo_fleet.update_layout(
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    xaxis_title='Actividad',
                    yaxis_title='Costo ($)',
                    font=dict(size=12),
                    hovermode='closest'  # Mostrar solo el trazo más cercano
                )
                st.plotly_chart(fig_costo_fleet, use_container_width=True)

            # Métricas Clave para Flota con "Cards"
            st.subheader("📊 Métricas Clave - Flota Completa")
            col8_fleet, col9_fleet, col10_fleet, col11_fleet = st.columns(4)

            with col8_fleet:
                create_metric_card(
                    title="💸 Merma Diaria Total",
                    value=f"${st.session_state.merma_diaria:,.2f}",
                    subtitle="Merma diaria total de la flota",
                    color="#FF6666"
                )
            with col9_fleet:
                create_metric_card(
                    title="💸 Merma Semanal Total",
                    value=f"${st.session_state.merma_semanal:,.2f}",
                    subtitle="Merma semanal total de la flota",
                    color="#FF6666"
                )
            with col10_fleet:
                create_metric_card(
                    title="💸 Merma Mensual Total",
                    value=f"${st.session_state.merma_mensual:,.2f}",
                    subtitle="Merma mensual total de la flota",
                    color="#FF6666"
                )
            with col11_fleet:
                create_metric_card(
                    title="💸 Merma Anual Total",
                    value=f"${st.session_state.merma_anual:,.2f}",
                    subtitle="Merma anual total de la flota",
                    color="#FF6666"
                )

            st.markdown("---")

            # Detalles de las métricas clave
            st.subheader("🔍 Detalles de las Métricas Clave - Flota Completa")
            col12_fleet, col13_fleet, col14_fleet = st.columns(3)

            with col12_fleet:
                create_metric_card(
                    title="Ralentí (MERMA)",
                    value=f"${st.session_state.costo_ralenti * num_unidades:,.2f}",
                    subtitle=f"{st.session_state.combustible_ralenti * num_unidades:.1f} L ({st.session_state.idle_percentage:.1f}%)",
                    color="#FF6666"
                )
            with col13_fleet:
                create_metric_card(
                    title="Movimiento",
                    value=f"${st.session_state.costo_movimiento * num_unidades:,.2f}",
                    subtitle=f"{st.session_state.combustible_movimiento * num_unidades:.1f} L ({st.session_state.moving_percentage:.1f}%)",
                    color="#66B2FF"
                )
            with col14_fleet:
                create_metric_card(
                    title="Total",
                    value=f"${st.session_state.costo_total * num_unidades:,.2f}",
                    subtitle=f"{st.session_state.combustible_total * num_unidades:.1f} L (100%)",
                    color="#28a745"
                )

            # Mensaje de alerta sobre la merma
            st.warning(f"⚠️ **MERMA POR RALENTÍ (Flota)**: ${st.session_state.costo_ralenti * num_unidades:,.2f} - Este monto representa pérdidas por tiempo en ralentí excesivo")

            st.markdown("---")

            # Visualizaciones ajustadas para merma real
            st.markdown("### 📈 **Visualización de la Merma Real**")

            col19, col20 = st.columns(2)

            with col19:
                st.markdown("**Merma Diaria Real**")
                fig_diaria_real = px.bar(
                    x=["Diaria"],
                    y=[st.session_state.merma_diaria_real_unit],
                    labels={'x': '', 'y': 'Merma ($)'},
                    title='Merma Diaria Real - Unidad',
                    text=[f"${st.session_state.merma_diaria_real_unit:,.2f}"],
                    color_discrete_sequence=['#28a745']
                )
                fig_diaria_real.update_traces(
                    texttemplate='$%{y:,.2f}',
                    textposition='outside',
                    textfont_color='green'  # Texto en verde
                )
                fig_diaria_real.update_layout(
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    xaxis_title='',
                    yaxis_title='Merma ($)',
                    font=dict(size=12),
                    plot_bgcolor='rgba(0,0,0,0)',  # Fondo transparente
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_diaria_real, use_container_width=True)

            with col20:
                st.markdown("**Merma Anual Real**")
                fig_anual_real = px.bar(
                    x=["Anual"],
                    y=[st.session_state.merma_anual_real_unit],
                    labels={'x': '', 'y': 'Merma ($)'},
                    title='Merma Anual Real - Unidad',
                    text=[f"${st.session_state.merma_anual_real_unit:,.2f}"],
                    color_discrete_sequence=['#66B2FF']
                )
                fig_anual_real.update_traces(
                    texttemplate='$%{y:,.2f}',
                    textposition='outside',
                    textfont_color='green'  # Texto en verde
                )
                fig_anual_real.update_layout(
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    xaxis_title='',
                    yaxis_title='Merma ($)',
                    font=dict(size=12),
                    plot_bgcolor='rgba(0,0,0,0)',  # Fondo transparente
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_anual_real, use_container_width=True)

            st.markdown("---")

            # Resumen final
            st.markdown("""
            ### 📌 **Conclusión**

            Ajustar el porcentaje real de ralentí te permite obtener una estimación más precisa de las pérdidas económicas. 
            Esto te ayuda a tomar decisiones informadas para optimizar el uso de combustible y reducir las mermas en tu flota.
            """)

            # Opcional: Gráficos adicionales para Flota Ajustada
            st.markdown("### 📈 **Visualización de la Merma Real - Flota Completa**")

            col21, col22 = st.columns(2)

            with col21:
                st.markdown("**Merma Diaria Real Total**")
                fig_diaria_real_fleet = px.bar(
                    x=["Diaria"],
                    y=[st.session_state.merma_diaria_real_fleet],
                    labels={'x': '', 'y': 'Merma ($)'},
                    title='Merma Diaria Real Total - Flota',
                    text=[f"${st.session_state.merma_diaria_real_fleet:,.2f}"],
                    color_discrete_sequence=['#28a745']
                )
                fig_diaria_real_fleet.update_traces(
                    texttemplate='$%{y:,.2f}',
                    textposition='outside',
                    textfont_color='green'  # Texto en verde
                )
                fig_diaria_real_fleet.update_layout(
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    xaxis_title='',
                    yaxis_title='Merma ($)',
                    font=dict(size=12),
                    plot_bgcolor='rgba(0,0,0,0)',  # Fondo transparente
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_diaria_real_fleet, use_container_width=True)

            with col22:
                st.markdown("**Merma Anual Real Total**")
                fig_anual_real_fleet = px.bar(
                    x=["Anual"],
                    y=[st.session_state.merma_anual_real_fleet],
                    labels={'x': '', 'y': 'Merma ($)'},
                    title='Merma Anual Real Total - Flota',
                    text=[f"${st.session_state.merma_anual_real_fleet:,.2f}"],
                    color_discrete_sequence=['#66B2FF']
                )
                fig_anual_real_fleet.update_traces(
                    texttemplate='$%{y:,.2f}',
                    textposition='outside',
                    textfont_color='green'  # Texto en verde
                )
                fig_anual_real_fleet.update_layout(
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    xaxis_title='',
                    yaxis_title='Merma ($)',
                    font=dict(size=12),
                    plot_bgcolor='rgba(0,0,0,0)',  # Fondo transparente
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_anual_real_fleet, use_container_width=True)

            st.markdown("---")

            # Recomendación Final
            st.markdown("""
            ### 🌟 **Recomendación Final**

            Basado en los cálculos y visualizaciones anteriores, recomendamos implementar el servicio de monitoreo de combustible para reducir las mermas por ralentí. Esta inversión no solo optimizará el uso de combustible sino que también mejorará la eficiencia operativa de tu flota.
            """)

            # Opcional: Añadir una imagen o gráfico adicional para reforzar la recomendación
            # st.image("path_to_image.jpg", caption="Optimiza tu flota con nuestro servicio", use_column_width=True)

        # Pestaña 5: Análisis Económico
        with tabs[4]:
            st.subheader("💡 Análisis Económico")

            st.markdown("""
            ### 📈 **Comparación Económica: Implementar Monitoreo vs No Implementar**

            Esta sección muestra una comparación clara entre mantener el estado actual y adoptar el servicio de monitoreo de combustible para reducir las mermas por ralentí.
            """)

            # Cálculos de ahorro y costos
            total_ahorro_mensual = round(st.session_state.ahorro_anual / 12, 2)
            total_ahorro_anual = round(st.session_state.ahorro_anual, 2)
            total_neto_mensual = round(st.session_state.neto_mensual, 2)
            total_neto_anual = round(st.session_state.neto_anual, 2)

            # Retorno de Inversión (ROI)
            if st.session_state.neto_mensual > 0:
                meses_para_recuperar = round(st.session_state.meses_para_recuperar, 2)
                roi_days = round(st.session_state.roi_days, 2)
            else:
                meses_para_recuperar = float('inf')  # No recuperable
                roi_days = float('inf')  # No recuperable

            # DataFrame de Comparación Económica
            data_comparacion = {
                'Concepto': [
                    'Ahorro Mensual',
                    'Ahorro Anual',
                    'Costo Inicial (Barras de Combustible)',
                    'Costo Mensual (Monitoreo)',
                    'Neto Mensual',
                    'Neto Anual',
                    'Retorno de Inversión (ROI - Meses)',
                    'Retorno de Inversión (ROI - Días)'
                ],
                'Valor ($)': [
                    total_ahorro_mensual,
                    total_ahorro_anual,
                    round(st.session_state.costo_total_barras, 2),
                    round(renta_mensual * num_unidades, 2),  # Multiplicamos por num_unidades
                    total_neto_mensual,
                    total_neto_anual,
                    f"{meses_para_recuperar} meses" if meses_para_recuperar != float('inf') else "No es recuperable",
                    f"{roi_days} días" if roi_days != float('inf') else "No es recuperable"
                ]
            }
            df_comparacion = pd.DataFrame(data_comparacion)

            # Separar ROI para evitar errores de formateo
            df_comparacion_valores = df_comparacion[df_comparacion['Concepto'].str.contains('Ahorro|Costo|Neto')]
            df_comparacion_roi = df_comparacion[~df_comparacion['Concepto'].str.contains('Ahorro|Costo|Neto')]

            # Tabla de Comparación Económica (Sin ROI)
            st.markdown("### 📊 **Tabla de Comparación Económica**")
            st.dataframe(df_comparacion_valores.style
                .format({
                    'Valor ($)': '${:,.2f}'
                })
                .applymap(highlight_positivo, subset=['Valor ($)'])
            )

            # Visualización de Comparación
            st.markdown("### 📊 **Visualización de la Comparación Económica**")
            fig_comparacion = px.bar(
                df_comparacion_valores,
                x='Concepto',
                y='Valor ($)',
                color='Concepto',
                title='Comparación Económica',
                labels={'Valor ($)': 'Valor en $'},
                text='Valor ($)',
                color_discrete_sequence=['#28a745', '#66B2FF', '#FF6666', '#FF6666']  # Verde, Azul, Rojo para 'Neto' etc.
            )
            fig_comparacion.update_traces(
                texttemplate='$%{y:,.2f}',
                textposition='outside',
                textfont_color='green'  # Texto en verde
            )
            fig_comparacion.update_layout(
                uniformtext_minsize=8,
                uniformtext_mode='hide',
                xaxis_title='Concepto',
                yaxis_title='Valor ($)',
                font=dict(size=12),
                hovermode='closest'  # Mostrar solo el trazo más cercano
            )
            st.plotly_chart(fig_comparacion, use_container_width=True)

            # **Nueva Sección: Explicación Detallada del ROI**
            st.markdown("---")
            st.markdown("## 🔍 **Cálculo Detallado del Retorno de Inversión (ROI)**")

            # Presentar la Fórmula del ROI en Meses y Días
            st.markdown("""
            ### 📐 **Fórmulas del ROI**
            """)

            st.markdown("""
            #### 📐 **Fórmula del ROI en Meses**
            """)
            st.latex(r'''
            \text{ROI (Meses)} = \frac{\text{Costo Inicial}}{\text{Ahorro Neto Mensual}} = \frac{\text{Costo Inicial}}{\text{Ahorro Mensual} - \text{Costo Mensual}}
            ''')

            # Desglose de los Componentes
            st.markdown(f"""
            ### 📝 **Desglose de los Componentes**

            - **Costo Inicial (Barras de Combustible):** ${round(st.session_state.costo_total_barras, 2):,}
            - **Costo Mensual (Monitoreo):** ${round(renta_mensual * num_unidades, 2):,}
            - **Ahorro Mensual:** ${round(total_ahorro_mensual, 2):,}
            - **Ahorro Neto Mensual:** ${round(total_neto_mensual, 2):,}
            - **Ahorro Neto Diario:** ${round(total_neto_mensual / 30, 2):,} por día
            """)

            # **Visualización de ROI**
            st.markdown("---")
            st.markdown("### 📈 **Visualización del ROI**")

            # Mostrar ROI en Meses
            if meses_para_recuperar != float('inf'):
                st.metric("⏳ Retorno de Inversión (ROI)", f"{meses_para_recuperar} meses", delta=f"{meses_para_recuperar} meses")
            else:
                st.metric("⏳ Retorno de Inversión (ROI)", "No es recuperable con el ahorro actual", delta="")

            # Mostrar ROI en Días
            if roi_days != float('inf'):
                st.metric("⏰ Retorno de Inversión (ROI)", f"{roi_days} días", delta=f"{roi_days} días")
            else:
                st.metric("⏰ Retorno de Inversión (ROI)", "No es recuperable con el ahorro actual", delta="")

            st.markdown("---")

            st.markdown(f"""
            ### 📌 **Conclusión del Análisis Económico**

            - **Ahorro Mensual y Anual:** Implementar el servicio de monitoreo de combustible puede generar un ahorro significativo en las mermas por ralentí.
            - **Costo del Servicio:** Aunque existe un costo inicial por las barras de combustible y un costo mensual por el servicio, el ahorro potencial supera estos gastos, especialmente a largo plazo.
            - **Retorno de Inversión (ROI):** El tiempo necesario para recuperar la inversión depende del ahorro neto mensual logrado. En este caso, el ROI es de {meses_para_recuperar} meses o {roi_days} días.
            - **Viabilidad:** Basado en los parámetros ingresados, adoptar el servicio de monitoreo es económicamente viable y beneficioso para la empresa.
            """)

            # **Nueva Mejora: Visualización Interactiva del ROI y Ahorros Acumulados**
            st.markdown("---")
            st.markdown("## 📈 **Evolución del ROI y Ahorros Acumulados**")

            # Crear DataFrame para la evolución mensual
            meses = 60  # Simular hasta 60 meses (5 años)
            data_evolucion = {
                'Mes': list(range(1, meses + 1)),
                'Ahorro Acumulado ($)': [],
                'Costo Acumulado ($)': [],
                'Ganancia Acumulada ($)': []
            }

            ahorro_acumulado = 0.0
            costo_inicial = st.session_state.costo_total_barras
            costo_mensual = st.session_state.renta_mensual * num_unidades
            ahorro_mensual = st.session_state.ahorro_mensual

            for mes in range(1, meses + 1):
                ahorro_acumulado += ahorro_mensual
                costo_acumulado = costo_inicial + (costo_mensual * mes)
                ganancia_acumulada = ahorro_acumulado - costo_acumulado
                data_evolucion['Ahorro Acumulado ($)'].append(round(ahorro_acumulado, 2))
                data_evolucion['Costo Acumulado ($)'].append(round(costo_acumulado, 2))
                data_evolucion['Ganancia Acumulada ($)'].append(round(ganancia_acumulada, 2))

            df_evolucion = pd.DataFrame(data_evolucion)

            # Determinar el mes del ROI
            roi_mes = df_evolucion[df_evolucion['Ganancia Acumulada ($)'] >= 0]['Mes'].min()

            # Crear el gráfico de línea con mejoras
            fig_evolucion = go.Figure()

            # Línea de Ahorro Acumulado
            fig_evolucion.add_trace(go.Scatter(
                x=df_evolucion['Mes'],
                y=df_evolucion['Ahorro Acumulado ($)'],
                mode='lines+markers',
                name='Ahorro Acumulado',
                line=dict(color='#00CC96'),
                marker=dict(size=6),
                hovertemplate='Ahorro Acumulado: $%{y:,.2f}<extra></extra>'  # Formateo con comas
            ))

            # Línea de Costo Acumulado
            fig_evolucion.add_trace(go.Scatter(
                x=df_evolucion['Mes'],
                y=df_evolucion['Costo Acumulado ($)'],
                mode='lines+markers',
                name='Costo Acumulado',
                line=dict(color='#FF0000'),
                marker=dict(size=6),
                hovertemplate='Costo Acumulado: $%{y:,.2f}<extra></extra>'  # Formateo con comas
            ))

            # Línea de Ganancia Acumulada
            fig_evolucion.add_trace(go.Scatter(
                x=df_evolucion['Mes'],
                y=df_evolucion['Ganancia Acumulada ($)'],
                mode='lines+markers',
                name='Ganancia Acumulada',
                line=dict(color='#636EFA'),
                marker=dict(size=6),
                hovertemplate='Ganancia Acumulada: $%{y:,.2f}<extra></extra>'  # Formateo con comas
            ))

            # Añadir línea vertical para el ROI
            if not pd.isna(roi_mes):
                fig_evolucion.add_vline(x=roi_mes, line_width=2, line_dash="dash", line_color="green")
                fig_evolucion.add_annotation(
                    x=roi_mes,
                    y=max(df_evolucion['Ahorro Acumulado ($)']),
                    text=f"ROI en el Mes {roi_mes}",
                    showarrow=True,
                    arrowhead=1,
                    ax=-40,
                    ay=-40,
                    bgcolor="rgba(255,255,255,0.7)",
                    bordercolor="green",
                    borderwidth=1,
                    font=dict(color="black", size=12)
                )

            fig_evolucion.update_layout(
                title='Evolución del Ahorro, Costo y Ganancia Acumulada',
                xaxis_title='Mes',
                yaxis_title='Monto ($)',
                legend_title='Concepto',
                hovermode='closest',  # Cambiar a 'closest' para mostrar solo el trazo más cercano
                font=dict(size=12),
                plot_bgcolor='rgba(0,0,0,0)',  # Fondo transparente
                paper_bgcolor='rgba(0,0,0,0)'  # Fondo transparente
            )

            # Añadir líneas de cuadrícula suaves
            fig_evolucion.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
            fig_evolucion.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')

            # Personalizar hover para mostrar únicamente el valor del trazo correspondiente
            for trace in fig_evolucion.data:
                trace.update(
                    hoveron='points+fills',
                    hoverinfo='x+y',
                    hovertemplate='Mes: %{x}<br>%{y:$,.2f}<extra></extra>'
                )

            fig_evolucion.update_layout(
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor="#2b2b2b",  # Fondo oscuro para el tooltip
                    font_size=12,
                    font_family="Arial",
                    font=dict(color='white')  # Texto en blanco
                ),
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(128, 128, 128, 0.2)',
                    showspikes=True,
                    spikemode='across',
                    spikesnap='cursor',
                    spikecolor='rgba(0,0,0,0.3)',
                    spikethickness=1
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(128, 128, 128, 0.2)',
                    showspikes=True,
                    spikemode='across',
                    spikesnap='cursor',
                    spikecolor='rgba(0,0,0,0.3)',
                    spikethickness=1
                ),
                spikedistance=1000
            )

            st.plotly_chart(fig_evolucion, use_container_width=True)

            st.markdown("""
            ### 📌 **Interpretación del Gráfico**

            - **Ahorro Acumulado:** Representa la suma de los ahorros mensuales generados.
            - **Costo Acumulado:** Incluye el costo inicial de las barras de combustible más los costos mensuales de monitoreo.
            - **Ganancia Acumulada:** Es la diferencia entre el ahorro acumulado y el costo acumulado. 
              - Si es negativa, indica una pérdida.
              - Si es positiva, indica una ganancia.
            - **Punto de ROI:** La línea vertical verde y la anotación indican el mes exacto en que se recupera la inversión inicial, es decir, cuando el ahorro acumulado supera al costo acumulado.
            """)

            st.markdown("---")

            # Recomendación Final
            st.markdown("""
            ### 🌟 **Recomendación Final**

            Basado en los cálculos y visualizaciones anteriores, recomendamos implementar el servicio de monitoreo de combustible para reducir las mermas por ralentí. Esta inversión no solo optimizará el uso de combustible sino que también mejorará la eficiencia operativa de tu flota.
            """)

            # Opcional: Añadir una imagen o gráfico adicional para reforzar la recomendación
            # st.image("path_to_image.jpg", caption="Optimiza tu flota con nuestro servicio", use_column_width=True)
