from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import warnings

warnings.filterwarnings('ignore')

## Funciones
def fromato_numero(valor, prefijo=''):
    for unidad in ['', 'mil']:
        if valor < 1000:
            return f'{prefijo} {valor:.2f} {unidad}'
        
        valor /= 1000
    
    return f'{prefijo} {valor:.2f} millones'


## Web
st.set_page_config(layout='wide')
st.title("DASHBOARD DE VENTAS :shopping_trolley:")

url = 'https://ahcamachod.github.io/productos'

response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
datos = pd.read_json(soup.pre.contents[0])

datos['Fecha de Compra'] = pd.to_datetime(datos['Fecha de Compra'], format= '%d/%m/%Y')

## Filtrando por region y por año 
regiones_dict = {'Bogotá':'Andina', 'Medellín':'Andina', 'Cali':'Pacífica', 'Pereira':'Andina','Barranquilla':'Caribe', 'Cartagena':'Caribe','Cúcuta':'Andina', 'Bucaramanga':'Andina', 'Riohacha':'Caribe', 'Santa Marta':'Caribe', 'Leticia':'Amazónica', 'Pasto':'Andina','Manizales':'Andina', 'Neiva':'Andina', 'Villavicencio':'Orinoquía', 'Armenia':'Andina', 'Soacha':'Andina','Valledupar':'Caribe', 'Inírida':'Amazónica'}

datos['Región'] = datos['Lugar de Compra'].map(regiones_dict)
datos['Año'] = datos['Fecha de Compra'].dt.year

## Sidebar para la interaccion con la API
regiones = ['Colombia','Caribe','Andina','Pacífica','Orinoquía','Amazónica']
st.sidebar.title('Filtro')
region = st.sidebar.selectbox('Región', regiones)

if region == 'Colombia':
    datos.loc[datos['Región'] != 'Colombia']
else:
    datos = datos.loc[datos['Región'] == region]

todos_anos = st.sidebar.checkbox('Datos de todo el periodo', value=True)
if todos_anos:
    datos = datos
else:
    ano = st.sidebar.slider('Año',2020,2023)
    datos = datos.loc[datos['Año'] == ano]

filtro_vendedores = st.sidebar.multiselect('Vendedores', datos.Vendedor.unique())
if filtro_vendedores:
    datos = datos[datos['Vendedor'].isin(filtro_vendedores)]
## Creacion de features
fact_ciudades = datos.groupby('Lugar de Compra')[['Precio']].sum()

fact_ciudades = datos.drop_duplicates(subset='Lugar de Compra')[['Lugar de Compra', 'lat', 'lon']].merge(fact_ciudades, left_on= 'Lugar de Compra', right_index=True).sort_values('Precio', ascending =False)

facturacion_mensual = datos.set_index('Fecha de Compra').groupby(pd.Grouper(freq='ME'))['Precio'].sum().reset_index()

facturacion_mensual['Año'] = facturacion_mensual['Fecha de Compra'].dt.year
facturacion_mensual['Mes'] = facturacion_mensual['Fecha de Compra'].dt.month_name('es')

datos = datos.rename(columns={"Categoría del Producto": 'Categoria del Producto'})
facturacion_categoria = datos.groupby('Categoria del Producto')[['Precio']].sum().sort_values('Precio', ascending=False)

vendedores = pd.DataFrame(datos.groupby('Vendedor')['Precio'].agg(['sum', 'count']))

#Tabla de cantidad de ventas por estado
vendas_estados = pd.DataFrame(datos.groupby('Lugar de Compra')['Precio'].count())
vendas_estados = datos.drop_duplicates(subset='Lugar de Compra')[['Lugar de Compra','lat', 'lon']].merge(vendas_estados, left_on='Lugar de Compra', right_index=True).sort_values('Precio', ascending=False)

#Tabla de cantidad de ventas mensual
vendas_mensal = pd.DataFrame(datos.set_index('Fecha de Compra').groupby(pd.Grouper(freq='M'))['Precio'].count()).reset_index()
vendas_mensal['Año'] = vendas_mensal['Fecha de Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Fecha de Compra'].dt.month_name()

#Tabla de cantidad de ventas por categoría de productos
vendas_categorias = pd.DataFrame(datos.groupby('Categoria del Producto')['Precio'].count().sort_values(ascending=False))

## Creacion de graficos

fig_facturacion = px.scatter_geo(fact_ciudades, lat='lat', lon='lon',
                                scope='south america', size= 'Precio',
                                template ='seaborn', hover_name='Lugar de Compra',
                                hover_data={'lat':False, 'lon':False},
                                title= 'Facturación por ciudad')

fig_facturacion.update_geos(fitbounds='locations')

fig_facturacion_mesnsual = px.line(facturacion_mensual, x='Mes', y='Precio',
                                    markers =True, range_y=(0, facturacion_mensual.max()),
                                    color='Año', line_dash='Año',
                                    title='Facturación mensual')

fig_facturacion_mesnsual.update_layout(yaxis_title='Facturación')

fig_facturacion_ciudades = px.bar(fact_ciudades.head(), x='Lugar de Compra', y='Precio',
                                text_auto=True, title='Top ciudades (Facturación)')

fig_facturacion_ciudades.update_layout(yaxis_title='Facturación')

fig_facturacion_categoria = px.bar(facturacion_categoria, text_auto=True,
                                    title='Facturación por Categoria')

fig_facturacion_categoria.update_layout(yaxis_title='Facturación')

# Gráfico de mapa de cantidad de ventas por estado
fig_mapa_ventas = px.scatter_geo(vendas_estados,
                                lat='lat',
                                lon='lon',
                                scope='south america',
                                #fitbounds='locations',
                                template='seaborn',
                                size='Precio',
                                hover_name='Lugar de Compra',
                                hover_data={'lat':False, 'lon':False},
                                title='Ventas por estado')

# Gráfico de cantidad de ventas mensual
fig_ventas_mensal = px.line(vendas_mensal,
                            x='Mes',
                            y='Precio',
                            markers=True,
                            range_y=(0, vendas_mensal.max()),
                            color='Año',
                            line_dash='Año',
                            title='Cantidad de ventas mensual')

fig_ventas_mensal.update_layout(yaxis_title='Cantidad de ventas')

# Gráfico de los 5 estados con mayor cantidad de ventas
fig_ventas_estados = px.bar(vendas_estados.head(),
                            x='Lugar de Compra',
                            y='Precio',
                            text_auto=True,
                            title='Top 5 estados')

fig_ventas_estados.update_layout(yaxis_title='Cantidad de ventas')

# Gráfico de cantidad de ventas por categoría de producto
fig_ventas_categorias = px.bar(vendas_categorias,
                                text_auto=True,
                                title='Ventas por categoría')

fig_ventas_categorias.update_layout(showlegend=False, yaxis_title='Cantidad de ventas')



## Contenedores (prestañas)
tab1, tab2, tab3 = st.tabs(['Facturación', 'Cantidad de ventas', 'Vendedores'])

## Columnas
## Facturacion
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.metric('Facturación', fromato_numero(datos['Precio'].sum(), 'COP'))
        st.plotly_chart(fig_facturacion, use_container_width=True)
        st.plotly_chart(fig_facturacion_ciudades, use_container_width=True)
    with col2:
        st.metric('Cantidad de ventas', fromato_numero(datos.shape[0]))
        st.plotly_chart(fig_facturacion_mesnsual, use_container_width=True)
        st.plotly_chart(fig_facturacion_categoria, use_container_width=True)

## Cantidad de ventas
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.metric('Facturación', fromato_numero(datos['Precio'].sum(), 'COP'))
        st.plotly_chart(fig_mapa_ventas, use_container_width=True)
        st.plotly_chart(fig_ventas_estados, use_container_width=True)

    with col2:
        st.metric('Cantidad de ventas', fromato_numero(datos.shape[0]))
        st.plotly_chart(fig_ventas_mensal, use_container_width=True)
        st.plotly_chart(fig_ventas_categorias, use_container_width=True)

## Vendedores
with tab3:
    ct_vendedores = st.number_input('Cantidad de vendedores', 2,10,5)
    col1, col2 = st.columns(2)

    with col1:
        st.metric('Facturación', fromato_numero(datos['Precio'].sum(), 'COP'))

        fig_facturacion_vendedores = px.bar(vendedores[['sum']].sort_values('sum').head(ct_vendedores), x='sum', y=vendedores[['sum']].sort_values('sum').head(ct_vendedores).index, text_auto=True, title= f'Top {ct_vendedores} Vendedores (Facturación)')
        st.plotly_chart(fig_facturacion_vendedores)

    with col2:
        st.metric('Cantidad de ventas', fromato_numero(datos.shape[0]))

        fig_cantidad_ventas = px.bar(vendedores[['count']].sort_values('count').head(ct_vendedores), x='count', y=vendedores[['count']].sort_values('count').head(ct_vendedores).index, text_auto=True, title= f'Top {ct_vendedores} Vendedores (Cantidad de ventas)')
        st.plotly_chart(fig_cantidad_ventas)



# st.dataframe(datos)