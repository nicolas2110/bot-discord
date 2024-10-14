
import discord
from discord.ext import commands
import yt_dlp
import asyncio
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
FFMPEG_OPTIONS = {'options': '-vn'}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []

    @commands.command()
    async def play(self, ctx, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("No estás en un canal de voz.")

        if not ctx.voice_client:
            await ctx.send(f"Conectando a {voice_channel.name}...")
            await voice_channel.connect()
            await ctx.send(f"Conectado a {voice_channel.name}")
        else:
            if ctx.voice_client.channel != voice_channel:
                return await ctx.send("El bot ya está en otro canal de voz.")

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

    async def play_next(self, ctx):
        if self.queue:
            url, title = self.queue.pop(0)
            source = await discord.FFmpegPCMAudio.from_probe(url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))
            await ctx.send(f'Ahora reproduciendo: **{title}**')
        else:
            await ctx.send("La cola está vacía.")

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Canción saltada.")
        else:
            await ctx.send("No hay nada que saltar.")

    @commands.command()
    async def queue(self, ctx):
        if not self.queue:
            await ctx.send("La cola está vacía.")
        else:
            queue_list = "\n".join(f"{i + 1}. {title}" for i, (_, title) in enumerate(self.queue))
            await ctx.send(f"Cola de canciones:\n{queue_list}")

client = commands.Bot(command_prefix="!", intents=intents)

async def main():
    await client.add_cog(MusicBot(client))
    await client.start('MTI5NTI1NzczNDU2Mzc2MjMyOA.Gaf21_.iO7IMjexhOR8_bblNneaOnHomo4GG-VcBZCwRw')

asyncio.run(main())
