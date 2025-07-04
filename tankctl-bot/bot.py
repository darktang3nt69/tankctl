#!/usr/bin/env python3
"""
tankctl-bot v2: Discord bot for managing fish tanks with /tank group commands
"""

import asyncio
import logging
import os
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger("tankctl-bot")

# API Config
BASE_URL = os.getenv("API_BASE_URL")

class TankAPI:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
    
    async def get_tanks(self):
        try:
            response = await self.client.get("/tanks")
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "tanks" in data:
                return data["tanks"]
            elif isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error(f"Error fetching tanks: {e}")
            return []
    
    async def send_command(self, tank_id: str, command_type: str):
        try:
            payload = {
                "tank_id": tank_id,
                "command_type": command_type,
                "parameters": {}
            }
            response = await self.client.post("/commands", json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False

api_client = TankAPI()

class TankBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.guild_id = os.getenv('DISCORD_GUILD_ID')
        if self.guild_id:
            self.guild_id = int(self.guild_id)
    
    async def setup_hook(self):
        logger.info("Setting up tankctl-bot...")
        try:
            if self.guild_id:
                guild = discord.Object(id=self.guild_id)
                self.tree.clear_commands(guild=guild)
                logger.info("Cleared guild commands")
            else:
                self.tree.clear_commands()
                logger.info("Cleared global commands")
        except Exception as e:
            logger.error(f"Error clearing commands: {e}")
        
        self.tree.add_command(tank_group, guild=discord.Object(id=self.guild_id) if self.guild_id else None)

        try:
            if self.guild_id:
                guild = discord.Object(id=self.guild_id)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} commands to guild {self.guild_id}")
            else:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} commands globally")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        logger.info(f"Bot is ready! Logged in as {self.user}")
        activity = discord.Activity(type=discord.ActivityType.watching, name="fish tanks 🐠")
        await self.change_presence(activity=activity)

bot = TankBot()

# ---- /tank group ----
tank_group = app_commands.Group(name="tank", description="Manage your fish tanks")

@tank_group.command(name="status", description="Check the status of all fish tanks")
async def tank_status(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        tanks = await api_client.get_tanks()
        if not tanks:
            embed = discord.Embed(title="🐠 Tank Status", description="No tanks found or API unavailable.", color=discord.Color.orange())
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🐠 Tank Status Dashboard",
            description=f"Found {len(tanks)} tank(s)",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        online_count = 0
        for tank in tanks:
            name = tank.get("tank_name", "Unknown")
            location = tank.get("location", "Unknown")
            is_online = tank.get("is_online", False)
            light_status = tank.get("light_status")
            last_seen = tank.get("last_seen", "Never")

            light_text = "Light is ON 💡" if light_status else "Light is OFF 🌙" if light_status is not None else "Light status unknown ❓"
            
            if is_online:
                online_count += 1
            
            try:
                dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                last_seen_formatted = f"<t:{int(dt.timestamp())}:R>"
            except:
                last_seen_formatted = "Unknown"
            
            status_emoji = "🟢" if is_online else "🔴"
            status_text = "Online" if is_online else "Offline"
            
            embed.add_field(
                name=f"{status_emoji} {name}",
                value=f"**Location:** {location}\n**Status:** {status_text}\n**Last Seen:** {last_seen_formatted}\n**Light:** {light_text}",
                inline=True
            )
        
        embed.add_field(
            name="📊 Summary",
            value=f"**Online:** {online_count}/{len(tanks)}\n**Offline:** {len(tanks) - online_count}/{len(tanks)}",
            inline=False
        )
        embed.set_footer(text="Use /tank feed or /tank light to control tanks")
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Error in tank status: {e}")
        await interaction.followup.send("❌ Error fetching tank status", ephemeral=True)

# ---- Feed command (multi-select + ALL + confirm) ----

class FeedDropdown(discord.ui.Select):
    def __init__(self, tanks, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label="ALL TANKS", value="ALL", emoji="🪄")
        ]
        for tank in tanks:
            if tank.get("is_online", False):
                options.append(discord.SelectOption(
                    label=f"{tank['tank_name']} ({tank['location']})",
                    value=tank['tank_id'],
                    emoji="🟢"
                ))
        if len(options) == 1:
            options = [discord.SelectOption(label="No online tanks", value="none", emoji="🔴")]

        super().__init__(
            placeholder="Select tank(s) to feed...",
            min_values=1, max_values=len(options),
            options=options
        )
        self.tanks = tanks

    async def callback(self, interaction: discord.Interaction):
        if "none" in self.values:
            await interaction.response.send_message("❌ No online tanks available", ephemeral=True)
            return

        if "ALL" in self.values:
            self.parent_view.selected_tanks = self.tanks
            await interaction.response.send_message(
                "⚠️ Please confirm feeding **ALL tanks** below.",
                view=ConfirmFeedView(self.tanks),
                ephemeral=True
            )
        else:
            self.parent_view.selected_tanks = [
                t for t in self.tanks if t['tank_id'] in self.values
            ]
            await self.parent_view.execute(interaction)

class FeedView(discord.ui.View):
    def __init__(self, tanks):
        super().__init__(timeout=300)
        self.selected_tanks = []
        self.add_item(FeedDropdown(tanks, self))

    async def execute(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        success_msgs = []
        for tank in self.selected_tanks:
            ok = await api_client.send_command(tank['tank_id'], "feed")
            if ok:
                success_msgs.append(f"🍽️ Fed **{tank['tank_name']}** in **{tank['location']}**")

        title = "✅ Feed Command Sent" if success_msgs else "❌ Feed Failed"
        embed = discord.Embed(
            title=title,
            description="\n".join(success_msgs) or "No commands succeeded.",
            color=discord.Color.green() if success_msgs else discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

class ConfirmFeedView(discord.ui.View):
    def __init__(self, tanks):
        super().__init__(timeout=60)
        self.tanks = tanks

    @discord.ui.button(label="✅ Confirm Feed ALL", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        success_msgs = []
        for tank in self.tanks:
            ok = await api_client.send_command(tank['tank_id'], "feed")
            if ok:
                success_msgs.append(f"🍽️ Fed **{tank['tank_name']}** in **{tank['location']}**")

        title = "✅ Feed Command Sent (ALL)" if success_msgs else "❌ Feed Failed"
        embed = discord.Embed(
            title=title,
            description="\n".join(success_msgs) or "No commands succeeded.",
            color=discord.Color.green() if success_msgs else discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cancelled feeding all tanks.", ephemeral=True)

@tank_group.command(name="feed", description="Feed fish in selected tank(s)")
async def tank_feed(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        tanks = await api_client.get_tanks()
        online = [t for t in tanks if t.get("is_online", False)]
        if not online:
            await interaction.followup.send("❌ No online tanks available", ephemeral=True)
            return

        embed = discord.Embed(title="🍽️ Feed Fish", description="Select tank(s) to feed:", color=discord.Color.blue())
        view = FeedView(online)
        await interaction.followup.send(embed=embed, view=view)
    except Exception as e:
        logger.error(f"Error in tank feed: {e}")
        await interaction.followup.send("❌ Error preparing feed command", ephemeral=True)

# ---- Light command (multi-select + ALL + confirm) ----

class LightDropdown(discord.ui.Select):
    def __init__(self, tanks, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label="ALL TANKS", value="ALL", emoji="🪄")
        ]
        for tank in tanks:
            if tank.get("is_online", False):
                options.append(discord.SelectOption(
                    label=f"{tank['tank_name']} ({tank['location']})",
                    value=tank['tank_id'],
                    emoji="🟢"
                ))
        if len(options) == 1:
            options = [discord.SelectOption(label="No online tanks", value="none", emoji="🔴")]

        super().__init__(
            placeholder="Select tank(s) to control lights...",
            min_values=1, max_values=len(options),
            options=options
        )
        self.tanks = tanks

    async def callback(self, interaction: discord.Interaction):
        if "none" in self.values:
            await interaction.response.send_message("❌ No online tanks available", ephemeral=True)
            return

        if "ALL" in self.values:
            await interaction.response.send_message(
                "⚠️ Please confirm light control for **ALL tanks** below.",
                view=ConfirmLightView(self.tanks),
                ephemeral=True
            )
        else:
            parent = self.parent_view
            parent.selected_tanks = [t for t in self.tanks if t['tank_id'] in self.values]
            await parent.show_controls(interaction)

class LightView(discord.ui.View):
    def __init__(self, tanks):
        super().__init__(timeout=300)
        self.selected_tanks = []
        self.add_item(LightDropdown(tanks, self))

    async def show_controls(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="💡 Light Control",
            description=f"Control lights for **{len(self.selected_tanks)}** selected tank(s)",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, view=LightButtons(self.selected_tanks), ephemeral=True)

class LightButtons(discord.ui.View):
    def __init__(self, tanks):
        super().__init__(timeout=300)
        self.tanks = tanks

    @discord.ui.button(label="Turn ON", style=discord.ButtonStyle.green, emoji="💡")
    async def light_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        msgs = []
        for tank in self.tanks:
            ok = await api_client.send_command(tank['tank_id'], "light_on")
            if ok:
                msgs.append(f"🟢 Light turned **ON** for **{tank['tank_name']}** in **{tank['location']}**")
        title = "🟢 Light ON" if msgs else "❌ Light ON Failed"
        embed = discord.Embed(title=title, description="\n".join(msgs) or "No lights were turned on.", color=discord.Color.green() if msgs else discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Turn OFF", style=discord.ButtonStyle.red, emoji="🌙")
    async def light_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        msgs = []
        for tank in self.tanks:
            ok = await api_client.send_command(tank['tank_id'], "light_off")
            if ok:
                msgs.append(f"🔴 Light turned **OFF** for **{tank['tank_name']}** in **{tank['location']}**")
        title = "🔴 Light OFF" if msgs else "❌ Light OFF Failed"
        embed = discord.Embed(title=title, description="\n".join(msgs) or "No lights were turned off.", color=discord.Color.red() if msgs else discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=True)

class ConfirmLightView(discord.ui.View):
    def __init__(self, tanks):
        super().__init__(timeout=60)
        self.tanks = tanks

    @discord.ui.button(label="✅ Confirm Light Control (ALL)", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="💡 Light Control for ALL Tanks",
                description="Choose ON or OFF below.",
                color=discord.Color.gold()
            ),
            view=LightButtons(self.tanks),
            ephemeral=True
        )

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cancelled light control for all tanks.", ephemeral=True)

@tank_group.command(name="light", description="Control lights in selected tank(s)")
async def tank_light(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        tanks = await api_client.get_tanks()
        online = [t for t in tanks if t.get("is_online", False)]
        if not online:
            await interaction.followup.send("❌ No online tanks available", ephemeral=True)
            return

        embed = discord.Embed(title="💡 Light Control", description="Select tank(s) to control lights:", color=discord.Color.blue())
        view = LightView(online)
        await interaction.followup.send(embed=embed, view=view)
    except Exception as e:
        logger.error(f"Error in tank light: {e}")
        await interaction.followup.send("❌ Error preparing light control", ephemeral=True)

# ---- Bot entrypoint ----

async def main():
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found")
        return
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        await bot.close()
        await api_client.client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
