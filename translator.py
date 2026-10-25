"""Pure logic for the Dementia Translator. No Streamlit import here,
so this file can be tested with plain python.

This is a communication aid only. It does not diagnose, it does not
read minds, and it does not replace a nurse or doctor. A sudden change,
new pain, fever, or distress should be checked with the care team promptly.
Never enter resident names, photos, or health records into the app.
"""

import re

# ---------------------------------------------------------------- patterns
# Each pattern: what a resident says or does, what it often means,
# what to try first, what to say, and what to avoid saying.
PATTERNS = [
    {
        "id": "go-home",
        "category": "Wanting to leave",
        "says": "I want to go home",
        "examples": "I want to go home. / Take me home. / I need to leave.",
        "likely_means": [
            "I feel unsafe, tired, bored, or overstimulated right now.",
            "I am looking for a familiar place or feeling, not necessarily a literal address.",
            "I may need the bathroom, food, rest, or reassurance.",
        ],
        "try": [
            "Check the basics first: bathroom, hunger, thirst, pain, tiredness.",
            "Lower noise and light, offer a quiet seat and a familiar object or blanket.",
            "Walk with them for a bit instead of blocking the door, if it is safe to do so.",
        ],
        "say": ["You are safe here with me. Let's sit together for a bit.", "Tell me about home. What did you love most there?"],
        "avoid": ["This IS your home now.", "You can't leave.", "Stop saying that."],
    },
    {
        "id": "looking-for-mom",
        "category": "Looking for family",
        "says": "Where is my mom? / Where is my dad?",
        "examples": "Where's my mother? / I want my mom. / Where did my dad go?",
        "likely_means": [
            "I am looking for comfort and a person who made me feel safe.",
            "I may be scared, lonely, or in need of reassurance.",
        ],
        "try": [
            "Stay close and calm. Offer a hand to hold if they welcome it.",
            "Look at a photo together or talk about a happy memory, if that helps.",
            "Redirect gently to a comforting activity after you have listened.",
        ],
        "say": ["Your mom loved you very much. I'm here with you now.", "Tell me about her. What was she like?"],
        "avoid": ["Your mom died years ago.", "You are 80 years old, your mom is gone.", "Stop asking."],
    },
    {
        "id": "repetitive-questions",
        "category": "Repeating",
        "says": "Asking the same question over and over",
        "examples": "What time is it? / When are we going? / When is my family coming?",
        "likely_means": [
            "I cannot hold the answer in my memory, so I keep checking.",
            "I may be anxious about what happens next.",
        ],
        "try": [
            "Answer the same way each time, calmly, without showing frustration.",
            "Write the answer in large print where they can see it.",
            "Give a simple next step: first this, then that.",
        ],
        "say": ["Lunch is at noon. First we will sit here, then we will go eat.", "Your family will visit soon. Let's wait together."],
        "avoid": ["I just told you.", "You already asked that ten times.", "Can't you remember?"],
    },
    {
        "id": "refusing-care",
        "category": "Refusing care",
        "says": "Refusing a shower, clothes change, or medicine",
        "examples": "No! / Leave me alone. / I already did that.",
        "likely_means": [
            "I feel scared, cold, embarrassed, rushed, or out of control.",
            "I may be in pain, or I may not understand what is happening.",
        ],
        "try": [
            "Pause, step back, and try again later with a different approach.",
            "Offer a choice of two: this shirt or that shirt, now or in 10 minutes.",
            "Break it into one small step and join the task, rather than doing it to them.",
        ],
        "say": ["No rush. We can do just one part together.", "Would you like this one or this one?"],
        "avoid": ["You have to.", "Don't be difficult.", "We already talked about this."],
    },
    {
        "id": "pacing-night",
        "category": "Restless / night",
        "says": "Pacing, restless, or awake at night",
        "examples": "Walking the halls at night. / Can't settle. / Trying doors.",
        "likely_means": [
            "I may need the bathroom, I may be in pain, hungry, or anxious.",
            "I may be confused about day and night, or looking for something familiar.",
        ],
        "try": [
            "Check bathroom, pain, hunger, and whether they are too hot or cold.",
            "Offer a calm, dim-lit activity: a snack, warm blanket, folding towels, music.",
            "Walk with them safely, then guide them back to a restful place.",
        ],
        "say": ["It's nighttime, time to rest. Let's get comfortable.", "Walk with me for a bit, then we will rest."],
        "avoid": ["Go back to bed!", "It's 2am, stop walking.", "You are keeping everyone awake."],
    },
    {
        "id": "not-eating",
        "category": "Food and drink",
        "says": "Pushing food away or saying they are not hungry",
        "examples": "I don't want that. / I'm not hungry. / Turning away from food.",
        "likely_means": [
            "I may have mouth pain, swallowing trouble, nausea, or I simply do not recognise the food.",
            "I may be distracted, tired, or need help starting.",
        ],
        "try": [
            "Offer small, familiar finger foods and a drink, not a full plate at once.",
            "Sit and eat with them, or hand them one item to hold.",
            "If eating changes suddenly, or swallowing looks unsafe, tell the nurse promptly.",
        ],
        "say": ["Just try one bite with me.", "Here is some water first."],
        "avoid": ["You have to eat it all.", "You haven't eaten anything today, eat!"],
    },
    {
        "id": "calling-out",
        "category": "Calling out / yelling",
        "says": "Calling out, yelling, or shouting the same word",
        "examples": "Help! / Hello? / Calling a name repeatedly.",
        "likely_means": [
            "I may be in pain, scared, lonely, or trying to get attention and not finding the words.",
            "I may need the bathroom or feel uncomfortable and cannot explain it.",
        ],
        "try": [
            "Go to them, get at eye level, and speak calmly. Do not shout back from the hall.",
            "Check pain, bathroom, position, hunger, and thirst.",
            "Stay a few minutes. Sometimes presence alone settles it.",
        ],
        "say": ["I'm here. I hear you. What do you need?", "I'm staying with you."],
        "avoid": ["Be quiet!", "Stop yelling.", "Nobody is hurting you."],
    },
    {
        "id": "accusing",
        "category": "Accusations / hiding things",
        "says": "Accusing others of stealing, or hiding things",
        "examples": "You stole my purse! / Someone took my things. / Hiding items in drawers.",
        "likely_means": [
            "I cannot find something I value, and I am trying to explain the loss.",
            "I may be scared about losing control of my belongings.",
        ],
        "try": [
            "Help search together, without arguing about who took it.",
            "Keep important items in a consistent, visible place.",
            "Offer a safe place they control, like a bag or drawer of their own.",
        ],
        "say": ["Let's look together. We will find it.", "Your things are safe here."],
        "avoid": ["Nobody stole anything.", "You hid it yourself.", "You are imagining things."],
    },
    {
        "id": "wanting-to-work",
        "category": "Wanting a role",
        "says": "I need to go to work / take care of the kids / catch the bus",
        "examples": "I have to go to work. / I need to pick up the kids. / I missed my bus.",
        "likely_means": [
            "I am returning to a time when I had a clear role and purpose.",
            "I may feel useless, bored, or anxious about responsibilities.",
        ],
        "try": [
            "Give a safe, useful task: folding, sorting, wiping a table, holding a clipboard.",
            "Validate the role, then bridge to now: first this job, then a rest.",
            "Avoid long explanations about retirement or the year.",
        ],
        "say": ["You worked hard. Can you help me with this job first?", "The kids are safe. Let's finish this together."],
        "avoid": ["You retired 20 years ago.", "Your kids are grown.", "There is no bus."],
    },
    {
        "id": "pain-signals",
        "category": "Possible pain",
        "says": "Grimacing, guarding, rubbing a spot, or sudden mood change",
        "examples": "Wincing when moving. / Holding an arm, leg, or belly. / Suddenly much more agitated.",
        "likely_means": [
            "Pain is a very common reason for a sudden change in behaviour.",
            "They may not be able to say where it hurts or what it feels like.",
        ],
        "try": [
            "Check gently: ask where it hurts, watch what movement hurts, check for injury or swelling.",
            "Tell the nurse promptly, especially if the change is sudden or new.",
            "Keep them comfortable and do not force movement that hurts.",
        ],
        "say": ["Show me where it hurts.", "I'm going to get help so we can make it feel better."],
        "avoid": ["You are fine.", "There's nothing wrong with you.", "Just sit still."],
        "red_flag": True,
    },
    {
        "id": "withdrawn",
        "category": "Withdrawn / crying",
        "says": "Quiet, withdrawn, crying, or staring",
        "examples": "Sitting alone for a long time. / Crying without clear words. / Not answering.",
        "likely_means": [
            "I may be sad, tired, overwhelmed, or overstimulated.",
            "I may not have the words for what I feel.",
        ],
        "try": [
            "Sit nearby quietly. Offer touch or music only if they welcome it.",
            "Offer a simple sensory comfort: warm blanket, familiar song, hand to hold.",
            "Give time. Do not rush a conversation.",
        ],
        "say": ["I'm here with you. No rush.", "Would you like some music, or just quiet?"],
        "avoid": ["Why are you crying?", "Cheer up.", "What's wrong with you?"],
    },
    {
        "id": "bathroom-shame",
        "category": "Bathroom",
        "says": "Refusing help in the bathroom, or upset after an accident",
        "examples": "No, I can do it myself. / Distress after incontinence. / Trying to hide it.",
        "likely_means": [
            "I feel embarrassed and want privacy and dignity.",
            "I may be confused about where the bathroom is or what I need.",
        ],
        "try": [
            "Keep it private, calm, and quick. Cover up as you go.",
            "Guide with short steps and a clear bathroom sign or light at night.",
            "Reassure them, clean up without fuss, and move on.",
        ],
        "say": ["No problem at all. Let's get you comfortable.", "I'll help, just this part."],
        "avoid": ["You had an accident again.", "You should have told me.", "This is a mess."],
    },
]

CATEGORIES = sorted(set(p["category"] for p in PATTERNS))


def search_patterns(query, category="All"):
    """Return patterns matching a free-text query and optional category."""
    q = (query or "").strip().lower()
    out = []
    for p in PATTERNS:
        if category and category != "All" and p["category"] != category:
            continue
        if not q:
            out.append(p)
            continue
        hay = " ".join([p["says"], p["examples"], p["category"]] + p["likely_means"]).lower()
        if all(word in hay for word in q.split()):
            out.append(p)
    return out


# ------------------------------------------------------- English <-> Spanish
# Caregiver phrases use the respectful usted form, which is the safer
# default for an older adult you do not know well. Pronunciation is a
# rough read-aloud guide, not formal phonetics.
SPANISH_PHRASES = [
    {"category": "Comfort and safety", "en": "Hello, I am here to help you.", "es": "Hola, estoy aquí para ayudarle.", "say": "OH-lah, es-TOY ah-KEE PAH-rah ah-yoo-DAR-leh"},
    {"category": "Comfort and safety", "en": "You are safe.", "es": "Está a salvo.", "say": "es-TAH ah SAHL-voh"},
    {"category": "Comfort and safety", "en": "Do not worry.", "es": "No se preocupe.", "say": "noh seh preh-oh-KOO-peh"},
    {"category": "Comfort and safety", "en": "I am going to stay with you.", "es": "Me voy a quedar con usted.", "say": "meh voy ah keh-DAR kohn oos-TEHD"},
    {"category": "Comfort and safety", "en": "Everything is okay.", "es": "Todo está bien.", "say": "TOH-doh es-TAH bee-EN"},
    {"category": "Comfort and safety", "en": "Let's sit together.", "es": "Vamos a sentarnos juntos.", "say": "VAH-mohs ah sen-TAR-nohs HOON-tohs"},
    {"category": "Comfort and safety", "en": "Please wait here.", "es": "Por favor, espere aquí.", "say": "por fah-VOR, es-PEH-reh ah-KEE"},
    {"category": "Comfort and safety", "en": "Hold my hand.", "es": "Tome mi mano.", "say": "TOH-meh mee MAH-noh"},
    {"category": "Comfort and safety", "en": "Let's go slowly.", "es": "Vamos despacio.", "say": "VAH-mohs des-PAH-see-oh"},
    {"category": "Needs", "en": "Are you hungry?", "es": "¿Tiene hambre?", "say": "tee-EH-neh AHM-breh"},
    {"category": "Needs", "en": "Are you thirsty?", "es": "¿Tiene sed?", "say": "tee-EH-neh sehd"},
    {"category": "Needs", "en": "Would you like some water?", "es": "¿Quiere un poco de agua?", "say": "kee-EH-reh oon POH-koh deh AH-gwah"},
    {"category": "Needs", "en": "Do you need the bathroom?", "es": "¿Necesita ir al baño?", "say": "neh-seh-SEE-tah eer ahl BAH-nyoh"},
    {"category": "Needs", "en": "Are you tired?", "es": "¿Está cansado?", "say": "es-TAH kahn-SAH-doh"},
    {"category": "Needs", "en": "Are you sleepy?", "es": "¿Tiene sueño?", "say": "tee-EH-neh SWEH-nyoh"},
    {"category": "Needs", "en": "Are you cold?", "es": "¿Tiene frío?", "say": "tee-EH-neh FREE-oh"},
    {"category": "Needs", "en": "Are you hot?", "es": "¿Tiene calor?", "say": "tee-EH-neh kah-LOR"},
    {"category": "Pain", "en": "Are you in pain?", "es": "¿Le duele algo?", "say": "leh DWAY-leh AHL-goh"},
    {"category": "Pain", "en": "Where does it hurt?", "es": "¿Dónde le duele?", "say": "DOHN-deh leh DWAY-leh"},
    {"category": "Pain", "en": "Show me where it hurts.", "es": "Muéstreme dónde le duele.", "say": "MWES-treh-meh DOHN-deh leh DWAY-leh"},
    {"category": "Pain", "en": "I am going to get help.", "es": "Voy a buscar ayuda.", "say": "voy ah boos-KAR ah-YOO-dah"},
    {"category": "Routine", "en": "It is time to eat.", "es": "Es hora de comer.", "say": "ehs OH-rah deh koh-MER"},
    {"category": "Routine", "en": "It is time for your medicine.", "es": "Es hora de su medicina.", "say": "ehs OH-rah deh soo meh-dee-SEE-nah"},
    {"category": "Routine", "en": "Let's get dressed.", "es": "Vamos a vestirnos.", "say": "VAH-mohs ah ves-TEER-nohs"},
    {"category": "Routine", "en": "It is time for a shower.", "es": "Es hora de bañarse.", "say": "ehs OH-rah deh bah-NYAR-seh"},
    {"category": "Routine", "en": "It is time for bed.", "es": "Es hora de dormir.", "say": "ehs OH-rah deh dor-MEER"},
    {"category": "Routine", "en": "Let's go for a walk.", "es": "Vamos a caminar.", "say": "VAH-mohs ah kah-mee-NAR"},
    {"category": "Routine", "en": "Would you like to listen to music?", "es": "¿Quiere escuchar música?", "say": "kee-EH-reh es-koo-CHAR MOO-see-kah"},
    {"category": "Family", "en": "Your family loves you very much.", "es": "Su familia le quiere mucho.", "say": "soo fah-MEE-lee-ah leh kee-EH-reh MOO-choh"},
    {"category": "Family", "en": "Let's talk about your family.", "es": "Hablemos de su familia.", "say": "ah-BLEH-mohs deh soo fah-MEE-lee-ah"},
]

# What a resident reverting to Spanish might say, in their own words.
RESIDENT_SPANISH = [
    {"es": "Quiero ir a casa.", "en": "I want to go home.", "reply_es": "Está a salvo aquí conmigo. Vamos a sentarnos juntos.", "reply_en": "You are safe here with me. Let's sit together."},
    {"es": "¿Dónde está mi mamá?", "en": "Where is my mom?", "reply_es": "Su mamá le quería mucho. Estoy aquí con usted.", "reply_en": "Your mom loved you very much. I am here with you."},
    {"es": "¿Dónde está mi papá?", "en": "Where is my dad?", "reply_es": "Su papá le quería mucho. Estoy aquí con usted.", "reply_en": "Your dad loved you very much. I am here with you."},
    {"es": "Tengo hambre.", "en": "I am hungry.", "reply_es": "Vamos a comer algo.", "reply_en": "Let's get something to eat."},
    {"es": "Tengo sed.", "en": "I am thirsty.", "reply_es": "¿Quiere un poco de agua?", "reply_en": "Would you like some water?"},
    {"es": "Quiero agua.", "en": "I want water.", "reply_es": "Aquí tiene agua.", "reply_en": "Here is some water."},
    {"es": "Necesito ir al baño.", "en": "I need the bathroom.", "reply_es": "Vamos al baño.", "reply_en": "Let's go to the bathroom."},
    {"es": "Me duele.", "en": "Something hurts.", "reply_es": "¿Dónde le duele? Voy a buscar ayuda.", "reply_en": "Where does it hurt? I am going to get help."},
    {"es": "Me duele la cabeza.", "en": "My head hurts.", "reply_es": "Voy a buscar ayuda.", "reply_en": "I am going to get help."},
    {"es": "Me duele el estómago.", "en": "My stomach hurts.", "reply_es": "Voy a buscar ayuda.", "reply_en": "I am going to get help."},
    {"es": "Tengo miedo.", "en": "I am scared.", "reply_es": "Está a salvo. Me quedo con usted.", "reply_en": "You are safe. I am staying with you."},
    {"es": "Estoy cansado.", "en": "I am tired.", "reply_es": "Vamos a descansar.", "reply_en": "Let's rest."},
    {"es": "Tengo frío.", "en": "I am cold.", "reply_es": "Vamos a buscar una cobija.", "reply_en": "Let's get a blanket."},
    {"es": "Tengo calor.", "en": "I am hot.", "reply_es": "Vamos a buscar un lugar fresco.", "reply_en": "Let's find a cool place."},
    {"es": "No quiero.", "en": "I do not want to.", "reply_es": "Está bien. No hay prisa.", "reply_en": "That is okay. There is no rush."},
    {"es": "Déjame en paz.", "en": "Leave me alone.", "reply_es": "Está bien. Estoy cerca si me necesita.", "reply_en": "That is okay. I am nearby if you need me."},
    {"es": "Ayúdame.", "en": "Help me.", "reply_es": "Estoy aquí para ayudarle.", "reply_en": "I am here to help you."},
    {"es": "No entiendo.", "en": "I do not understand.", "reply_es": "No se preocupe. Vamos despacio.", "reply_en": "Do not worry. Let's go slowly."},
    {"es": "No me siento bien.", "en": "I do not feel well.", "reply_es": "Voy a buscar ayuda.", "reply_en": "I am going to get help."},
    {"es": "Quiero dormir.", "en": "I want to sleep.", "reply_es": "Es hora de dormir. Vamos a descansar.", "reply_en": "It is time to sleep. Let's rest."},
    {"es": "¿Cuándo vienen?", "en": "When are they coming?", "reply_es": "Vendrán pronto. Esperemos juntos.", "reply_en": "They will come soon. Let's wait together."},
]

SPANISH_CATEGORIES = sorted(set(p["category"] for p in SPANISH_PHRASES))


def search_spanish(query, category="All"):
    """Search caregiver phrases by English or Spanish words."""
    q = (query or "").strip().lower()
    out = []
    for p in SPANISH_PHRASES:
        if category and category != "All" and p["category"] != category:
            continue
        if not q or all(word in (p["en"] + " " + p["es"]).lower() for word in q.split()):
            out.append(p)
    return out


def search_resident_spanish(query):
    """Search resident Spanish phrases by Spanish or English words."""
    q = (query or "").strip().lower()
    if not q:
        return RESIDENT_SPANISH
    return [p for p in RESIDENT_SPANISH
            if all(word in (p["es"] + " " + p["en"]).lower() for word in q.split())]


# ------------------------------------------------------- simplify my words
def simplify(text):
    """Turn a long instruction into short, one-step lines.

    Rule-based only: split on sentence ends and on and/then, strip
    filler, and return numbered steps. It does not claim to understand
    meaning the way a person would.
    """
    if not text or not text.strip():
        return []
    cleaned = text.strip()
    # Split sentences, then split long sentences on and / then.
    parts = re.split(r"[.!?]+", cleaned)
    steps = []
    for part in parts:
        for chunk in re.split(r"\b(?:and then|then|and)\b", part, flags=re.I):
            chunk = chunk.strip(" ,")
            if not chunk:
                continue
            # Drop common filler openers.
            chunk = re.sub(r"^(okay|ok|so|now|listen|come on)[,\s]+", "", chunk, flags=re.I)
            chunk = chunk.strip()
            if chunk:
                steps.append(chunk[0].upper() + chunk[1:] + ".")
    return steps
