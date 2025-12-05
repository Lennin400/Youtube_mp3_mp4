from django.shortcuts import render #esto es para mostrar las plantillas de templates
from django.shortcuts import redirect #esto es para redirigir otrasladar a otra pagina
from django.urls import reverse #esto es para obtener la url de una vista por su nombre
import os #esto es para manejar rutas de archivos
import uuid #esto es para generar nombres unicos
import yt_dlp #esto es para descargar videos de youtube
from django.http import FileResponse, HttpResponse #esto es para manejar respuestas de archivos ... el FileResponse es 
                                                    #para enviar archivos como respuestas al usuario y el HttpResponse es para enviar respuestas HTTP simples
from django.conf import settings #esto es para acceder a la configuración de proyecto django 
from .forms import DownloadForm # esto lo estamos importando del achivo forms.py para manejar formularios
import threading  # AGREGADO: Para limpiar archivos después
import time  # AGREGADO: Para manejar tiempos

# Create your views here.


def home(request): # esta funcion muestra la plantilla home.html

    if request.method == 'POST': # si el metodo de la solicitud es POST 
        form = DownloadForm(request.POST) # creamos una instancia del formulario con los datos enviados por el usuario 
        if form.is_valid(): # si el formulario es valido
            # obtenemos los datos del formulario
            url = form.cleaned_data['url'] # estamos usando cleaned_data de forms.py para obtener el valor del campo URL
            format_type = form.cleaned_data['format'] # obtenemos el valor del campo formato (mp4 o mp3)
            quality = form.cleaned_data['quality'] # obtenemos el valor del campo calidad (mejor calidad, 1080p, 720p, etc)

            # DEBUG: Agrega esto para ver qué está pasando
            print("=" * 60)
            print(f"📥 URL recibida: {url}")
            print(f"🎵 Formato: {format_type}")
            print(f"📊 Calidad: {quality}")

            #generamos un nombre unico para el archivo descargado
            unique_id = str(uuid.uuid4()) [:8] # generamos un id unico y tomamos los primeros 8 caracteres
            downloads_dir = os.path.join(settings.BASE_DIR, 'downloads')# unimos la ruta base del proyecto con la carpeta downloads para guardar los archivos descargados 
            os.makedirs(downloads_dir, exist_ok=True)# creamos la carpeta downloads si no existe 

            # configuramos las opciones de yt_dlp para descargar el video o audio

            ydl_opts = { # opciones de yt_dlp
                'outtmpl': os.path.join(downloads_dir, f'{unique_id}.%(ext)s'), # plantilla para el nombre del archivo de salida
                'quiet': False,  # CAMBIADO: Poner False para ver los logs
                'no_warnings': False,  # CAMBIADO: Poner False para ver warnings

            }

            if format_type == 'mp3': # si el usuario elegío mp3
                #configuramos las opciones para descargar audio en mpe
                ydl_opts['format'] = 'bestaudio/best' # descargamos el mejor audio disponible
                # CORRECCIÓN: quality puede ser 'best', no siempre es número
                audio_quality = '192'  # default
                if quality.isdigit():
                    audio_quality = quality
                elif quality == 'best':
                    audio_quality = '320'
                
                ydl_opts['postprocessors'] = [{   #con esto le decimos a yt_dlp que use el postprecesador para convertir a mp3
                    'key': 'FFmpegExtractAudio', #usamos FFmpeg para extraer audio
                    'preferredcodec': 'mp3', #convertimos a mp3
                    'preferredquality': audio_quality, # calidad del audio segun la  eleccion del usuario 

                }]
                file_extension = 'mp3' # extension del archivo descargado para que salga como mp3

            else: # si el usuario elegío mp4
                # configuramos las opciones para descargar video en mp4
                if quality == 'best' : # si el usuario elegío mejor calidad
                    ydl_opts['format'] = 'best[height<=1080]/best' # descargamos el mejor video disponible hasta 1080p
                else:
                    # CORRECCIÓN: Asegurar que quality sea un número
                    try:
                        quality_num = int(quality)
                        ydl_opts['format'] = f'best[height<={quality_num}]/best' # descargamos el mejor video disponible hasta la calidad elegida por el usuario
                    except:
                        ydl_opts['format'] = 'best[height<=720]/best'  # default
                file_extension = 'mp4' # extension del archivo descargado para que salga como mp4

            try:
                # DEBUG
                print(f"🚀 Iniciando descarga...")
                
                #descargamos el video o audio usando yt_dlp con las opciones configuradas
                with yt_dlp.YoutubeDL(ydl_opts) as ydl: # creamos una instancia de YoutubeDl con las opciones configuradas
                    info = ydl.extract_info(url, download=True) # extraemos la informacion del video y lo descargamos
                    title = info.get('title', 'video').replace(' ', '_')# obtenemos el titulo del video y reemplazamos los espacios para que no haya problemas con los nombres de archivos
                    print(f"✅ Video descargado: {title}")

                # ruta del archivo descargado
                file_path = os.path.join(downloads_dir, f'{unique_id}.{file_extension}') # unimos la ruta de descargas con el nombre unico y la extension del archivo
                
                # DEBUG: Verificar que el archivo existe
                if not os.path.exists(file_path):
                    # Buscar el archivo con cualquier extensión
                    import glob
                    pattern = os.path.join(downloads_dir, f'{unique_id}.*')
                    files = glob.glob(pattern)
                    if files:
                        file_path = files[0]
                        print(f"🔍 Archivo encontrado: {file_path}")
                    else:
                        return HttpResponse(f'❌ Error: Archivo no encontrado después de descargar', status=400)
                
                # NUEVA FUNCIÓN: Limpiar archivo después de 1 minuto
                def clean_file_later(file_to_clean):
                    time.sleep(60)  # Esperar 1 minuto
                    try:
                        if os.path.exists(file_to_clean):
                            os.remove(file_to_clean)
                            print(f"🧹 Archivo eliminado: {file_to_clean}")
                    except:
                        pass
                
                # Iniciar limpieza en segundo plano
                cleanup_thread = threading.Thread(target=clean_file_later, args=(file_path,))
                cleanup_thread.daemon = True
                cleanup_thread.start()
                
                #enviamos el archivo descargado como respuesta al usuario
                response = FileResponse( # creamos la variable response como una instancia de FileResponse
                    open(file_path, 'rb'), # abrimos el archivo en modo lectura binaria
                    as_attachment=True, # le decimos que es un archivo adjunto para que se descargue 
                    filename=f'{title[:50]}.{file_extension}' # nombre del archivo que vera el usuario (limitado a 50 caracteres)
                )
                
                # 🚨 CAMBIO CRÍTICO: NO eliminar inmediatamente
                # os.remove(file_path)  # ¡COMENTADO! Esto causaba el problema

                response.set_cookie('just_downloaded', 'true', max_age=5) # esto va a hacer que aparezca la notificacion de descarga en la pantalla principal


                print(f"📤 Enviando archivo: {title[:50]}.{file_extension}")
                return response
                
            except Exception as e:
                import traceback
                print(f"❌ Error en descarga: {str(e)}")
                print(traceback.format_exc())  # Mostrar el error completo
                return HttpResponse(f'❌ Error: {str(e)}', status=400)
        else:
            # Si el formulario no es válido
            print(f"❌ Errores del formulario: {form.errors}")
            return HttpResponse(f'❌ Errores en el formulario: {form.errors}', status=400)
    else:
        form = DownloadForm() # si el metodo no es POST, creamos una instancia vacía del formulario

    return render(request , 'core/index.html', {'form': form}) # renderizamos la platilla index.html con el formulario

# En core/views.py, agrega esta función
def test_direct(request):

    '''Prueba directa sin formulario'''
    try:
        url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        downloads_dir = os.path.join(settings.BASE_DIR, 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        ydl_opts = {
            'format': 'worst',  # Más rápido para prueba
            'outtmpl': os.path.join(downloads_dir, 'test.%(ext)s'),
            'quiet': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
        # Buscar archivo
        import glob
        files = glob.glob(os.path.join(downloads_dir, 'test.*'))
        
        if files:
            return FileResponse(
                open(files[0], 'rb'),
                as_attachment=True,
                filename='test_video.mp4'
            )
        return HttpResponse("❌ Archivo no encontrado")
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}")
    
