import discord
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import asyncio
import os

SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIPY_REDIRECT_URI = 'https://bot-discord-production-371e.up.railway.app/callback'  # Debe coincidir con la URI de redireccionamiento de tu aplicación de Spotify
SPOTIFY_ACCESS_TOKEN = os.getenv('SPOTIFY_ACCESS_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True}

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []

    @commands.command()
    async def join(self, ctx):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("No estás en un canal de voz.")
        
        await voice_channel.connect()
        await ctx.send(f"Conectado a {voice_channel.name}.")
    @commands.command()
    async def shuffle(self, ctx):
        """Mezcla las canciones en la cola."""
        if len(self.queue) > 1:
            random.shuffle(self.queue)  # Mezcla la lista de canciones
            await ctx.send("La cola de canciones ha sido mezclada.")
        else:
            await ctx.send("No hay suficientes canciones en la cola para mezclar.")
    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Desconectado del canal de voz.")
        else:
            await ctx.send("No estoy en ningún canal de voz.")
    @commands.command()
    async def play(self, ctx, *, search):
        """Reproduce una canción de YouTube."""
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("No estás en un canal de voz.")
        
        if not ctx.voice_client:
            await voice_channel.connect()

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url = info['url']
                title = info['title']
                self.queue.append((url, title))
                await ctx.send(f'Agregado a la cola: **{title}**')
                if not ctx.voice_client.is_playing():
                    await self.play_next(ctx)
    @commands.command()
    async def nextplay(self, ctx, *, search, insert=False):
        """Reproduce una canción de YouTube."""
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("No estás en un canal de voz.")
    
        if not ctx.voice_client:
            await voice_channel.connect()

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                    url = info['url']
                    title = info['title']

                if insert and ctx.voice_client.is_playing():
                    # Inserta la canción justo después de la actual
                    self.queue.insert(1, (url, title))
                    await ctx.send(f'Agregado como la siguiente canción: **{title}**')
                else:
                    # Agrega la canción al final de la cola
                    self.queue.append((url, title))
                    await ctx.send(f'Agregado a la cola: **{title}**')

                if not ctx.voice_client.is_playing():
                    await self.play_next(ctx)

    async def play_next(self, ctx):
        if self.queue:
            url, title = self.queue.pop(0)
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda e: self.client.loop.create_task(self.play_next(ctx)))
            await ctx.send(f'Reproduciendo ahora: **{title}**')
        else:
            await ctx.send("La cola está vacía.")
    async def sssplay(self, ctx, *, search):
        """Reproduce una canción de YouTube."""
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("No estás en un canal de voz.")
        
        if not ctx.voice_client:
            await voice_channel.connect()

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url = info['url']
                title = info['title']
                self.queue.append((url, title))
                #await ctx.send(f'Agregado a la cola: **{title}**')
                if not ctx.voice_client.is_playing():
                    await self.play_next(ctx)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()  # Detiene la reproducción actual
            await ctx.send("Canción saltada.")
           ## await self.play_next(ctx)  # Reproduce la siguiente canción en la cola
    
    @commands.command()
    async def clear(self, ctx):
        """Elimina toda la cola de canciones y detiene la playlist."""
        self.queue.clear()  # Vaciar la lista de la cola
        self.is_playing_playlist = False  # Detiene la reproducción de la playlist
        await ctx.send("La cola de canciones ha sido eliminada.")
        await self.skip(ctx)  # Salta la canción actual

    @commands.command()
    async def queue(self, ctx):
        if not self.queue:
            await ctx.send("La cola está vacía.")
        else:
            queue_list = "\n".join(f"{i + 1}. {title}" for i, (_, title) in enumerate(self.queue))
            await ctx.send(f"Cola de canciones:\n{queue_list}")

    @commands.command()
    async def splay(self, ctx, url):
        """Muestra el título de una canción específica de Spotify."""
        sp = spotipy.Spotify(auth=SPOTIFY_ACCESS_TOKEN)

        track_id = url.split("/")[-1].split("?")[0]  # Extraer el ID de la canción de la URL
        try:
            track_info = sp.track(track_id)
            track_title = track_info['name']
            await ctx.send(f'Canción: **{track_title}**')
            
            await self.sssplay(ctx, search=track_title)
        except Exception as e:
            await ctx.send(f"Ocurrió un error al obtener la canción: {e}")

    @commands.command()
    async def splaylist(self, ctx, url):
        """Muestra los títulos de las canciones en una lista de reproducción de Spotify."""
        sp = spotipy.Spotify(auth=SPOTIFY_ACCESS_TOKEN)

        playlist_id = url.split("/")[-1].split("?")[0]  # Extraer el ID de la lista de reproducción de la URL
        try:
            tracks = sp.playlist_tracks(playlist_id)
            song_titles = [item['track']['name'] for item in tracks['items']]  # Agregar el nombre de la canción a la lista
            
            await ctx.send("Canciones en la lista de reproducción:")
            await ctx.send("\n".join(song_titles))  # Enviar la lista de canciones al chat

            self.is_playing_playlist = True  # Se está reproduciendo una playlist

            # Reproducir canciones de la playlist
            for title in song_titles:
                if not self.is_playing_playlist:
                    break  # Detener si se ha detenido la playlist (flag es False)
                
                await self.sssplay(ctx, search=title)
                
        except Exception as e:
            await ctx.send(f"Ocurrió un error al obtener la lista de reproducción: {e}")
    @commands.command()
    async def yplaylist(self, ctx, url):
        try:
            ydl_opts = {
                'format': 'bestaudio',
                'quiet': True,
                'extract_flat': True  # Para solo obtener los títulos y URLs sin descargarlos
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

        # Verifica si hay 'entries' en el objeto de la lista
            if 'entries' not in info:
                await ctx.send("No se pudo obtener la lista de reproducción o la URL no es válida.")
                return
        
        # Lista de canciones extraídas de la playlist, pero solo toma las primeras 10
            song_titles = [entry['title'] for entry in info['entries'][:10]]  # Limitar a 10 canciones
            song_urls = [entry['url'] for entry in info['entries'][:10]]  # URLs de los videos

        # Reproducción de cada canción en el queue (solo las primeras 10)
            for index, (title, video_url) in enumerate(zip(song_titles, song_urls)):
                await self.play(ctx, search=video_url)  # Usa la función yplay para reproducirlo

        except Exception as e:
            await ctx.send(f"Ocurrió un error al obtener la lista de reproducción: {e}")
        


    

client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')

async def main():
    await client.add_cog(MusicBot(client))
    await client.start(DISCORD_TOKEN)  # Reemplaza con tu token de bot de Discord

asyncio.run(main())
