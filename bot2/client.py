import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import Settings
from bot2.gift_cards import search_items, get_cheapest_store

logger = logging.getLogger("bot2.compare")


class PriceCompareBot(commands.Bot):
    """Bot 2 — Interactive gift-card / game price comparator via /compare."""

    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix=None, intents=intents)
        self.settings = settings
        self._channel_id = settings.channel_id_2

    # ── lifecycle ──────────────────────────────────────────────

    async def on_ready(self) -> None:
        logger.info("Bot 2 online — %s (ID: %s)", self.user, self.user.id)
        try:
            synced = await self.tree.sync()
            logger.info("Synced %d slash command(s)", len(synced))
        except Exception as exc:
            logger.warning("Failed to sync command tree: %s", exc)

    # ── /compare ───────────────────────────────────────────────

    async def setup_hook(self) -> None:
        self.tree.add_command(compare_command, bot=self)

# ── slash command implementation ────────────────────────────────

@app_commands.command(
    name="compare",
    description="Compare gift card and game prices across stores",
)
@app_commands.describe(query="Gift card or game name to search for")
async def compare_command(
    interaction: discord.Interaction,
    query: str,
) -> None:
    results = search_items(query)

    if not results:
        embed = discord.Embed(
            title="🔍 No Results",
            description=f"No items found matching **{query}**.",
            color=0xE74C3C,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    top = results[0]
    cheapest = get_cheapest_store(top)
    type_emoji = "🎮" if top.get("_type") == "game" else "💳"

    embed = discord.Embed(
        title=f"{type_emoji} Price Comparison — {top['name']}",
        color=0x2ECC71,
    )

    if top.get("denomination"):
        unit = top.get("unit", "gift card")
        embed.description = (
            f"**Platform:** {top['platform']}  ·  "
            f"**Denomination:** {top['denomination']} {unit}"
        )

    lines = []
    for i, store in enumerate(sorted(top["stores"], key=lambda s: s["price"]), 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        lines.append(f"{medal} **${store['price']:.2f}** — [{store['name']}]({store['url']})")

    embed.add_field(
        name="Stores (sorted by price)",
        value="\n".join(lines),
        inline=False,
    )

    if cheapest:
        embed.set_footer(
            text=f"Best deal: {cheapest['name']} — ${cheapest['price']:.2f}"
        )

    # Build the button view
    view = BuyBestDealView(top)

    await interaction.response.send_message(embed=embed, view=view)

    if len(results) > 1:
        others = "\n".join(f"• {r['name']}" for r in results[1:6])
        await interaction.followup.send(
            f"**Also found ({len(results) - 1} more):**\n{others}",
            ephemeral=True,
        )


# ── interactive button ─────────────────────────────────────────

class BuyBestDealView(discord.ui.View):
    """View with a single button that reveals the cheapest store link."""

    def __init__(self, item: dict) -> None:
        super().__init__(timeout=180)
        self._item = item

    @discord.ui.button(
        label="Buy Best Deal",
        style=discord.ButtonStyle.success,
        emoji="🛒",
    )
    async def buy_best(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        cheapest = get_cheapest_store(self._item)
        if cheapest is None:
            await interaction.response.send_message(
                "No stores available for this item.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"🛒 Best Deal — {self._item['name']}",
            description=(
                f"**Store:** [{cheapest['name']}]({cheapest['url']})\n"
                f"**Price:** ${cheapest['price']:.2f}"
            ),
            color=0x2ECC71,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
