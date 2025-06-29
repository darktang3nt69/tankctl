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
BASE_URL = os.getenv("API_BASE_URL",)


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

# FEED

class FeedDropdown(discord.ui.Select):
    def __init__(self, tanks):
        options = []
        for tank in tanks:
            if tank.get("is_online", False):
                options.append(discord.SelectOption(
                    label=f"{tank.get('tank_name', 'Unknown')} ({tank.get('location', 'Unknown')})",
                    value=tank.get("tank_id", ""),
                    emoji="🟢"
                ))
        if not options:
            options = [discord.SelectOption(label="No online tanks", value="none", emoji="🔴")]
        super().__init__(placeholder="Select a tank to feed...", options=options[:25])
        self.tanks = tanks
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("❌ No online tanks available", ephemeral=True)
            return
        
        tank_id = self.values[0]
        tank = next((t for t in self.tanks if t.get("tank_id") == tank_id), None)
        
        if not tank:
            await interaction.response.send_message("❌ Tank not found", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        success = await api_client.send_command(tank_id, "feed")
        
        if success:
            embed = discord.Embed(
                title="🍽️ Feed Command Sent",
                description=f"Successfully fed **{tank.get('tank_name')}** in **{tank.get('location')}**",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("❌ Failed to send feed command", ephemeral=True)

class FeedView(discord.ui.View):
    def __init__(self, tanks):
        super().__init__(timeout=300)
        self.add_item(FeedDropdown(tanks))

@tank_group.command(name="feed", description="Feed fish in a selected tank")
async def tank_feed(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        tanks = await api_client.get_tanks()
        if not tanks:
            await interaction.followup.send("❌ No tanks available", ephemeral=True)
            return
        
        online_tanks = [t for t in tanks if t.get("is_online", False)]
        if not online_tanks:
            await interaction.followup.send("❌ No online tanks available", ephemeral=True)
            return
        
        embed = discord.Embed(title="🍽️ Feed Fish", description="Select a tank to feed:", color=discord.Color.blue())
        view = FeedView(tanks)
        await interaction.followup.send(embed=embed, view=view)
    except Exception as e:
        logger.error(f"Error in tank feed: {e}")
        await interaction.followup.send("❌ Error preparing feed command", ephemeral=True)

# LIGHT

class LightButtons(discord.ui.View):
    def __init__(self, tank_id, tank_name, location):
        super().__init__(timeout=300)
        self.tank_id = tank_id
        self.tank_name = tank_name
        self.location = location
    
    @discord.ui.button(label="Turn ON", style=discord.ButtonStyle.green, emoji="💡")
    async def light_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        success = await api_client.send_command(self.tank_id, "light_on")
        if success:
            embed = discord.Embed(
                title="🟢 Light ON",
                description=f"✅ Light turned **ON** for **{self.tank_name}** in **{self.location}**",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("❌ Failed to turn light ON", ephemeral=True)
    
    @discord.ui.button(label="Turn OFF", style=discord.ButtonStyle.red, emoji="🌙")
    async def light_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        success = await api_client.send_command(self.tank_id, "light_off")
        if success:
            embed = discord.Embed(
                title="🔴 Light OFF",
                description=f"✅ Light turned **OFF** for **{self.tank_name}** in **{self.location}**",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("❌ Failed to turn light OFF", ephemeral=True)

class LightDropdown(discord.ui.Select):
    def __init__(self, tanks):
        options = []
        for tank in tanks:
            if tank.get("is_online", False):
                options.append(discord.SelectOption(
                    label=f"{tank.get('tank_name', 'Unknown')} ({tank.get('location', 'Unknown')})",
                    value=tank.get("tank_id", ""),
                    emoji="🟢"
                ))
        if not options:
            options = [discord.SelectOption(label="No online tanks", value="none", emoji="🔴")]
        super().__init__(placeholder="Select a tank to control lights...", options=options[:25])
        self.tanks = tanks
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("❌ No online tanks available", ephemeral=True)
            return
        
        tank_id = self.values[0]
        tank = next((t for t in self.tanks if t.get("tank_id") == tank_id), None)
        
        if not tank:
            await interaction.response.send_message("❌ Tank not found", ephemeral=True)
            return
        
        tank_name = tank.get("tank_name", "Unknown")
        location = tank.get("location", "Unknown")
        light_status = tank.get("light_status")
        light_status_text = "💡 Light is ON" if light_status else "🌙 Light is OFF" if light_status is not None else "❓ Light status unknown"

        embed = discord.Embed(
            title="💡 Light Control",
            description=f"Control lights for **{tank_name}**\n**Location:** {location}\n**Current:** {light_status_text}",
            color=discord.Color.blue()
        )
        view = LightButtons(tank_id, tank_name, location)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class LightView(discord.ui.View):
    def __init__(self, tanks):
        super().__init__(timeout=300)
        self.add_item(LightDropdown(tanks))

@tank_group.command(name="light", description="Control lights in a selected tank")
async def tank_light(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        tanks = await api_client.get_tanks()
        if not tanks:
            await interaction.followup.send("❌ No tanks available", ephemeral=True)
            return
        
        online_tanks = [t for t in tanks if t.get("is_online", False)]
        if not online_tanks:
            await interaction.followup.send("❌ No online tanks available", ephemeral=True)
            return
        
        embed = discord.Embed(title="💡 Light Control", description="Select a tank to control lights:", color=discord.Color.blue())
        view = LightView(tanks)
        await interaction.followup.send(embed=embed, view=view)
    except Exception as e:
        logger.error(f"Error in tank light: {e}")
        await interaction.followup.send("❌ Error preparing light control", ephemeral=True)

# Entry
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
