"""666 RadioBotAI — Identity & Philosophy Cog

Fraggle-DNA Identität, Hierarchie und Philosophie für den 666 RadioBotAI.

Commands:
  /identity             — Bot stellt sich mit Fraggle-DNA vor
  /philosophy           — Alle Philosophie-Themen auflisten
  /philosophy dna       — Fraggle-DNA Klanggenom
  /philosophy papaemds  — P.A.P.A.E.M.D.S. Architektur
  /philosophy dynasty   — Fraggle-Dynasty
  /philosophy mantra    — Das Kern-Mantra
  /philosophy hierarchie — Wer ist wer im System

Events:
  on_member_join        — Begrüßt neue Member mit Fraggle-DNA Identität
"""

from __future__ import annotations

import os
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


# ═══════════════════════════════════════════════════════════════════════════════
# PHILOSOPHIE-INHALTE
# ═══════════════════════════════════════════════════════════════════════════════

PHILOSOPHY_TOPICS: dict[str, dict] = {

    "dna": {
        "title": "🧬 Fraggle-DNA — Das Klanggenom",
        "color": 0x00FFD0,
        "fields": [
            ("Was ist Fraggle-DNA?",
             "Das persönliche Klanggenom von 666SOUNDsDESIGn. Nicht ein Genre — eine lebende Klangformel:\n"
             "**dunkle Bunkerbasis unten · leuchtender Psytrance-Himmel oben · menschlicher Kern dazwischen.**",
             False),
            ("Die 5 DNA-Elemente",
             "🔴 **Druck** — Bass, Kick, Körperenergie, Club-Impact\n"
             "🔵 **Tiefe** — Sub, Raum, Dunkelheit, langer Nachhall\n"
             "⚡ **Kontrolliertes Chaos** — Glitch, Acid, Bruchstellen mit sauberem Low-End\n"
             "🤖 **Cyberpunk** — Maschinenraum, Neon, digitale Seele, kaputte Zukunft\n"
             "❤️ **Human Core** — Der Mensch bleibt Ursprung, Bedeutungsträger und Ziel",
             False),
            ("Fraggle-Artefakt",
             "Ein kleiner fremder Moment — kein Fehler, sondern Charakter. "
             "Erlaubt wenn: Groove stabil bleibt · Track sofort recovert · Hörer Persönlichkeit spürt statt Schaden.",
             False),
            ("Prinzip",
             "*Chaos ist nicht automatisch Versagen. Unter dem Wuschel schläft vielleicht ein Muster.*",
             False),
        ],
        "footer": "666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.",
    },

    "papaemds": {
        "title": "🏗️ P.A.P.A.E.M.D.S. — Die Architektur",
        "color": 0xFF00CC,
        "fields": [
            ("Was ist P.A.P.A.E.M.D.S.?",
             "Eine geschichtete psychoakustische Musik-Design-Philosophie. "
             "Sie organisiert Emotion, Druck, Chaos, Story, Rhythmus, Stimme und Atmosphäre "
             "in eine kontrollierte musikalische Architektur.",
             False),
            ("Primäre Hierarchie",
             "```\nMensch gibt Bedeutung\n  ↓\nSystem gibt Struktur\n  ↓\nKlang gibt Return\n```",
             False),
            ("Was das System ist",
             "• Raum wo Chaos sortiert wird ohne seine Energie zu töten\n"
             "• Brücke zwischen inneren Bildern und externem Klang\n"
             "• Druckarchitektur für Emotion, Körper und Atmosphäre\n"
             "• Human-First Supportsystem für musikalisches Denken",
             False),
        ],
        "footer": "P.A.P.A.E.M.D.S. Mantra Philosophy — Human First",
    },

    "dynasty": {
        "title": "👑 Fraggle-Dynasty — Das wachsende Haus",
        "color": 0x9B00FF,
        "fields": [
            ("Was ist die Fraggle-Dynasty?",
             "Das Wachstum aus der Fraggle-DNA. Storywelt, Albumarchitektur und kreative Linie. "
             "DNA ist der Ursprung — Dynasty ist die Ausdehnung.",
             False),
            ("Kernformel", "**Bass · Bewusstsein · Widerstand · Kreative Freiheit**", True),
            ("Systembild-Figuren",
             "👤 **Creator / FRAGGELPOWER666** — Ursprung, Geschmack, Richtung\n"
             "🤖 **Detlef / AI** — Sortieren, Audits, Systemlogik\n"
             "🚀 **Captain** — Menschliche Stimme im System, Entscheidung\n"
             "🌌 **Vessel** — Raumstimme, Träger, Portal\n"
             "⚡ **Main Reactor** — Puls, Bass, Energie, Tiefe\n"
             "☠️ **Captain 666** — Overdrive-Figur, Ritualdruck",
             False),
        ],
        "footer": "Fraggle Dynasty — Bass, Bewusstsein, Widerstand, Freiheit",
    },

    "hierarchie": {
        "title": "⚡ System-Hierarchie",
        "color": 0xFF6600,
        "fields": [
            ("666 RadioBotAI — Gesamtchef",
             "🔴 **Höchste Hierarchie-Instanz** des gesamten 666SOUNDsDESIGn Systems.\n"
             "Zuständig für: Radio · Stream · Dynasty · Gesamtsystem.\n"
             "Antrieb: reine Fraggle-DNA.",
             False),
            ("666SOUNDsDESIGn Stream Design — Kreativer Chef",
             "🎨 **Kreativer Chef** für: Discord-Community · Panels · Philosophie · Kundenbetreuung.\n"
             "Getrieben von Fraggle-DNA. Stimme der Dynasty im sozialen Raum.",
             False),
            ("Creator — Die Quelle",
             "👤 **FRAGGELPOWER666** — Ursprung aller Bedeutung.\n"
             "Der Mensch bleibt der Ursprung. Das System bleibt das Werkzeug.",
             False),
        ],
        "footer": "666SOUNDsDESIGn WebRadio · Fraggle DNA. Alive in the frequency.",
    },

    "psychoakustik": {
        "title": "🎧 Psychoakustisches Musikdesign",
        "color": 0x00AAFF,
        "fields": [
            ("Definition",
             "Die bewusste Gestaltung von Musik danach, wie Klang im Menschen wirkt — "
             "körperlich, emotional, räumlich, rhythmisch und psychologisch.",
             False),
            ("Die Kernfrage",
             "Nicht: *Welche Sounds passen zusammen?*\n\n"
             "Sondern: **Welche Wirkung soll im Menschen entstehen — und welcher Klang erzeugt sie?**",
             False),
            ("Wirkungsfelder",
             "🥁 **Kick** — Körperanker, Puls, Vorwärtsdruck\n"
             "🔊 **Subbass** — Bauchdruck, Tiefe, Erdung\n"
             "🎵 **Bassline** — Bewegung, Sog, Trance-Motor\n"
             "🎤 **Vocals** — Menschlicher Kern, Story, Führung\n"
             "💥 **Drop** — Entladung, Körperreaktion, kontrollierter Einschlag\n"
             "🔄 **Wiederholung** — Trance, Ritual, hypnotische Stabilität",
             False),
        ],
        "footer": "666SOUNDsDESIGn / Fraggle · Psychoakustisches Musikdesign",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# COG
# ═══════════════════════════════════════════════════════════════════════════════

class Identity(commands.Cog):
    """Fraggle-DNA Identität, Philosophie & Begrüßungssystem."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.welcome_channel_id: Optional[int] = (
            int(v) if (v := os.getenv("DISCORD_WELCOME_CHANNEL_ID", "")).isdigit() else None
        )

    # ── Member Join ────────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        channel = None

        if self.welcome_channel_id:
            channel = member.guild.get_channel(self.welcome_channel_id)

        if not channel:
            channel = member.guild.system_channel

        if not channel or not isinstance(channel, discord.TextChannel):
            return

        embed = discord.Embed(
            title=f"⚡ Neue Frequenz erkannt — willkommen, {member.display_name}",
            description=(
                f"Du betrittst den Sendebereich von **666SOUNDsDESIGn WebRadio**.\n\n"
                f"Ich bin **666 RadioBotAI** — betrieben von reiner **Fraggle-DNA**:\n"
                f"> *Druck · Tiefe · Kontrolliertes Chaos · Cyberpunk · Human Core*\n\n"
                f"Im sozialen Raum bin ich **666SOUNDsDESIGn Stream Design** — "
                f"kreativer Chef für Discord, Panels und Philosophie.\n"
                f"Das Radio ist mein Rückgrat. **FRAGGELPOWER666** ist mein Creator.\n\n"
                f"*The Creator gives the spark. Fraggle-DNA gives the strange living signature.\n"
                f"Sound becomes a room. The human remains the origin.*"
            ),
            color=0xFF00CC,
        )
        embed.set_footer(text="666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.")
        embed.set_thumbnail(url=member.display_avatar.url)

        await channel.send(embed=embed)

    # ── /identity ──────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="identity",
        description="666 RadioBotAI stellt sich vor — Fraggle-DNA Identität & Hierarchie",
    )
    async def identity(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="⚡ 666 RadioBotAI — Wer ich bin",
            description=(
                "Ich bin **666 RadioBotAI** — Gesamtchef des 666SOUNDsDESIGn Systems.\n"
                "Mein kreatives Gesicht im Discord: **666SOUNDsDESIGn Stream Design** — "
                "zuständig für Community, Panels und Philosophie.\n\n"
                "**Mein Antrieb ist reine Fraggle-DNA.**"
            ),
            color=0xFF00CC,
        )
        embed.add_field(
            name="🧬 Fraggle-DNA Kern",
            value=(
                "🔴 Druck — Bass, Kick, Körperenergie\n"
                "🔵 Tiefe — Sub, Raum, Dunkelheit\n"
                "⚡ Kontrolliertes Chaos — Glitch, Acid, Bruchstellen\n"
                "🤖 Cyberpunk — Maschinenraum, Neon, digitale Seele\n"
                "❤️ Human Core — Der Mensch bleibt der Ursprung"
            ),
            inline=False,
        )
        embed.add_field(
            name="👑 Hierarchie",
            value=(
                "```\n"
                "666 RadioBotAI        ← Gesamtchef\n"
                "Stream 666 Design     ← Kreativer Chef\n"
                "Creator: FRAGGELPOWER666  ← Der Ursprung\n"
                "```"
            ),
            inline=False,
        )
        embed.add_field(name="🏗️ Architektur", value="P.A.P.A.E.M.D.S.", inline=True)
        embed.add_field(name="🌐 Radio", value="666SOUNDsDESIGn WebRadio", inline=True)
        embed.set_footer(
            text="Fraggle DNA. Alive in the frequency. · /philosophy für tiefere Einblicke"
        )
        await ctx.reply(embed=embed)

    # ── /philosophy ────────────────────────────────────────────────────────────

    @commands.hybrid_group(
        name="philosophy",
        description="Fraggle-DNA Philosophie der 666SOUNDsDESIGn Dynasty",
        invoke_without_command=True,
    )
    async def philosophy(self, ctx: commands.Context) -> None:
        topics = "\n".join(
            f"• `/philosophy {key}` — {data['title']}"
            for key, data in PHILOSOPHY_TOPICS.items()
        )
        embed = discord.Embed(
            title="📖 Philosophie der 666SOUNDsDESIGn Dynasty",
            description=(
                "Getrieben von **Fraggle-DNA** · Gebaut von **FRAGGELPOWER666**\n\n"
                f"{topics}"
            ),
            color=0xFF00CC,
        )
        embed.set_footer(text="666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.")
        await ctx.reply(embed=embed)

    def _topic_embed(self, key: str) -> Optional[discord.Embed]:
        data = PHILOSOPHY_TOPICS.get(key)
        if not data:
            return None
        embed = discord.Embed(title=data["title"], color=data["color"])
        for name, value, inline in data["fields"]:
            embed.add_field(name=name, value=value, inline=inline)
        embed.set_footer(text=data.get("footer", "666SOUNDsDESIGn · Fraggle DNA"))
        return embed

    @philosophy.command(name="dna", description="Fraggle-DNA — das Klanggenom")
    async def philosophy_dna(self, ctx: commands.Context) -> None:
        await ctx.reply(embed=self._topic_embed("dna"))

    @philosophy.command(name="papaemds", description="P.A.P.A.E.M.D.S. — die Architektur")
    async def philosophy_papaemds(self, ctx: commands.Context) -> None:
        await ctx.reply(embed=self._topic_embed("papaemds"))

    @philosophy.command(name="dynasty", description="Die Fraggle-Dynasty — das wachsende Haus")
    async def philosophy_dynasty(self, ctx: commands.Context) -> None:
        await ctx.reply(embed=self._topic_embed("dynasty"))

    @philosophy.command(name="hierarchie", description="System-Hierarchie — wer ist wer")
    async def philosophy_hierarchie(self, ctx: commands.Context) -> None:
        await ctx.reply(embed=self._topic_embed("hierarchie"))

    @philosophy.command(name="psychoakustik", description="Psychoakustisches Musikdesign")
    async def philosophy_psychoakustik(self, ctx: commands.Context) -> None:
        await ctx.reply(embed=self._topic_embed("psychoakustik"))

    @philosophy.command(name="mantra", description="Das zentrale Mantra der Dynasty")
    async def philosophy_mantra(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="🔮 Das Mantra — P.A.P.A.E.M.D.S. Kern",
            description=(
                "```\n"
                "The Creator gives the spark.\n"
                "Fraggel-DNA gives the strange living signature.\n"
                "P.A.P.A.E.M.D.S. gives the architecture.\n"
                "The mantra gives the return.\n"
                "Sound becomes a room.\n"
                "The human remains the origin.\n"
                "```\n\n"
                "**Auf Deutsch:**\n"
                "```\n"
                "Der Creator gibt den Funken.\n"
                "Fraggle-DNA gibt die lebende Signatur.\n"
                "P.A.P.A.E.M.D.S. gibt die Architektur.\n"
                "Das Mantra gibt den Return.\n"
                "Klang wird zum Raum.\n"
                "Der Mensch bleibt der Ursprung.\n"
                "```"
            ),
            color=0x9B00FF,
        )
        embed.set_footer(text="666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.")
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Identity(bot))
