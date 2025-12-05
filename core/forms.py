from django import forms # esto es para validar y manejar formularios en django ....

class DownloadForm(forms.Form): #creamos la clase DownloadForm que hereda de forms.Form ..
                                #esta clase crea un formulario con un campo de URL
# opciones de formato de descarga
    FORMAT_CHOICES = [                 #esto es una lista para las opciones de formato que tendra el usuario 
        ('mp4', '🎬 Video (MP4)'),     # le estamos diciendo que puede eligir descargar mp4 o mp3
         ('mp3', '🎵 Solo Audio (MP3)'),
        
    ]

# opciones de calidad de (video)
    VIDEO_QUALITY = [                  #le estamos diciendo las opciones de calidad que tendra el usuario para descargar el video
        ('best', '🔥 Mejor calidad'),
        ('1080', '📺 1080p (Full HD)'),
        ('720', '🖥️ 720p (HD)'),
        ('480', '📱 480p'),
        ('360', '📟 360p'),
        ('240', '🕹️ 240p'),
        ('144', '⌚ 144p'),
    ]

# opciones de calidad de (audio)

    AUDIO_QUALITIES = [
        ('320', '🎧 320 kbps (Excelente)'),
        ('256', '🎵 256 kbps (Muy bueno)'),
        ('192', '🎶 192 kbps (Bueno)'),
        ('128', '📻 128 kbps (Estándar)'),
        ('64', '📱 64 kbps (Bajo)'),
    ]

# Campos del formulario
    url = forms.URLField(
        label= 'Ingresa la URL del video', # le damos una etiqueta al campo de URL
        # widget es para personalizar el campo de entrada y forms.URLInput es para especificar que es un campo de URL
        widget=forms.URLInput(attrs= {'placeholder': 'https://www.youtube.com/watch?v=...',
            'class': 'w-full px-4 py-3 rounded-lg border-2 border-pink-500 bg-gray-800 text-white focus:outline-none focus:border-pink-300',
            'required': True,}) # con esto le damos estilo al campo de entrada de URL

    )
# con esto le damos al usuario la opcion de elegir el formato de descarga (mp4 o mp3)
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        widget=forms.RadioSelect(attrs={ #con esto le damos estilo a la opciones de formato
            'class': 'format-radio hidden', # y con forms.RadioSelect le decimos que es un campo de opciones  de  formato
            'onchange':'changeQualityOptions()', 
        }),
        initial='mp4' # le decimos que la opcion inicial es mp4

    )
    
    quality = forms.ChoiceField(
        
        choices= VIDEO_QUALITY, #le decimos que las opciones de calidad son las que definimos en VIDEO_QUALITY 
        widget=forms.Select(attrs={ # con forms.Select le decimos que es un campo de seleccion desplegable
            'class': 'w-full px-4 py-3 rounded-lg border-2 border-purple-500 bg-gray-800 text-white focus:outline-none focus:border-purple-300',
            'id': 'quality-select',
        })

    )

# validación personalizada para el campo de URL
    def clean_url(self): # con esta funcion validamos el campo de URL
        url = self.cleaned_data['url'] # con esto obtenemos el valor del campo de URL
        if 'youtube.com' not in url and 'youtu.be' not in url: # si la URL no contiene youtube.con o youtube.be 
            raise forms.ValidationError ('Solo se permiten URLS de Youtube') # lanzamo un error de validación 
        return url # si la url es valida la devolvemos como esta 