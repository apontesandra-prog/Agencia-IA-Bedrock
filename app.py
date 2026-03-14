import streamlit as st
import boto3
import json
import base64
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Agencia IA", layout="wide")

# --- MEMORIA A CORTO PLAZO DE LA APP (Historial y Galería) ---
if "galeria" not in st.session_state:
    st.session_state.galeria = []
if "historial_textos" not in st.session_state:
    st.session_state.historial_textos = []
if "comentarios" not in st.session_state:
    st.session_state.comentarios = []

st.title("Agencia IA - Espacio Creativo 🚀")
st.markdown("Herramienta colaborativa con Amazon Bedrock.")

# --- BARRA LATERAL: ROLES Y SEGURIDAD ---
st.sidebar.header("👤 Inicio de Sesión (Simulado)")
rol = st.sidebar.selectbox("Selecciona tu Rol:", ["Administrador (Acceso Total)", "Diseñador", "Redactor", "Aprobador"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configuración de AWS")
aws_access_key = st.sidebar.text_input("Access Key", type="password")
aws_secret_key = st.sidebar.text_input("Secret Key", type="password")
region = st.sidebar.selectbox("Región de AWS:", ["us-west-2", "us-east-1"])
model_id_img = st.sidebar.text_input("Model ID (Imágenes):", value="stability.sd3-5-large-v1:0")

# --- PESTAÑAS DE NAVEGACIÓN ---
tab_img, tab_txt, tab_colab, tab_etica = st.tabs([
    "🎨 Generación de Imágenes", 
    "✍️ Edición de Contenido", 
    "✅ Colaboración y Aprobación", 
    "🛡️ Ética y Seguridad"
])

# --- PESTAÑA 1: IMÁGENES (Solo Diseñadores y Administradores) ---
with tab_img:
    if rol in ["Administrador (Acceso Total)", "Diseñador"]:
        st.subheader("Estudio de Diseño (Stable Diffusion)")
        descripcion = st.text_area("Describe la imagen que quieres generar:")
        estilo = st.selectbox("Selecciona un estilo:", ["Ninguno", "Anime", "Pintura al óleo", "Realismo"])
        
        if st.button("Generar Imagen"):
            if not aws_access_key or not aws_secret_key:
                st.warning("⚠️ Ingresa tus llaves de AWS en la barra lateral.")
            else:
                with st.spinner("Creando la magia..."):
                    try:
                        bedrock = boto3.client('bedrock-runtime', region_name=region, aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
                        prompt_final = descripcion
                        if estilo == "Anime": prompt_final += ", anime style, studio ghibli, highly detailed"
                        elif estilo == "Pintura al óleo": prompt_final += ", oil painting style, masterpiece"
                        elif estilo == "Realismo": prompt_final += ", ultra realistic, photographic"

                        body = {"prompt": prompt_final, "mode": "text-to-image", "aspect_ratio": "1:1", "output_format": "png"}
                        response = bedrock.invoke_model(modelId=model_id_img.strip(), body=json.dumps(body))
                        
                        response_body = json.loads(response.get("body").read())
                        
                        # ESCUDO PROTECTOR PARA IMÁGENES
                        if "images" in response_body:
                            base64_image = response_body["images"][0]
                            image = Image.open(BytesIO(base64.b64decode(base64_image)))
                            
                            st.image(image, caption=f"Estilo: {estilo}")
                            st.success("¡Imagen generada!")
                            
                            st.session_state.galeria.append({"prompt": descripcion, "estilo": estilo, "imagen": image})
                        else:
                            st.error("⚠️ La IA no devolvió una imagen. Es probable que tu texto haya activado los filtros de seguridad de Amazon. Intenta con otra descripción.")
                            
                    except Exception as e:
                        st.error(f"Error de AWS: {e}")
    else:
        st.warning("🔒 Acceso denegado. Esta herramienta es exclusiva para Diseñadores y Administradores.")

# --- PESTAÑA 2: TEXTOS (Solo Redactores y Administradores) ---
with tab_txt:
    if rol in ["Administrador (Acceso Total)", "Redactor"]:
        st.subheader("Sala de Redacción (Claude)")
        texto_original = st.text_area("Pega aquí el texto que deseas editar:")
        accion = st.selectbox("¿Qué quieres hacer?", ["Resumir texto", "Expandir ideas", "Corregir errores gramaticales y de estilo", "Generar variaciones"])
        
        if st.button("Editar Texto"):
            if not aws_access_key or not aws_secret_key:
                st.warning("⚠️ Ingresa tus llaves de AWS en la barra lateral.")
            else:
                with st.spinner("Claude está editando..."):
                    try:
                        bedrock_texto = boto3.client('bedrock-runtime', region_name=region, aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
                        instruccion = f"Actúa como un editor experto de marketing. Tu tarea es {accion.lower()} del siguiente texto. Devuelve ÚNICAMENTE el texto editado.\n\nTexto original: {texto_original}"
                        body = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 1000, "messages": [{"role": "user", "content": instruccion}]}
                        
                        # Usamos Claude 3 Haiku porque es muy rápido y bueno para textos
                        response = bedrock_texto.invoke_model(modelId="anthropic.claude-3-haiku-20240307-v1:0", body=json.dumps(body))
                        response_body = json.loads(response.get("body").read())
                        
                        # ESCUDO PROTECTOR PARA TEXTOS
                        if "content" in response_body:
                            texto_final = response_body["content"][0]["text"]
                            st.write("### Resultado final:")
                            st.info(texto_final)
                            
                            st.session_state.historial_textos.append({"original": texto_original, "nuevo": texto_final, "accion": accion})
                        else:
                            st.error("⚠️ La IA no devolvió el texto editado. Verifica que Claude 3 Haiku esté activado en tu consola de AWS Bedrock.")
                            
                    except Exception as e:
                        st.error(f"Error de AWS con Claude: {e}")
    else:
        st.warning("🔒 Acceso denegado. Esta herramienta es exclusiva para Redactores y Administradores.")

# --- PESTAÑA 3: COLABORACIÓN E HISTORIAL ---
with tab_colab:
    st.subheader("Galería, Historial y Comentarios")
    st.markdown("Revisa el trabajo del equipo y deja retroalimentación.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 🖼️ Galería de Imágenes")
        if not st.session_state.galeria:
            st.write("Aún no hay imágenes generadas.")
        for i, item in enumerate(reversed(st.session_state.galeria)):
            st.image(item["imagen"], caption=f"Prompt: {item['prompt']}")
            
    with col2:
        st.write("#### 📝 Historial de Textos")
        if not st.session_state.historial_textos:
            st.write("Aún no hay textos editados.")
        for i, txt in enumerate(reversed(st.session_state.historial_textos)):
            with st.expander(f"Edición: {txt['accion']}"):
                st.markdown("**Versión Anterior:**")
                st.write(txt["original"])
                st.markdown("**Nueva Versión:**")
                st.info(txt["nuevo"])
                
    st.markdown("---")
    if rol in ["Administrador (Acceso Total)", "Aprobador"]:
        st.write("#### 💬 Dejar un comentario")
        nuevo_comentario = st.text_input("Escribe una nota para el equipo creativo:")
        if st.button("Enviar Comentario"):
            st.session_state.comentarios.append({"autor": rol, "nota": nuevo_comentario})
            st.success("Comentario guardado.")
    
    if st.session_state.comentarios:
        st.write("**Notas del equipo:**")
        for c in st.session_state.comentarios:
            st.warning(f"🗣️ {c['autor']}: {c['nota']}")

# --- PESTAÑA 4: ÉTICA Y SEGURIDAD ---
with tab_etica:
    st.subheader("Políticas de Uso de Inteligencia Artificial")
    st.markdown("""
    **1. Privacidad y Seguridad de Datos:** Toda comunicación con Amazon Bedrock se realiza mediante conexiones seguras cifradas. No se almacenan datos sensibles de los clientes en los prompts.
    
    **2. Mitigación de Sesgos:**
    Los prompts del sistema están diseñados para fomentar la diversidad. Las imágenes generadas no deben perpetuar estereotipos dañinos.
    
    **3. Derechos de Autor:**
    Queda estrictamente prohibido utilizar esta herramienta para copiar el estilo artístico exacto de artistas vivos o generar contenido protegido por copyright.
    
    **4. Moderación de Contenido:**
    Está prohibida la generación de material explícito, violento o desinformativo. Los usuarios deben reportar cualquier comportamiento anómalo de los modelos.
    """)