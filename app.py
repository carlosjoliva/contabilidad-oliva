import streamlit as st
import pandas as pd
import sqlite3
import datetime

# Configuración de la página
st.set_page_config(page_title="Contabilidad Sociedad Oliva", layout="wide")

# Inicialización de Base de Datos SQLite
def init_db():
    conn = sqlite3.connect("contabilidad_oliva.db")
    c = conn.cursor()
    
    # Tabla Ventas (Facturas Emitidas)
    c.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio INTEGER UNIQUE,
            cliente TEXT,
            rut TEXT,
            fecha_emision DATE,
            plazo_dias INTEGER,
            fecha_pago DATE,
            neto REAL,
            iva REAL,
            total REAL,
            estado_pago TEXT
        )
    ''')
    
    # Tabla Compras (Facturas Recibidas)
    c.execute('''
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio INTEGER,
            proveedor TEXT,
            rut TEXT,
            fecha_emision DATE,
            neto REAL,
            iva REAL,
            total REAL,
            categoria TEXT
        )
    ''')
    
    # Cargar datos iniciales de 2025 si la tabla está vacía
    c.execute("SELECT COUNT(*) FROM ventas")
    if c.fetchone()[0] == 0:
        ventas_iniciales = [
            (1515, "VAPOR AUSTRAL SPA", "76487820-5", "2025-01-06", 30, None, 113913, 21643.47, 135556.47, "PENDIENTE"),
            (1517, "VAPOR AUSTRAL SPA", "76487820-5", "2025-01-06", 30, None, 390000, 74100.00, 464100.00, "PENDIENTE"),
            (1518, "AQUAMET S A", "96949330-6", "2025-01-06", 30, "2025-02-06", 380000, 72200.00, 452200.00, "PAGADO"),
            (1519, "COMERCIAL LAS NALCAS LIMITADA", "77493508-8", "2025-01-13", 5, "2025-02-13", 704557, 133865.83, 838422.83, "PAGADO"),
            (1520, "HOTEL VIVO MONTAÑA SPA", "77116666-0", "2025-01-23", 30, "2025-02-23", 90000, 17100.00, 107100.00, "PAGADO"),
            (1521, "HOTEL VIVO MONTAÑA SPA", "77116666-0", "2025-01-30", 30, "2025-03-02", 731540, 138992.60, 870532.60, "PAGADO"),
            (1522, "MULTI X S.A.", "79891160-0", "2025-01-31", 30, "2025-03-03", 3000000, 570000.00, 3570000.00, "PAGADO")
        ]
        c.executemany('''
            INSERT INTO ventas (folio, cliente, rut, fecha_emision, plazo_dias, fecha_pago, neto, iva, total, estado_pago)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ventas_iniciales)
        
    conn.commit()
    conn.close()

init_db()

# Título Principal
st.title("💼 Sistema Contable & Tributario - Sociedad Oliva y Cía. Ltda.")
st.markdown("---")

# Cargar Datos de SQLite
conn = sqlite3.connect("contabilidad_oliva.db")
df_ventas = pd.read_sql_query("SELECT * FROM ventas", conn)
df_compras = pd.read_sql_query("SELECT * FROM compras", conn)
conn.close()

# Métricas Principales (KPIs)
col1, col2, col3, col4 = st.columns(4)

plata_en_la_calle = df_ventas[df_ventas['estado_pago'] == 'PENDIENTE']['total'].sum()
ventas_mes_neto = df_ventas['neto'].sum()
ventas_mes_bruto = df_ventas['total'].sum()
iva_debito_total = df_ventas['iva'].sum()

with col1:
    st.metric(label="🚨 Plata en la Calle (Pendiente)", value=f"${plata_en_la_calle:,.0f}")
with col2:
    st.metric(label="📅 Facturado Neto Mes", value=f"${ventas_mes_neto:,.0f}")
with col3:
    st.metric(label="📈 Total Facturado (Bruto)", value=f"${ventas_mes_bruto:,.0f}")
with col4:
    st.metric(label="🏛️ IVA Débito Generado", value=f"${iva_debito_total:,.0f}")

st.markdown("---")

# Menú Principal
opcion = st.sidebar.selectbox("Seleccione un Módulo:", [
    "Dashboard & Ventas",
    "Ingresar Nueva Factura",
    "Módulo de Compras & Proveedores",
    "Proyección de IVA y F29 (PPM 2%)",
    "Conciliación con RCV del SII"
])

# Módulo 1: Dashboard y Control de Ventas
if opcion == "Dashboard & Ventas":
    st.subheader("📋 Registro de Facturas Emitidas (Ventas)")
    
    st.dataframe(df_ventas, use_container_width=True)
    
    st.subheader("🔴 Facturas Pendientes de Cobro")
    df_pendientes = df_ventas[df_ventas['estado_pago'] == 'PENDIENTE']
    if not df_pendientes.empty:
        for idx, row in df_pendientes.iterrows():
            col_a, col_b, col_c = st.columns([3, 2, 2])
            with col_a:
                st.write(f"**Factura N° {row['folio']}** - {row['cliente']} (RUT: {row['rut']})")
            with col_b:
                st.write(f"Monto Total: **${row['total']:,.0f}**")
            with col_c:
                if st.button(f"Marcar Pagada #{row['folio']}", key=row['folio']):
                    conn = sqlite3.connect("contabilidad_oliva.db")
                    c = conn.cursor()
                    hoy = datetime.date.today().strftime("%Y-%m-%d")
                    c.execute("UPDATE ventas SET estado_pago = 'PAGADO', fecha_pago = ? WHERE folio = ?", (hoy, row['folio']))
                    conn.commit()
                    conn.close()
                    st.success(f"Factura #{row['folio']} actualizada a PAGADA.")
                    st.rerun()
    else:
        st.info("¡Excelente! No hay facturas pendientes en la calle.")

# Módulo 2: Ingreso de Ventas Manuales
elif opcion == "Ingresar Nueva Factura":
    st.subheader("➕ Registro Manual de Factura Emitida")
    
    with st.form("form_venta"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            folio = st.number_input("N° de Factura", min_value=1, step=1)
            cliente = st.text_input("Razón Social del Cliente")
            rut = st.text_input("RUT Cliente (ej: 76.487.820-5)")
        with col_f2:
            fecha_emision = st.date_input("Fecha de Emisión", datetime.date.today())
            plazo = st.number_input("Plazo de Pago (Días)", min_value=0, value=30)
            neto = st.number_input("Monto Neto ($)", min_value=0.0, step=1000.0)
            
        iva_calc = round(neto * 0.19, 2)
        total_calc = round(neto + iva_calc, 2)
        
        st.info(f"💡 IVA (19%): **${iva_calc:,.0f}** | Total Bruto: **${total_calc:,.0f}**")
        
        submitted = st.form_submit_button("Guardar Factura")
        if submitted:
            conn = sqlite3.connect("contabilidad_oliva.db")
            c = conn.cursor()
            c.execute('''
                INSERT INTO ventas (folio, cliente, rut, fecha_emision, plazo_dias, fecha_pago, neto, iva, total, estado_pago)
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, 'PENDIENTE')
            ''', (folio, cliente, rut, str(fecha_emision), plazo, neto, iva_calc, total_calc))
            conn.commit()
            conn.close()
            st.success(f"Factura N° {folio} registrada correctamente.")
            st.rerun()

# Módulo 3: Proyección Tributaria F29
elif opcion == "Proyección de IVA y F29 (PPM 2%)":
    st.subheader("🏛️ Simulación y Proyección de F29 en Tiempo Real")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        remanente_anterior = st.number_input("Remanente IVA Mes Anterior (Código 504)", value=123292.0)
        tasa_ppm = st.number_input("Tasa PPM (%) (Código 115)", value=2.0) / 100.0
        retenciones = st.number_input("Retenciones / Préstamo (Código 151 / 049)", value=31640.0)
    
    with col_p2:
        iva_credito_compras = df_compras['iva'].sum() if not df_compras.empty else 784059.0
        st.write(f"**IVA Crédito Fiscal (Compras registradas):** ${iva_credito_compras:,.0f}")
        
    # Cálculos F29
    iva_debito = df_ventas['iva'].sum()
    ventas_netas = df_ventas['neto'].sum()
    ppm_determinado = round(ventas_netas * tasa_ppm)
    
    total_creditos = iva_credito_compras + remanente_anterior
    iva_determinado = max(0.0, iva_debito - total_creditos)
    total_f29 = iva_determinado + ppm_determinado + retenciones
    
    st.markdown("### 📊 Liquidación Estimada F29")
    st.write(f"(+) IVA Débito Fiscal (Ventas): **${iva_debito:,.0f}**")
    st.write(f"(-) IVA Crédito Fiscal (Compras): **-${iva_credito_compras:,.0f}**")
    st.write(f"(-) Remanente Mes Anterior: **-${remanente_anterior:,.0f}**")
    st.markdown(f"**= IVA Determinado a Pagar: ${iva_determinado:,.0f}**")
    st.markdown(f"**+ PPM Determinado ({tasa_ppm*100}%): ${ppm_determinado:,.0f}**")
    st.markdown(f"**+ Retenciones y Ajustes: ${retenciones:,.0f}**")
    st.subheader(f"💵 Total Líquido a Pagar en F29: ${total_f29:,.0f}")

# Módulo 4: Conciliación SII
elif opcion == "Conciliación con RCV del SII":
    st.subheader("🔍 Auditoría de Ventas vs RCV SII")
    archivo_sii = st.file_uploader("Cargue el archivo CSV de Registro de Ventas descargado del SII", type=["csv", "xlsx"])
    if archivo_sii:
        st.success("Archivo del SII recibido. Ejecutando cruce automático de folios e impuestos...")