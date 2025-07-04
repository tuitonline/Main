import os
import json
import requests
import logging
from telegram import Update, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Configurar logging para ver errores
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración de claves
try:
    from dotenv import load_dotenv
    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    
    # Verificar que las claves existen
    if not TELEGRAM_BOT_TOKEN or not DEEPSEEK_API_KEY:
        logger.error("❌ ERROR: Las claves de API no se encontraron en .env")
        raise ValueError("Missing API keys in environment variables")
        
except ImportError:
    logger.warning("⚠️ Advertencia: python-dotenv no está instalado. Usando valores directos.")
    TELEGRAM_BOT_TOKEN = "TU_TELEGRAM_TOKEN"  # Reemplaza con tu token real
    DEEPSEEK_API_KEY = "TU_DEEPSEEK_API_KEY"   # Reemplaza con tu API key real
except Exception as e:
    logger.error(f"❌ Error cargando variables: {e}")
    raise

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Función para /start
def start(update: Update, context: CallbackContext) -> None:
    try:
        logger.info(f"Comando /start recibido de {update.effective_user.id}")
        mensaje = (
            "🎙️ ¡Bienvenido al conversatorio de tecnología!\n"
            "Hoy respondemos: *Internet lento, WiFi débil... ¿Es culpa del router o del vecino?*\n\n"
            "Hazme cualquier pregunta sobre WiFi, velocidad de internet o cómo mejorar tu red."
        )
        update.message.reply_text(mensaje, parse_mode="Markdown")
        logger.info("Mensaje de bienvenida enviado")
    except Exception as e:
        logger.error(f"Error en /start: {e}")

# Función para manejar mensajes
def handle_message(update: Update, context: CallbackContext) -> None:
    try:
        pregunta = update.message.text
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        logger.info(f"Mensaje recibido de {user_id}: {pregunta[:50]}{'...' if len(pregunta) > 50 else ''}")
        
        # Enviar indicador de "escribiendo..."
        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # Construir payload para DeepSeek
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un experto en redes WiFi y tecnología de consumo. Responde de forma sencilla, con humor y sin tecnicismos."
                },
                {"role": "user", "content": pregunta}
            ],
            "max_tokens": 600
        }
        
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        logger.info("Enviando solicitud a DeepSeek API...")
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload  # Usamos json= en lugar de data=json.dumps()
        )
        
        # Verificar respuesta HTTP
        response.raise_for_status()
        logger.info(f"DeepSeek API respondió con código: {response.status_code}")
        
        # Procesar respuesta JSON
        respuesta_json = response.json()
        texto_respuesta = respuesta_json['choices'][0]['message']['content'].strip()
        
        logger.info(f"Respuesta recibida: {texto_respuesta[:50]}{'...' if len(texto_respuesta) > 50 else ''}")
        
        # Enviar respuesta en fragmentos si es necesario
        max_length = 4000  # Límite de Telegram por mensaje
        for i in range(0, len(texto_respuesta), max_length):
            context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            fragmento = texto_respuesta[i:i+max_length]
            update.message.reply_text(fragmento)
        
        logger.info("Respuesta enviada exitosamente")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión con DeepSeek: {e}")
        update.message.reply_text("🔌 ¡Ups! Estoy teniendo problemas para conectar con mi cerebro. ¿Podrías intentarlo más tarde?")
    except KeyError as e:
        logger.error(f"Error procesando respuesta de DeepSeek: {e}")
        update.message.reply_text("🧠 ¡Vaya! Mi cerebro respondió de forma inesperada. ¿Puedes reformular tu pregunta?")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        update.message.reply_text("⚠️ ¡Ay! Algo salió mal. ¿Podrías intentarlo de nuevo?")

# Función principal
def main() -> None:
    logger.info("Iniciando bot...")
    
    try:
        updater = Updater(TELEGRAM_BOT_TOKEN)
        dispatcher = updater.dispatcher
        
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        logger.info("Bot iniciado. Escuchando mensajes...")
        print("🤖 Bot DeepSeek corriendo. Abre Telegram y escribe /start")
        
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"Error fatal al iniciar el bot: {e}")
        print(f"❌ ERROR: No se pudo iniciar el bot: {e}")

if __name__ == '__main__':
    main()