import streamlit as st
import google.generativeai as genai
import json
import time

# --- CONFIGURACIÓN DE LA PÁGINA Y API ---

# Configuración de la página de Streamlit (debe ser el primer comando de st)
st.set_page_config(
    page_title="Quiz de Álgebra Lineal",
    #page_icon="🧠",
    layout="centered"
)

# Configuración de la API de Google
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Creación del modelo
    model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    st.error(f"Error al configurar la API de Google: {e}")
    st.error("Asegúrate de haber configurado tu GOOGLE_API_KEY en los secretos de Streamlit.")
    st.stop()


# --- FUNCIONES AUXILIARES ---

def reset_app():
    """Limpia todo el estado de la sesión y reinicia la aplicación."""
    # Iterar sobre una copia de las claves para poder modificar el diccionario
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def generar_quiz_con_ia():
    """
    Función que llama a la API de Google para generar el quiz.
    Utiliza un prompt detallado para asegurar el formato JSON correcto.
    """
    prompt = """
    Actúa como un matemático experto en álgebra lineal y un excelente pedagogo. 
    Tu tarea es crear un quiz de 10 preguntas de nivel intermedio/avanzado sobre razonamiento lógico en álgebra lineal.
    No te enfoques solo en cálculos mecánicos, sino en la interpretación de conceptos clave.
    Los temas deben incluir: espacios vectoriales, transformaciones lineales, independencia lineal,
    valores y vectores propios, significado geométrico de los determinantes, formas canónicas elementales y espacios con producto interior. 

    Cada pregunta debe tener 4 opciones de respuesta (A, B, C, D).
    Usa código LaTeX para las fórmulas pero asegúrate de colocar el signo dólar ($) antes y despues de la fórmula y que sea 100% compatible con JSON (para evitar errores de escape)

    Devuelve el resultado ÚNICAMENTE en formato JSON válido. No incluyas texto, explicaciones o ```json```
    antes o después del propio objeto JSON. El JSON debe ser una lista de 10 objetos.

    Cada objeto en la lista debe tener exactamente las siguientes claves:
    - "pregunta": (string) El texto de la pregunta.
    - "opciones": (dict) Un diccionario con claves "A", "B", "C", "D" y sus respectivos textos como valores.
    - "respuesta_correcta": (string) La letra de la opción correcta (e.g., "C").
    - "explicacion": (string) Una explicación clara y concisa de por qué la respuesta es correcta y, si es posible, por qué las otras son incorrectas.
    
    Ejemplo de un objeto en la lista:
    {
        "pregunta": "¿Qué representa el determinante de una matriz 2x2 en un contexto geométrico?",
        "opciones": {
            "A": "La longitud del vector más largo de la matriz.",
            "B": "El área del paralelogramo formado por los vectores columna de la matriz.",
            "C": "La suma de los elementos de la diagonal.",
            "D": "El ángulo entre los dos vectores columna."
        },
        "respuesta_correcta": "B",
        "explicacion": "El valor absoluto del determinante de una matriz 2x2 representa el factor de escala del área de una transformación lineal. Específicamente, es el área del paralelogramo definido por los vectores columna de la matriz."
    }
    """
    try:
        response = model.generate_content(prompt)
        # Limpiar la respuesta para asegurar que sea solo JSON
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        quiz_data = json.loads(json_text)
        # Verificación básica del formato
        if isinstance(quiz_data, list) and len(quiz_data) == 10 and all('pregunta' in q for q in quiz_data):
            return quiz_data
        else:
            st.error("La IA generó una respuesta con un formato inesperado. Intentando de nuevo...")
            time.sleep(2) # Esperar antes de reintentar
            return None # Devolver None para que el código principal pueda reintentar
    except (json.JSONDecodeError, AttributeError, Exception) as e:
        #st.error(f"Hubo un problema al generar o procesar el quiz: {e}")
        st.info("A veces, la IA no responde con el formato exacto. Intentando de nuevo...")
        time.sleep(2) # Esperar antes de reintentar
        return None


# --- INICIALIZACIÓN DEL ESTADO DE LA SESIÓN ---

if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'
if 'nombre_estudiante' not in st.session_state:
    st.session_state.nombre_estudiante = ""
if 'quiz_generado' not in st.session_state:
    st.session_state.quiz_generado = None
if 'pregunta_actual' not in st.session_state:
    st.session_state.pregunta_actual = 0
if 'respuestas_usuario' not in st.session_state:
    st.session_state.respuestas_usuario = {}
if 'puntaje' not in st.session_state:
    st.session_state.puntaje = 0
if 'respuesta_enviada' not in st.session_state:
    st.session_state.respuesta_enviada = False

# --- LÓGICA DE LAS PÁGINAS ---

# PÁGINA DE INICIO
if st.session_state.pagina == 'inicio':
    st.title("Quiz de álgebra lineal")
    st.markdown("""
    Este es un quiz interactivo para poner a prueba la comprensión conceptual del álgebra lineal.
    
    El quiz consta de **10 preguntas** de opción múltiple generadas por una **IA**.
    Después de cada respuesta, recibirás una explicación detallada.
    
    ¡Mucha suerte!
    """)
    
    nombre = st.text_input("Por favor, ingresa tu nombre para personalizar tu experiencia:", key="input_nombre")
    
    if st.button("Generar Quiz", type="primary"):
        if nombre:
            st.session_state.nombre_estudiante = nombre
            # Generar el quiz solo una vez
            with st.spinner("""
            Preparando tu quiz **personalizado**... Esto puede tardar varios segundos
            * Ten paciencia. La comunicación con la API de la IA puede demorar.
            * Además, se esta usando un modelo que incrementa el tiempo de razonamiento.
            """):
                quiz_data = None
                # Intentar generar el quiz hasta 3 veces si falla
                for i in range(3):
                    quiz_data = generar_quiz_con_ia()
                    if quiz_data:
                        break
                
                if quiz_data:
                    st.session_state.quiz_generado = quiz_data
                    st.session_state.pagina = 'quiz'
                    st.rerun()
                else:
                    st.error("No se pudo generar el quiz después de varios intentos. Por favor, recarga la página para intentarlo de nuevo.")
                    if st.button("Reiniciar Aplicación"):
                    	reset_app()
                    	
                    st.stop()
        else:
            st.warning("Debes ingresar un nombre para continuar.")

# PÁGINA DEL QUIZ
elif st.session_state.pagina == 'quiz':
    st.header(f"Quiz para {st.session_state.nombre_estudiante}")
    st.progress((st.session_state.pregunta_actual) / 10)
    
    # Obtener la pregunta actual
    idx = st.session_state.pregunta_actual
    pregunta_info = st.session_state.quiz_generado[idx]
    
    st.subheader(f"Pregunta {idx + 1}/10")
    st.markdown(f"**{pregunta_info['pregunta']}**")
    
    # Usar un formulario para agrupar las opciones y el botón
    with st.form(key=f"form_pregunta_{idx}"):
        opciones = pregunta_info['opciones']
        # Mostramos las opciones solo si la respuesta no ha sido enviada
        if not st.session_state.respuesta_enviada:
            respuesta_usuario = st.radio(
                "Selecciona tu respuesta:",
                options=list(opciones.keys()),
                format_func=lambda key: f"{key}: {opciones[key]}",
                key=f"radio_{idx}"
            )
        
        submitted = st.form_submit_button("Enviar Respuesta")

        if submitted and not st.session_state.respuesta_enviada:
            st.session_state.respuesta_enviada = True
            st.session_state.respuestas_usuario[idx] = respuesta_usuario
            if respuesta_usuario == pregunta_info['respuesta_correcta']:
                st.session_state.puntaje += 1
            st.rerun()

    # Mostrar la explicación después de enviar la respuesta
    if st.session_state.respuesta_enviada:
        respuesta_correcta = pregunta_info['respuesta_correcta']
        opcion_elegida = st.session_state.respuestas_usuario[idx]
        
        if opcion_elegida == respuesta_correcta:
            st.success(f"¡Correcto! La respuesta es la **{respuesta_correcta}**.")
            #texto_completo_respuesta = pregunta_info['opciones'][respuesta_correcta]
        else:
        	texto_completo_respuesta = pregunta_info['opciones'][respuesta_correcta]
        	texto_completo_eleccion = pregunta_info['opciones'][opcion_elegida]
        	st.error(f"**Incorrecto**. \n* Tu respuesta fue la **{opcion_elegida}**: {texto_completo_eleccion} \n* La respuesta correcta era la **{respuesta_correcta}**: {texto_completo_respuesta}")
        
        st.info(f"**Explicación:**\n{pregunta_info['explicacion']}")
        
        # Botón para pasar a la siguiente pregunta o ver resultados
        if st.session_state.pregunta_actual < 6:
            if st.button("Siguiente Pregunta"):
                st.session_state.pregunta_actual += 1
                st.session_state.respuesta_enviada = False
                st.rerun()
        else:
            if st.button("Ver Resultados Finales", type="primary"):
                st.session_state.pagina = 'resultados'
                st.rerun()

# PÁGINA DE RESULTADOS
elif st.session_state.pagina == 'resultados':
    st.title("Resultados Finales")
    
    puntaje_final = st.session_state.puntaje
    nombre = st.session_state.nombre_estudiante
    
    st.markdown(f"### {nombre} ha finalizado el quiz")
    
    # Calcular calificación en base a 20
    calificacion = (puntaje_final / 7) * 20
    
    col1, col2 = st.columns(2)
    
    with col1:
    	st.metric(label="Respuestas Correctas", value=f"{puntaje_final} de 7", border=True)
    	
    with col2:
    	st.metric(label="Calificación (sobre 20)", value=f"{calificacion:.2f}", border=True)
    	
    # st.divider()

    # Mensaje de retroalimentación
    if calificacion >= 18:
        st.success("¡Excelente! Tienes un dominio impresionante de los conceptos.")
        st.balloons()
    elif calificacion >= 14:
        st.info("¡Muy bien! Tienes una base sólida, sigue así.")
    elif calificacion >= 10:
        st.warning("¡Buen esfuerzo! Hay algunos conceptos que puedes repasar para fortalecer tu conocimiento.")
    else:
        st.error("No te desanimes. El álgebra lineal es un desafío. ¡Sigue practicando y verás cómo mejoras!")

    if st.button("Reiniciar Quiz"):
        # Reiniciar todos los estados para empezar de nuevo
        for key in list(st.session_state.keys()):
            if key != 'nombre_estudiante':  # Opcional: mantener el nombre
                del st.session_state[key]

        # Reinicializar valores necesarios
        st.session_state.pagina = 'inicio'
        st.rerun()
        
        
# --- Footer ---
st.caption("DEMAT-FEC-LUZ")
