import json
import os

import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
import sqlite3
from api import ApiJoin
from shop import MarketAPI
from ship import TaxAPI, UpgradeAPI, TheftAPI
TOKEN_DISCORD = "NOP"
TOKEN_API ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjb2RpbmdnYW1lIiwic3ViIjoiMGEyNzcwODItYjZlNi00Y2E3LWJlMTItZGE4OGU1N2Q4NmI4Iiwicm9sZXMiOlsiVVNFUiJdfQ.9lmC6AZsJktL3F92Zm2dj8SEdAGfzeWk08g13hB4qRE"
DB_NAME = "world.db"

api = ApiJoin(TOKEN_API)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SALON_ALERTE_ID = 1485017705294860408

offres_deja_signalees = set()
market_api = MarketAPI(TOKEN_API)
tax_api = TaxAPI(TOKEN_API)
upgrade_api = UpgradeAPI(TOKEN_API)
theft_api = TheftAPI(TOKEN_API)

def get_db_data():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM player WHERE id = 1")
    player = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) as total FROM tiles")
    tiles = cursor.fetchone()['total']
    conn.close()
    return player, tiles
class GameMenu(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📊 Stats Temps Réel", style=discord.ButtonStyle.primary, emoji="📍")
    async def info_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        player, total_tiles = get_db_data()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT island_name) FROM tiles WHERE island_name IS NOT NULL")
        total_islands = cursor.fetchone()[0]
        conn.close()
        embed = discord.Embed(
            title="🛰️ Radar de Navigation - Direct",
            description="Données synchronisées avec le navire.",
            color=discord.Color.blue()
        )
        embed.add_field(name="📍 Position Actuelle", value=f"**X:** {player['x']} | **Y:** {player['y']}", inline=True)
        embed.add_field(name="⚡ Énergie", value=f"**{player['energy']}** unités", inline=True)
        embed.add_field(name="🗺️ Secteurs Explorés", value=f"{total_tiles} tuiles", inline=True)
        embed.add_field(name="🏝️ Archipels Connus", value=f"{total_islands} îles", inline=True)
        import datetime
        embed.set_footer(text=f"Dernière mise à jour : {datetime.datetime.now().strftime('%H:%M:%S')}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📦 Ressources", style=discord.ButtonStyle.secondary, emoji="🪵")
    async def resources_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        try:
            ressources_actuelles = api.resources()
            details = api.connect_get("/players/details")
            storage_max = details["storage"]["maxResources"]

            embed = discord.Embed(
                title="📦 État de la Cale & Trésorerie",
                color=discord.Color.gold()  # Couleur dorée pour le prestige
            )
            liste_res = [
                ("🔥 Charbonium", "CHARBONIUM"),
                ("⛓️ Feronium", "FERONIUM"),
                ("🪵 Boisium", "BOISIUM")
            ]

            for label, key in liste_res:
                actuel = ressources_actuelles.get(key, 0)
                maximum = storage_max.get(key, 1)

                percent = (actuel / maximum) * 100
                filled = int(percent / 10)
                bar = "🟩" * min(filled, 10) + "⬜" * max(0, (10 - filled))
                alerte = " ⚠️ **PLEIN !**" if actuel >= maximum - 1000 else ""

                embed.add_field(
                    name=label,
                    value=f"**{actuel:,}** / {maximum:,}{alerte}\n{bar} ({percent:.1f}%)",
                    inline=False
                )
            # On utilise un nouveau champ dédié pour l'or
            fortune = details.get('money', 0)
            embed.add_field(
                name="💰 Pièces d'Or",
                value=f"**{fortune:,} G**",  # Utilisation de Markdown h2 pour un affichage plus gros
                inline=False
            )

            embed.timestamp = discord.utils.utcnow()
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Erreur ressources: {e}")
            await interaction.followup.send(f"❌ Erreur de synchronisation avec la cale : {e}", ephemeral=True)

    @discord.ui.button(label="🛒 Shop Global", style=discord.ButtonStyle.secondary, emoji="💰")
    async def shop_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ShopControlView(market_api)
        await interaction.response.send_message("Bienvenue au comptoir commercial :", view=view, ephemeral=True)

    @discord.ui.button(label="💸 Taxes", style=discord.ButtonStyle.danger, emoji="⚖️")
    async def tax_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        taxes = tax_api.get_due_taxes()

        if not taxes:
            return await interaction.followup.send("☀️ Vous n'avez aucune taxe à payer pour le moment !",
                                                   ephemeral=True)

        view = TaxView(taxes, tax_api)
        embed = discord.Embed(title="⚖️ Service des Impôts",
                              description="Régularisez vos taxes avant la fin du temps imparti !",
                              color=discord.Color.red())

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="⚙️ Upgrades", style=discord.ButtonStyle.success, emoji="🏗️")
    async def upgrade_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = UpgradeView(upgrade_api)
        embed = discord.Embed(
            title="🛠️ Centre d'Amélioration",
            description="Choisissez ce que vous souhaitez améliorer (Navire ou Entrepôt).",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🏴‍☠️ Vols", style=discord.ButtonStyle.secondary, emoji="💀")
    async def theft_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TheftMenuView(theft_api)
        await interaction.response.send_message("⚓ **Pont de Piraterie** : Que voulez-vous faire ?", view=view,
                                                ephemeral=True)
class ShopView(discord.ui.View):
    def __init__(self, offers, market_api):
        super().__init__(timeout=60)
        self.offers = offers
        self.market_api = market_api  # On le stocke
        self.add_item(ShopSelect(offers, market_api))



class ShopSelect(discord.ui.Select):
    def __init__(self, offers, market_api):
        self.market_api = market_api  # On stocke l'API ici aussi
        options = []

        for o in offers[:25]:
            # Assure-toi d'utiliser les bonnes clés (resourceType, quantityIn)
            res_type = o.get('resourceType', 'Inconnu')
            qty = o.get('quantityIn', 0)
            price = o.get('pricePerResource', 0)
            offer_id = o.get('id', '???')

            options.append(discord.SelectOption(
                label=f"Acheter {qty} {res_type}",
                value=str(offer_id),
                description=f"Prix unit: {price}G",
                emoji="💰"
            ))

        super().__init__(placeholder="Choisissez une offre...", options=options)

    async def callback(self, interaction: discord.Interaction):
        offer_id = self.values[0]
        view = ConfirmBuyView(offer_id, self.market_api)
        await interaction.response.send_message(f"🛒 Offre #{offer_id} choisie.", view=view, ephemeral=True)


class QuantityModal(discord.ui.Modal, title="Confirmer l'Achat"):
    quantity_input = discord.ui.TextInput(
        label="Combien voulez-vous en acheter ?",
        placeholder="Entrez un nombre (ex: 5)...",
        min_length=1,
        max_length=10,
    )

    def __init__(self, offer_id, market_api):
        super().__init__()
        self.offer_id = offer_id
        self.market_api = market_api

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qty = int(self.quantity_input.value)
            if qty <= 0:
                raise ValueError()
        except ValueError:
            return await interaction.response.send_message("❌ Erreur : Veuillez entrer un nombre entier positif.",
                                                           ephemeral=True)
        result = self.market_api.buy(self.offer_id, qty)

        if result:
            await interaction.response.send_message(
                f"✅ Achat de **{qty}** unités de l'offre **#{self.offer_id}** réussi !", ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Échec de l'achat. Vérifiez vos fonds ou la disponibilité de l'offre.", ephemeral=True)

class ConfirmBuyView(discord.ui.View):
    def __init__(self, offer_id, market_api):
        super().__init__(timeout=30)
        self.offer_id = offer_id
        self.market_api = market_api # On le stocke pour le Modal

    @discord.ui.button(label="Choisir la Quantité", style=discord.ButtonStyle.success, emoji="🛒")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(QuantityModal(self.offer_id, self.market_api))


class ShopControlView(discord.ui.View):
    def __init__(self, market_api):
        super().__init__(timeout=None)
        self.market_api = market_api

    @discord.ui.select(
        placeholder="Que voulez-vous faire sur le marché ?",
        options=[
            discord.SelectOption(label="Acheter", description="Voir les offres du marché (Live JSON)", emoji="🛒",
                                 value="buy"),
            discord.SelectOption(label="Vendre", description="Mettre mes ressources en vente", emoji="💰", value="sell"),
            discord.SelectOption(label="Mes Offres", description="Gérer mes ventes en cours (Mod/Del)", emoji="📜",
                                 value="my_offers"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        action = select.values[0]

        if action == "buy":
            if not os.path.exists("market_data.json"):
                return await interaction.response.send_message(
                    "❌ Fichier `market_data.json` introuvable. Lance le broker !", ephemeral=True)

            try:
                with open("market_data.json", "r", encoding="utf-8") as f:
                    market_data = json.load(f)
            except Exception as e:
                return await interaction.response.send_message(f"❌ Erreur lecture JSON : {e}", ephemeral=True)

            if not market_data:
                return await interaction.response.send_message("📭 Le marché est actuellement vide.", ephemeral=True)
            # On trie pour avoir les offres les moins chères en premier
            offres_triees = sorted(market_data.items(), key=lambda x: x[1].get('price', 999999))

            embed = discord.Embed(
                title="🛒 Marché Global (Direct Broker)",
                description="Voici les meilleures affaires actuelles. Sélectionnez une offre ci-dessous pour l'acheter.",
                color=discord.Color.gold()
            )

            offers_for_select = []
            for offer_id, info in offres_triees[:25]:
                res = info.get('res', 'Inconnu')
                qty = info.get('qty', 0)
                price = info.get('price', 0)
                owner = info.get('owner', 'Anonyme')
                # existant (ShopSelect) que ça vient de l'API !
                offers_for_select.append({
                    'id': offer_id,
                    'resourceType': res,
                    'quantityIn': qty,
                    'pricePerResource': price
                })
                if len(offers_for_select) <= 10:
                    embed.add_field(
                        name=f"📦 {res} (par {owner})",
                        value=f"🔢 Qté: **{qty:,}**\n💰 Prix: **{price} G/u**",
                        inline=True
                    )
            # On passe notre fausse liste API au menu déroulant
            view = ShopView(offers_for_select, self.market_api)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        elif action == "sell":
            await interaction.response.send_modal(SellModal(self.market_api))

        elif action == "my_offers":
            my_offers = self.market_api.get_my_offers()
            if not my_offers:
                return await interaction.response.send_message("Vous n'avez aucune offre active.", ephemeral=True)
            view = MyOffersView(my_offers, self.market_api)
            await interaction.response.send_message("📜 Vos offres en cours :", view=view, ephemeral=True)

class SellModal(discord.ui.Modal, title="Mettre en vente"):
    res_type = discord.ui.TextInput(label="Ressource", placeholder="FERONIUM, BOISIUM ou CHARBONIUM")
    qty = discord.ui.TextInput(label="Quantité", placeholder="Ex: 10")
    price = discord.ui.TextInput(label="Prix Unitaire", placeholder="Ex: 5")

    def __init__(self, market_api):
        super().__init__()
        self.market_api = market_api

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            res = self.market_api.sell(
                self.res_type.value.upper(),
                int(self.qty.value),
                int(self.price.value)
            )

            if res:
                embed = discord.Embed(
                    title="💰 Offre publiée !",
                    description=f"Votre annonce pour **{self.qty.value} {self.res_type.value}** est en ligne.",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send("❌ Le serveur a refusé la création de l'offre (Vérifiez votre stock).",
                                                ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"⚠️ Erreur imprévue : {e}", ephemeral=True)


class MyOffersView(discord.ui.View):
    def __init__(self, my_offers, market_api):
        super().__init__()
        self.add_item(MyOfferSelect(my_offers, market_api))


class MyOfferSelect(discord.ui.Select):
    def __init__(self, my_offers, market_api):
        self.market_api = market_api
        self.my_offers = my_offers
        options = [
            discord.SelectOption(
                label=f"Offre {o['id'][:8]}... - {o['resourceType']}",
                description=f"Qte: {o['quantityIn']} | Prix: {o['pricePerResource']}G",
                value=str(o['id'])  # On garde l'ID complet ici
            ) for o in my_offers
        ]
        super().__init__(placeholder="Sélectionnez une de vos offres...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # On retire le int(), on garde la valeur telle quelle (string)
        offer_id = self.values[0]
        # Attention : on compare des strings maintenant
        offer_data = next((o for o in self.my_offers if str(o['id']) == offer_id), None)

        if not offer_data:
            return await interaction.response.send_message("❌ Offre introuvable.", ephemeral=True)

        res_type = offer_data['resourceType']
        view = EditDeleteView(offer_id, res_type, self.market_api)
        await interaction.response.send_message(f"⚙️ Gestion de l'offre **#{offer_id[:8]}...** ({res_type}) :",
                                                view=view, ephemeral=True)

class EditDeleteView(discord.ui.View):
    def __init__(self, offer_id, res_type, market_api):
        super().__init__()
        self.offer_id = offer_id
        self.res_type = res_type
        self.market_api = market_api

    @discord.ui.button(label="Modifier", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditOfferModal(self.offer_id, self.res_type, self.market_api))

    @discord.ui.button(label="Supprimer", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = self.market_api.delete_offer(self.offer_id)
        if success:
            await interaction.response.edit_message(content=f"🗑️ Offre #{self.offer_id} supprimée.", view=None)
        else:
            await interaction.response.send_message("❌ Échec de la suppression.", ephemeral=True)

class EditOfferModal(discord.ui.Modal, title="Modifier mon offre"):
    qty = discord.ui.TextInput(label="Nouvelle Quantité total", placeholder="Ex: 50")
    price = discord.ui.TextInput(label="Nouveau Prix Unitaire", placeholder="Ex: 10")

    def __init__(self, offer_id, res_type, market_api):
        super().__init__()
        self.offer_id = offer_id
        self.res_type = res_type  # L'API a besoin du type pour le PATCH
        self.market_api = market_api

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            res = self.market_api.update_offer(
                self.offer_id,
                self.res_type,
                int(self.qty.value),
                int(self.price.value)
            )

            if res:
                embed = discord.Embed(
                    title="✏️ Offre mise à jour",
                    description=f"L'offre **#{self.offer_id}** a été modifiée avec succès.",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send("❌ Échec de la modification. Vérifiez vos stocks.", ephemeral=True)
        except ValueError:
            await interaction.followup.send("❌ Veuillez entrer des nombres valides.", ephemeral=True)


class TaxView(discord.ui.View):
    def __init__(self, taxes, tax_api):
        super().__init__(timeout=60)
        self.add_item(TaxSelect(taxes, tax_api))


class TaxSelect(discord.ui.Select):
    def __init__(self, taxes, tax_api):
        self.tax_api = tax_api
        options = []
        for t in taxes:
            label = f"Payer {t['amount']}G ({t['type']})"
            desc = f"Temps restant: {t['remainingTime']} min"
            options.append(discord.SelectOption(label=label, value=str(t['id']), description=desc, emoji="💸"))

        super().__init__(placeholder="Sélectionnez une taxe à régulariser...", options=options)

    async def callback(self, interaction: discord.Interaction):
        tax_id = self.values[0]
        success = self.tax_api.pay_tax(tax_id)

        if success:
            await interaction.response.send_message(f"✅ Taxe réglée avec succès !", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Erreur lors du paiement. Vérifiez votre solde d'or.",
                                                    ephemeral=True)


class UpgradeView(discord.ui.View):
    def __init__(self, upgrade_api):
        super().__init__(timeout=60)
        self.upgrade_api = upgrade_api

    @discord.ui.button(label="📦 Upgrade Storage", style=discord.ButtonStyle.primary, emoji="🏗️")
    async def storage_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        info = self.upgrade_api.get_storage_next_level()
        if not info:
            return await interaction.response.send_message("Niveau max atteint ou erreur.", ephemeral=True)

        embed = discord.Embed(title=f"Amélioration Entrepôt : {info['name']}", color=discord.Color.blue())
        max_res = info['maxResources']
        embed.add_field(name="Nouveaux Max",
                        value=f"🪵 Bois: {max_res['BOISIUM']}\n⛓️ Fer: {max_res['FERONIUM']}\n🔥 Charbon: {max_res['CHARBONIUM']}",
                        inline=False)
        costs = info['costResources']
        embed.add_field(name="Coût de l'amélioration",
                        value=f"🪵 {costs['BOISIUM']} | ⛓️ {costs['FERONIUM']} | 🔥 {costs['CHARBONIUM']}",
                        inline=False)

        await interaction.response.send_message(embed=embed, view=ConfirmUpgradeView("storage", self.upgrade_api),
                                                ephemeral=True)

    @discord.ui.button(label="🚢 Upgrade Ship", style=discord.ButtonStyle.success, emoji="⚓")
    async def ship_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        info = self.upgrade_api.get_ship_next_level()
        if not info:
            return await interaction.response.send_message("Navire déjà au niveau maximum !", ephemeral=True)

        embed = discord.Embed(title=f"Amélioration Navire : {info['name']}", color=discord.Color.green())
        embed.add_field(name="Bonus",
                        value=f"👀 Vision: {info['visibilityRange']}\n⚡ Mouvements: {info['maxMovement']}\n🚀 Vitesse: {info['speed']}",
                        inline=False)

        costs = info['costResources']
        embed.add_field(name="Coût de l'amélioration",
                        value=f"🪵 {costs['BOISIUM']} | ⛓️ {costs['FERONIUM']} | 🔥 {costs['CHARBONIUM']}",
                        inline=False)

        await interaction.response.send_message(embed=embed, view=ConfirmUpgradeView("ship", self.upgrade_api),
                                                ephemeral=True)


class ConfirmUpgradeView(discord.ui.View):
    def __init__(self, target, upgrade_api):
        super().__init__()
        self.target = target
        self.upgrade_api = upgrade_api

    @discord.ui.button(label="Confirmer l'amélioration", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.target == "storage":
            res = self.upgrade_api.upgrade_storage()
        else:
            res = self.upgrade_api.upgrade_ship()

        if res.status_code == 200:
            await interaction.response.send_message("✅ Amélioration terminée ! Votre empire s'agrandit.",
                                                    ephemeral=True)
        else:
            error_msg = res.json().get('message', 'Ressources insuffisantes')
            await interaction.response.send_message(f"❌ Erreur : {error_msg}", ephemeral=True)


class TheftModal(discord.ui.Modal, title="💰 Préparer un Vol"):
    res_type = discord.ui.TextInput(label="Ressource cible", placeholder="CHARBONIUM, FERONIUM, BOISIUM")
    amount = discord.ui.TextInput(label="Mise en OR", placeholder="Combien d'or investissez-vous ?")

    def __init__(self, theft_api):
        super().__init__()
        self.theft_api = theft_api

    async def on_submit(self, interaction: discord.Interaction):
        res_val = self.res_type.value.upper()
        amt_val = self.amount.value
        embed = discord.Embed(
            title="⚠️ Confirmation de l'Assaut",
            description=f"Capitaine, êtes-vous sûr de vouloir investir **{amt_val} G** pour tenter de piller du **{res_val}** ?",
            color=discord.Color.orange()
        )
        embed.set_footer(text="L'or investi ne sera pas remboursé en cas d'échec !")
        view = ConfirmTheftView(self.theft_api, res_val, amt_val)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
class ConfirmTheftView(discord.ui.View):
    def __init__(self, theft_api, res_type, amount):
        super().__init__(timeout=30)
        self.theft_api = theft_api
        self.res_type = res_type
        self.amount = amount

    @discord.ui.button(label="Confirmer l'Assaut", style=discord.ButtonStyle.danger, emoji="🏴‍☠️")
    async def confirm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        for child in self.children:
            child.disabled = True
        await interaction.edit_original_response(view=self)

        try:
            res = self.theft_api.launch_theft(self.res_type, int(self.amount))

            if res:
                embed = discord.Embed(title="✅ Vol Lancé avec succès !", color=discord.Color.dark_red())
                embed.add_field(name="🆔 ID de l'opération", value=f"`{res.get('id', 'N/A')[:8]}`", inline=False)
                chance = float(res.get('chance', 0)) * 100
                embed.add_field(name="🎲 Chances de réussite", value=f"**{chance:.1f}%**", inline=True)
                embed.add_field(name="⏱️ Résultat attendu à", value=f"`{res.get('resolveAt', 'Bientôt')}`", inline=True)

                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send("❌ Échec de l'opération. Vérifiez que vous avez assez d'or.",
                                                ephemeral=True)

        except ValueError:
            await interaction.followup.send("❌ Erreur : Le montant investi doit être un nombre.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Erreur système : {e}", ephemeral=True)

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="🛑 Assaut annulé",
            description="Le vol a été annulé. Votre or est en sécurité.",
            color=discord.Color.light_grey()
        )
        await interaction.response.edit_message(embed=embed, view=self)


class TheftMenuView(discord.ui.View):
    def __init__(self, theft_api):
        super().__init__(timeout=60)
        self.theft_api = theft_api

    @discord.ui.button(label="Lancer un Vol", style=discord.ButtonStyle.danger, emoji="🗡️")
    async def start_theft(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TheftModal(self.theft_api))

    @discord.ui.button(label="Historique des Vols", style=discord.ButtonStyle.secondary, emoji="📜")
    async def history_theft(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        history = self.theft_api.get_theft_history()

        if not history:
            return await interaction.followup.send("Aucun vol dans les registres.", ephemeral=True)

        embed = discord.Embed(title="📜 Registre de Piraterie", color=discord.Color.light_grey())
        for v in history[-5:]:
            # On convertit 'chance' en float pour éviter l'erreur de formatage
            try:
                chance_val = float(v.get('chance', 0)) * 100
                chance_str = f"{chance_val:.0f}%"
            except (ValueError, TypeError):
                chance_str = "Inconnue"

            status_emoji = "✅" if v.get('status') == 'SUCCESS' else "❌" if v.get('status') == 'FAILED' else "⏳"

            embed.add_field(
                name=f"Vol #{str(v['id'])[:8]}",
                value=f"Type: **{v.get('resourceType', '?')}**\nStatut: {status_emoji} `{v.get('status', 'N/A')}`\nChance: {chance_str}",
                inline=True
            )

        await interaction.followup.send(embed=embed, ephemeral=True)


@tasks.loop(seconds=3.0)  # Le bot vérifie le fichier toutes les 3 secondes
async def sniper_marche():
    global offres_deja_signalees
    if not os.path.exists("market_data.json"):
        return
    try:
        with open("market_data.json", "r", encoding="utf-8") as f:
            market_data = json.load(f)
    except Exception:
        return  # Si le fichier est en cours d'écriture par le broker, on passe notre tour
    channel = bot.get_channel(SALON_ALERTE_ID)
    if not channel:
        return  # Salon introuvable
    for offer_id, info in market_data.items():
        res = info.get("res", "")
        price = float(info.get("price", 9999))
        qty = info.get("qty", 0)
        owner = info.get("owner", "Anonyme")
        if res in ["FERONIUM", "BOISIUM"] and price < 3:
            if offer_id not in offres_deja_signalees:
                embed = discord.Embed(
                    title="🚨 DING DING DING ! AFFAIRE EN OR !",
                    description=f"Foncez acheter cette offre avant les autres !",
                    color=discord.Color.red()
                )
                embed.add_field(name="📦 Ressource", value=f"**{res}**", inline=True)
                embed.add_field(name="💰 Prix Unitaire", value=f"**{price} G**", inline=True)
                embed.add_field(name="🔢 Quantité", value=f"{qty} unités", inline=True)
                embed.add_field(name="👤 Vendeur", value=owner, inline=True)
                embed.add_field(name="🆔 ID de l'offre", value=f"`{offer_id}`", inline=False)
                await channel.send(content="@here 🎯 **CIBLE DÉTECTÉE !**", embed=embed)
                offres_deja_signalees.add(offer_id)
@bot.command()
async def menu(ctx):
    """Affiche le menu principal avec les boutons."""
    embed = discord.Embed(
        title="🚢 Tableau de Bord du Navire",
        description="Bienvenue capitaine ! Gérez votre flotte via les boutons ci-dessous.",
        color=discord.Color.dark_grey()
    )
    await ctx.send(embed=embed, view=GameMenu())

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    if not sniper_marche.is_running():
        sniper_marche.start()
        print("🎯 Sniper du marché ACTIVÉ !")


bot.run(TOKEN_DISCORD)