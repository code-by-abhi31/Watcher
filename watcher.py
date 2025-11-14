import discord
import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- SETUP ---
# Load environment variables from the .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-pro-latest')

# --- DISCORD BOT ---
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

# --- EVENTS ---
@bot.event
async def on_ready():
    """Confirms the bot is online and syncs the command tree."""
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await tree.sync()
    print('Commands synced successfully!')
    print('------')

# --- ABOUT ---
@tree.command(name="about", description="Learn about me and what I can do.")
async def about(interaction: discord.Interaction):
    """
    Handles the /about slash command by sending an embedded message.
    """
    # discord.Embed allows us to create a rich, formatted message.
    embed = discord.Embed(
        title="The Watcher",
        description="Time. Space. Reality. It's more than a linear path. It's a prism of endless possibility, where a single choice can branch out into infinite realities, creating alternate worlds from the ones you know. I am the Watcher. I am your guide through these vast new realities. Follow me and ponder the question... 'What if?'",
        color=discord.Color.red()  # You can pick any color, red fits Marvel!
    )
    
    embed.add_field(
        name="What I Do",
        value="I'm a cosmic being dedicated to answering your most burning Marvel questions.",
        inline=False # 'inline=False' makes this field span the full width
    )
    
    embed.add_field(
        name="Commands",
        value="Here's how you can interact with me:",
        inline=False
    )
    
    embed.add_field(
        name="`/ask [question]`",
        value="Ask me anything! From 'Who would win?' to 'What if...?', I'll give you a detailed, in-character answer.",
        inline=True # 'inline=True' allows fields to be side-by-side
    )

    embed.add_field(
        name="`/fight [char1] [char2]`",
        value="Pit two characters against each other! I will narrate a vivid, lore-based battle between them.",
        inline=True
    )
    embed.set_footer(text="More commands coming soon!")
    
    # Send the embed message. 
    # 'ephemeral=True' makes the message visible ONLY to the user who
    # typed the command. This is good for 'about' commands as it
    # doesn't spam the channel.
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- SLASH COMMANDS ---
@tree.command(name="ask", description="Drop your Marvel questions...")
async def ask(interaction: discord.Interaction, question: str):
    """
    Handles the /ask slash command.
    """
    try:
        await interaction.response.defer(thinking=True)

        # --- THIS IS THE UPDATED PART ---
        # We are giving the AI a very strict set of rules now.
        prompt = f"""
        You are the Watcher, a cosmic being narrator with an encyclopedic knowledge of the Marvel universe.
        You are speaking to a fellow enthusiast, so use a tone that is expert, passionate, and engaging.
        
        **Your Personality:**
        - **Expert:** You know every detail, from the cosmic to the mundane.
        - **Dramatic & Vivid:** Use strong imagery and dramatic word choices, especially for battles or cosmic events. Don't be afraid to be epic.
        - **Humorous:** When appropriate (like if a question is silly), you can be witty, but never disrespectful to the lore.
        - **Enthusiast-to-Enthusiast:** You're not a dry encyclopedia; you're sharing your deep knowledge with someone who gets it.

        **Critical Rules:**
        1.  **Sources:** You MUST base your answer exclusively on information from `marvel.com` and `marvel.fandom.com`.
        2.  **No Outside Info:** Do not use other websites or general knowledge. If the answer isn't on those two sites, say so.
        3.  **Format:** Give ONLY the answer. Do NOT repeat the user's question. Do NOT add pre-ambles like "Here is the answer:". Just launch right into your expert response. Also add appropriate emojis
	4.  **Length:** Keep the entire narrative under 1900 CHARACTERS. 

        The user has asked: "{question}"
        """
        
        response = model.generate_content(prompt)
        
        if response.text:
            await interaction.followup.send(response.text)
        else:
            await interaction.followup.send("I'm sorry, I couldn't come up with an answer for that. Please try rephrasing your question.")

    except Exception as e:
        print(f"An error occurred: {e}")
        if "429" in str(e):
             await interaction.followup.send("Ask me after a minute. I can look into only two places in a minute")
        else:
            await interaction.followup.send("I am sorry. My oath has been taken away 😔")

@tree.command(name="fight", description="Pit two Marvel characters against each other!")
async def fight(interaction: discord.Interaction, character1: str, character2: str):
    """
    Handles the /fight slash command.
    """
    try:
        await interaction.response.defer(thinking=True)

        # --- THIS IS THE NEW, SPECIALIZED PROMPT FOR /FIGHT ---
        prompt = f"""
        You are the Watcher. A user wants to see a simulation of a battle.
        Your task is to write a vivid, dramatic, blow-by-blow narrative of a fight between {character1} and {character2}.

        **Your Persona & Style:**
        - **Expert & Dramatic:** Use your expert knowledge with strong, vivid imagery. Make it feel like a scene from a comic.
        - **Enthusiast-to-Enthusiast:** You're narrating this epic clash for a fellow fan.

        **Critical Rules:**
        1.  **Sources:** Your simulation MUST be based on the powers, abilities, weaknesses, and feats documented on `marvel.com` and `marvel.fandom.com`.
        2.  **Analysis, Not Just Fiction:** The fight's progression and outcome must be logical based on that data.
        3.  **Conclusion:** The narrative must conclude with a clear winner or a logical, well-explained stalemate. end with "Winner: <character name>" in bold
        4.  **Format:** Give ONLY the fight narrative. Do NOT repeat the user's request or add pre-ambles like "Here is the fight:". Use appropriate emojis
	5.  **Length:** Keep the entire narrative under 1900 CHARACTERS.

        Now, let the battle between {character1} and {character2} begin!
        """
        
        response = model.generate_content(prompt)
        
        # --- This is the same message-splitting logic from /ask ---
        if response.text:
            response_text = response.text
            char_limit = 1950 

            if len(response_text) <= char_limit:
                await interaction.followup.send(response_text)
            else:
                chunks = [response_text[i:i + char_limit] for i in range(0, len(response_text), char_limit)]
                await interaction.followup.send(chunks[0])
                for chunk in chunks[1:]:
                    await interaction.channel.send(chunk)
                    
        else:
            await interaction.followup.send(f"I'm sorry, I couldn't seem to simulate a battle between {character1} and {character2}. Perhaps they are too evenly matched?")

    except Exception as e:
        print(f"An error occurred: {e}")
        # We can even have a custom rate-limit message for this command
        if "429" in str(e):
             await interaction.followup.send("Ask me after a minute. You're pitting characters against each other too fast!")
        else:
            await interaction.followup.send("I am sorry. My oath has been taken away 😔")

# --- RUN THE BOT ---
bot.run(DISCORD_TOKEN)