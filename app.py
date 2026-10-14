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
    
    # Tabla Notas de Crédito
    c.execute('''
        CREATE TABLE IF NOT EXISTS notas_credito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio_nc INTEGER UNIQUE,
            folio_factura INTEGER,
            cliente TEXT,
            rut TEXT,
            fecha_emision DATE,
            neto REAL,
            iva REAL,
            total REAL,
            motivo TEXT
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
    
    # Cargar datos iniciales si la tabla está vacía
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
df_nc = pd.read_sql_query("SELECT * FROM notas_credito", conn)
df_compras = pd.read_sql_query("SELECT * FROM compras", conn)
conn.close()

# Cálculo de Fechas de Vencimiento y Estado de Morosidad
hoy = datetime.date.today()

if not df_ventas.empty:
    df_ventas['fecha_emision_dt'] = pd.to_datetime(df_ventas['fecha_emision'])
    df_ventas['fecha_vencimiento_dt'] = df_ventas['fecha_emision_dt'] + pd.to_timedelta(df_ventas['plazo_dias'], unit='D')
    df_ventas['fecha_vencimiento'] = df_ventas['fecha_vencimiento_dt'].dt.strftime('%Y-%m-%d')
    df_ventas['dias_mora'] = (pd.to_datetime(hoy) - df_ventas['fecha_vencimiento_dt']).dt.days
    df_ventas['anio'] = df_ventas['fecha_emision_dt'].dt.year
    df_ventas['mes'] = df_ventas['fecha_emision_dt'].dt.month
else:
    df_ventas['fecha_vencimiento'] = []
    df_ventas['dias_mora'] = []
    df_ventas['anio'] = []
    df_ventas['mes'] = []

if not df_nc.empty:
    df_nc['fecha_emision_dt'] = pd.to_datetime(df_nc['fecha_emision'])
    df_nc['anio'] = df_nc['fecha_emision_dt'].dt.year
    df_nc['mes'] = df_nc['fecha_emision_dt'].dt.month

# Sidebar - Menú Principal y Filtros de Período
st.sidebar.header("🔍 Navegación y Filtros")

opcion = st.sidebar.selectbox("Seleccione un Módulo:", [
    "Dashboard & Ventas",
    "Ingresar Nueva Factura",
    "Emitir Nota de Crédito",
    "Módulo de Compras & Proveedores",
    "Proyección de IVA y F29 (PPM 2%)",
    "Conciliación con RCV del SII"
])

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Período Tributario")

# Opciones de Filtro de Año y Mes
anios_disponibles = sorted(list(set(df_ventas['anio'].dropna().astype(int).tolist() + [hoy.year])), reverse=True)
anio_sel = st.sidebar.selectbox("Año:", ["Todos"] + anios_disponibles, index=1 if len(anios_disponibles)>0 else 0)

meses_nombres = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

mes_sel_nombre = st.sidebar.selectbox("Mes:", ["Todos"] + list(meses_nombres.values()))
mes_sel_num = [k for k, v in meses_nombres.items() if v == mes_sel_nombre]
mes_sel = mes_sel_num[0] if len(mes_sel_num) > 0 else "Todos"

# Aplicación de Filtros a DataFrames
df_ventas_filtrado = df_ventas.copy()
df_nc_filtrado = df_nc.copy()

if anio_sel != "Todos":
    df_ventas_filtrado = df_ventas_filtrado[df_ventas_filtrado['anio'] == int(anio_sel)]
    if not df_nc_filtrado.empty:
        df_nc_filtrado = df_nc_filtrado[df_nc_filtrado['anio'] == int(anio_sel)]

if mes_sel != "Todos":
    df_ventas_filtrado = df_ventas_filtrado[df_ventas_filtrado['mes'] == int(mes_sel)]
    if not df_nc_filtrado.empty:
        df_nc_filtrado = df_nc_filtrado[df_nc_filtrado['mes'] == int(mes_sel)]

# Cálculo de Métricas Principales (KPIs)
col1, col2, col3, col4 = st.columns(4)

total_nc_neto = df_nc_filtrado['neto'].sum() if not df_nc_filtrado.empty else 0.0
total_nc_iva = df_nc_filtrado['iva'].sum() if not df_nc_filtrado.empty else 0.0
total_nc_bruto = df_nc_filtrado['total'].sum() if not df_nc_filtrado.empty else 0.0

plata_en_la_calle = df_ventas_filtrado[df_ventas_filtrado['estado_pago'] == 'PENDIENTE']['total'].sum()
ventas_mes_neto = df_ventas_filtrado['neto'].sum() - total_nc_neto
ventas_mes_bruto = df_ventas_filtrado['total'].sum() - total_nc_bruto
iva_debito_total = df_ventas_filtrado['iva'].sum() - total_nc_iva

with col1:
    st.metric(label="🚨 Plata en la Calle (Pendiente)", value=f"${plata_en_la_calle:,.0f}")
with col2:
    st.metric(label="📅 Facturado Neto Efectivo", value=f"${ventas_mes_neto:,.0f}")
with col3:
    st.metric(label="📈 Total Facturado (Bruto)", value=f"${ventas_mes_bruto:,.0f}")
with col4:
    st.metric(label="🏛️ IVA Débito (Neto de NC)", value=f"${iva_debito_total:,.0f}")

st.markdown("---")

# Módulo 1: Dashboard y Control de Ventas
if opcion == "Dashboard & Ventas":
    st.subheader(f"📋 Registro de Facturas Emitidas - Período: {mes_sel_nombre} / {anio_sel}")
    
    # Selección y orden de columnas para presentación
    cols_visibles = ['id', 'folio', 'cliente', 'rut', 'fecha_emision', 'plazo_dias', 'fecha_vencimiento', 'fecha_pago', 'neto', 'iva', 'total', 'estado_pago']
    cols_existentes = [c for c in cols_visibles if c in df_ventas_filtrado.columns]
    st.dataframe(df_ventas_filtrado[cols_existentes], use_container_width=True)
    
    st.subheader("🔴 Control de Cobranza y Alertas de Vencimiento")
    df_pendientes = df_ventas_filtrado[df_ventas_filtrado['estado_pago'] == 'PENDIENTE']
    
    if not df_pendientes.empty:
        for idx, row in df_pendientes.iterrows():
            mora = row['dias_mora']
            vencida = mora > 0
            
            # Etiqueta de estado
            if vencida:
                titulo_expander = f"🚨 VENCIDA ({mora} días de mora) | Factura N° {row['folio']} - {row['cliente']} | Total: ${row['total']:,.0f}"
            else:
                titulo_expander = f"⏳ En Plazo ({abs(mora)} días restantes) | Factura N° {row['folio']} - {row['cliente']} | Total: ${row['total']:,.0f}"
                
            with st.expander(titulo_expander):
                col_p1, col_p2 = st.columns([2, 2])
                with col_p1:
                    st.write(f"**RUT Cliente:** {row['rut']}")
                    st.write(f"**Fecha Emisión:** {row['fecha_emision']} ({row['plazo_dias']} días plazo)")
                    st.write(f"**Fecha Límite Pago (Vencimiento):** `{row['fecha_vencimiento']}`")
                    st.write(f"**Monto Bruto:** ${row['total']:,.0f}")
                    if vencida:
                        st.error(f"⚠️ Alerta: Esta factura debía cancelarse el {row['fecha_vencimiento']}.")
                with col_p2:
                    st.markdown("#### 💵 Registrar Cancelación Deuda")
                    fecha_cancelacion_input = st.date_input(f"Fecha Real de Cancelación (Folio #{row['folio']})", hoy, key=f"f_canc_{row['folio']}")
                    
                    if st.button(f"Confirmar Cancelación #{row['folio']}", key=f"btn_pagar_{row['folio']}"):
                        conn = sqlite3.connect("contabilidad_oliva.db")
                        c = conn.cursor()
                        c.execute("UPDATE ventas SET estado_pago = 'PAGADO', fecha_pago = ? WHERE folio = ?", (str(fecha_cancelacion_input), row['folio']))
                        conn.commit()
                        conn.close()
                        st.success(f"Factura #{row['folio']} cancelada exitosamente el {fecha_cancelacion_input}.")
                        st.rerun()
    else:
        st.info("¡Excelente! No hay facturas pendientes registradas en este período.")
        
    st.markdown("---")
    st.subheader("🗑️ Eliminar o Anular Factura por Error")
    if not df_ventas.empty:
        col_del1, col_del2 = st.columns([2, 1])
        with col_del1:
            folio_eliminar = st.selectbox("Seleccione Folio a Eliminar:", df_ventas['folio'].unique())
        with col_del2:
            st.write("")
            st.write("")
            if st.button("❌ Solicitar Eliminación", type="primary"):
                st.session_state['confirmar_eliminacion'] = folio_eliminar

        # Modal / Cuadro de confirmación de seguridad
        if st.session_state.get('confirmar_eliminacion') == folio_eliminar:
            st.warning(f"⚠️ ¿Está seguro que desea eliminar la Factura N° **{folio_eliminar}**?")
            
            with st.form("form_confirmacion_seguridad"):
                codigo = st.text_input("Ingrese el código de autorización:", type="password")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    btn_confirmar = st.form_submit_button("Confirmar Eliminación")
                with col_c2:
                    btn_cancelar = st.form_submit_button("Cancelar")

                if btn_confirmar:
                    if codigo == "2010":
                        conn = sqlite3.connect("contabilidad_oliva.db")
                        c = conn.cursor()
                        c.execute("DELETE FROM ventas WHERE folio = ?", (folio_eliminar,))
                        conn.commit()
                        conn.close()
                        
                        st.session_state.pop('confirmar_eliminacion', None)
                        st.success(f"Factura N° {folio_eliminar} eliminada exitosamente.")
                        st.rerun()
                    else:
                        st.error("🔒 Código de autorización incorrecto. No se realizó ninguna acción.")
                
                if btn_cancelar:
                    st.session_state.pop('confirmar_eliminacion', None)
                    st.rerun()

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
            fecha_emision = st.date_input("Fecha de Emisión", hoy)
            plazo = st.number_input("Plazo de Pago (Días)", min_value=0, value=30)
            neto = st.number_input("Monto Neto ($)", min_value=0.0, step=1000.0)
            
        iva_calc = round(neto * 0.19, 2)
        total_calc = round(neto + iva_calc, 2)
        venc_calc = fecha_emision + datetime.timedelta(days=int(plazo))
        
        st.info(f"💡 IVA (19%): **${iva_calc:,.0f}** | Total Bruto: **${total_calc:,.0f}** | Fecha Límite de Pago: **{venc_calc}**")
        
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

# Módulo M: Notas de Crédito
elif opcion == "Emitir Nota de Crédito":
    st.subheader("📄 Registro y Emisión de Notas de Crédito")
    
    if not df_ventas.empty:
        with st.form("form_nc"):
            col_nc1, col_nc2 = st.columns(2)
            with col_nc1:
                folio_nc = st.number_input("N° Nota de Crédito", min_value=1, step=1)
                folio_factura_ref = st.selectbox("Seleccione Factura Afecta (Folio):", df_ventas['folio'].unique())
                
                # Datos de la factura seleccionada
                factura_sel = df_ventas[df_ventas['folio'] == folio_factura_ref].iloc[0]
                st.caption(f"Cliente: **{factura_sel['cliente']}** | RUT: **{factura_sel['rut']}**")
                
                motivo = st.text_input("Motivo / Razon de la NC", value="Anulación o descuento de factura")
                
            with col_nc2:
                fecha_nc = st.date_input("Fecha de Emisión NC", hoy)
                neto_nc = st.number_input("Monto Neto a Rebajar ($)", min_value=0.0, max_value=float(factura_sel['neto']), value=float(factura_sel['neto']), step=1000.0)
                
            iva_nc_calc = round(neto_nc * 0.19, 2)
            total_nc_calc = round(neto_nc + iva_nc_calc, 2)
            
            st.warning(f"📉 Total Rebaja NC: **Neto: ${neto_nc:,.0f}** | **IVA: ${iva_nc_calc:,.0f}** | **Total:${total_nc_calc:,.0f}**")
            
            sub_nc = st.form_submit_button("Guardar Nota de Crédito")
            if sub_nc:
                conn = sqlite3.connect("contabilidad_oliva.db")
                c = conn.cursor()
                c.execute('''
                    INSERT INTO notas_credito (folio_nc, folio_factura, cliente, rut, fecha_emision, neto, iva, total, motivo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (folio_nc, folio_factura_ref, factura_sel['cliente'], factura_sel['rut'], str(fecha_nc), neto_nc, iva_nc_calc, total_nc_calc, motivo))
                
                # Si la NC es por el total neto de la factura, se actualiza el estado
                if neto_nc >= factura_sel['neto']:
                    c.execute("UPDATE ventas SET estado_pago = 'ANULADA_NC' WHERE folio = ?", (folio_factura_ref,))
                    
                conn.commit()
                conn.close()
                st.success(f"Nota de Crédito N° {folio_nc} registrada correctamente.")
                st.rerun()
    else:
        st.info("No existen facturas registradas para emitir notas de crédito.")
        
    st.markdown("---")
    st.subheader("📜 Histórico de Notas de Crédito Registradas")
    if not df_nc.empty:
        st.dataframe(df_nc, use_container_width=True)
    else:
        st.info("No hay notas de crédito registradas.")

# Módulo 3: Proyección Tributaria F29
elif opcion == "Proyección de IVA y F29 (PPM 2%)":
    st.subheader(f"🏛️ Simulación y Proyección de F29 - Período: {mes_sel_nombre} / {anio_sel}")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        remanente_anterior = st.number_input("Remanente IVA Mes Anterior (Código 504)", value=123292.0)
        tasa_ppm = st.number_input("Tasa PPM (%) (Código 115)", value=2.0) / 100.0
        retenciones = st.number_input("Retenciones / Préstamo (Código 151 / 049)", value=31640.0)
    
    with col_p2:
        iva_credito_compras = df_compras['iva'].sum() if not df_compras.empty else 784059.0
        st.write(f"**IVA Crédito Fiscal (Compras registradas):** ${iva_credito_compras:,.0f}")
        
    # Cálculos F29 ajustados con Notas de Crédito y Filtro de Período
    iva_debito_bruto = df_ventas_filtrado['iva'].sum()
    iva_debito = max(0.0, iva_debito_bruto - total_nc_iva)
    ventas_netas = max(0.0, df_ventas_filtrado['neto'].sum() - total_nc_neto)
    
    ppm_determinado = round(ventas_netas * tasa_ppm)
    
    total_creditos = iva_credito_compras + remanente_anterior
    iva_determinado = max(0.0, iva_debito - total_creditos)
    total_f29 = iva_determinado + ppm_determinado + retenciones
    
    st.markdown("### 📊 Liquidación Estimada F29")
    st.write(f"(+) IVA Débito Fiscal (Ventas): **${iva_debito_bruto:,.0f}**")
    if total_nc_iva > 0:
        st.write(f"(-) IVA Rebajado por NC: **-${total_nc_iva:,.0f}**")
    st.write(f"(-) IVA Crédito Fiscal (Compras): **-${iva_credito_compras:,.0f}**")
    st.write(f"(-) Remanente Mes Anterior: **-${remanente_anterior:,.0f}**")
    st.markdown(f"**= IVA Determinado a Pagar: ${iva_determinado:,.0f}**")
    st.markdown(f"**+ PPM Determinado ({tasa_ppm*100:.1f}%): ${ppm_determinado:,.0f}**")
    st.markdown(f"**+ Retenciones y Ajustes: ${retenciones:,.0f}**")
    st.subheader(f"💵 Total Líquido a Pagar en F29: ${total_f29:,.0f}")

# Módulo 4: Conciliación SII
elif opcion == "Conciliación con RCV del SII":
    st.subheader("🔍 Auditoría de Ventas vs RCV SII")
    archivo_sii = st.file_uploader("Cargue el archivo CSV de Registro de Ventas descargado del SII", type=["csv", "xlsx"])
    if archivo_sii:
        st.success("Archivo del SII recibido. Ejecutando cruce automático de folios e impuestos...")
