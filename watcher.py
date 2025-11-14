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

async def send_response(interaction: discord.Interaction, response_text: str):

    """
    Checks message length and sends it, splitting if necessary.
    """
    char_limit = 1950  # Safe limit under Discord's 2000


    if len(response_text) <= char_limit:
        # If deferred, use followup.send. Otherwise, use response.send_message
        if interaction.response.is_done():
            await interaction.followup.send(response_text)
        else:
            await interaction.response.send_message(response_text)
    else:
        # Answer is too long, we must split it!
        chunks = [response_text[i:i + char_limit] for i in range(0, len(response_text), char_limit)]
        # Send the first chunk as the initial reply
        if interaction.response.is_done():
            await interaction.followup.send(chunks[0])
        else:
            await interaction.response.send_message(chunks[0])

        # Send the rest of the chunks as separate messages
        for chunk in chunks[1:]:
            await interaction.channel.send(chunk)

# --- GLOBAL FUNCTION: HANDLE ERRORS ---
# We also use this for every command.
async def handle_error(interaction: discord.Interaction, error: Exception):
    """
    Handles common errors in a consistent way.
    """

    print(f"An error occurred: {error}")
    if "429" in str(error):
         error_message = "Ask me after a minute. That's my cooldown time"
    else:
        error_message = "I am sorry. My oath has been taken away 😔"

    if interaction.response.is_done():
        await interaction.followup.send(error_message)
    else:
        await interaction.response.send_message(error_message, ephemeral=True)

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
    embed.add_field(
        name="`/bio [character]`",
        value="Get a full biography of any Marvel character, from their origins to their key storylines.",
        inline=False
    )
    
    embed.add_field(
        name="`/whatif [scenario]`",
        value="Propose an alternate-reality scenario and I'll write a short narrative about what might happen.",
        inline=False
    )
    
    embed.add_field(
        name="`/teamup [char1] [char2]`",
        value="Curious how two characters would work together? I'll write a short scene about their first mission!",
        inline=False
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
        await handle_error(interaction, e)

@tree.command(name="fight", description="Pit two Marvel characters against each other!")
async def fight(interaction: discord.Interaction, character1: str, character2: str):
    
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
            await send _response(interaction, response.text)
                    
        else:
            await interaction.followup.send(f"I'm sorry, I couldn't seem to simulate a battle between {character1} and {character2}. Perhaps they are too evenly matched?")

    except Exception as e:
        await handle_error(interaction,e)

@tree.command(name="bio", description="Get a detailed biography of a Marvel character.")
async def bio(interaction: discord.Interaction, character: str):
    try:
        await interaction.response.defer(thinking=True)

        prompt = f"""
        You are the Watcher. A user wants a full biography of {character}.
        **Persona:** Expert, passionate, and encyclopedic.
        **Rules:**
        1. Provide a detailed biography of {character}.
        2. Include their Origin Story, a summary of their Powers/Abilities, and a brief mention of 1-2 of their most important story arcs.
        3. Base this ONLY on `marvel.com` and `marvel.fandom.com`.
        4. Give ONLY the biography.
        Begin!
        """
        
        response = model.generate_content(prompt)
        if response.text:
            await send_response(interaction, response.text)
        else:
            await interaction.followup.send(f"I'm sorry, I couldn't find a detailed biography for {character}.")

    except Exception as e:
        await handle_error(interaction, e)


@tree.command(name="whatif", description="Propose an alternate-reality 'What If' scenario.")
async def whatif(interaction: discord.Interaction, scenario: str):
    try:
        await interaction.response.defer(thinking=True)

        prompt = f"""
        You are the Watcher. A user is proposing a "What If" scenario.
        **Scenario:** "{scenario}"
        **Persona:** Creative, dramatic, and visionary.
        **Rules:**
        1. Write a short, vivid narrative exploring the logical consequences of this change in the timeline.
        2. Base your narrative on the lore and character traits from `marvel.com` and `marvel.fandom.com`.
        3. Give ONLY the narrative.
        Begin!
        """
        
        response = model.generate_content(prompt)
        if response.text:
            await send_response(interaction, response.text)
        else:
            await interaction.followup.send("I'm sorry, I couldn't seem to find a scenario for that.")

    except Exception as e:
        await handle_error(interaction, e)


@tree.command(name="teamup", description="See how two Marvel characters would work together.")
async def teamup(interaction: discord.Interaction, character1: str, character2: str):
    try:
        await interaction.response.defer(thinking=True)

        prompt = f"""
        You are the Watcher. A user wants to see a team-up between {character1} and {character2}.
        **Persona:** Creative, witty, and dramatic.
        **Rules:**
        1. Write a short, creative scene about their first mission or interaction.
        2. Explore how their personalities and powers would complement each other OR how they would clash.
        3. Base this on their known character traits from `marvel.com` and `marvel.fandom.com`.
        4. Give ONLY the scene.
        Begin!
        """
        
        response = model.generate_content(prompt)
        if response.text:
            await send_response(interaction, response.text)
        else:
            await interaction.followup.send(f"I'm sorry, I couldn't seem to find a team-up for {character1} and {character2}.")

    except Exception as e:
        await handle_error(interaction, e)

# --- RUN THE BOT ---
bot.run(DISCORD_TOKEN)