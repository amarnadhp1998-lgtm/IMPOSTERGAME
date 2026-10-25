"""Core rules and word bank for the Imposter word game."""

import secrets

from config import CLUE_ROUNDS, NUMBER_OF_IMPOSTERS

rng = secrets.SystemRandom()

# Prompts aim for quick recognition and fun clues for players in their 20s.
WORD_DATABASE = {
    "Adulting Is a Scam": ["Rent day", "Laundry mountain", "Grocery bill", "Meal prep", "Doctor appointment", "Tax season", "Subscription renewal", "Credit score", "Electricity bill", "Water filter service", "Appliance warranty", "One quick errand", "Home delivery slot", "Saving for later", "Forgot the password", "Cooking for one", "Life admin", "Sunday reset"],
    "Workplace Plot Twists": ["This could be an email", "Quick five-minute call", "Calendar invite", "Camera-off meeting", "Reply all", "Deadline moved up", "Lunch at the desk", "Monday morning", "Out-of-office reply", "Office birthday cake", "Spreadsheet panic", "Can you hear me?", "Meeting that ran late", "Work-from-bed day", "Fake productivity", "Team-building game", "The boss is typing", "Salary day"],
    "Dating & Situationships": ["Soft launch", "Situationship", "Double text", "Seen-zoned", "First date", "Red flag", "Green flag", "Talking stage", "Awkward hug", "Late-night hey", "Ex liked your story", "Who pays the bill?", "Dating app bio", "Voice note from a crush", "Met the parents", "Accidental like", "Hard launch", "It's complicated"],
    "Friend Group Lore": ["I'll be there in five", "The plan is in the group chat", "One friend is always late", "Split the bill", "Birthday collection", "Cancelled last minute", "Inside joke", "Four-minute voice note", "Screenshot for the group", "Who is bringing snacks?", "Photo dump", "The group trip spreadsheet", "One friend sends reels", "Where are we meeting?", "Someone lost the keys", "One last round", "Group admin drama", "We should do this more often"],
    "Kerala Core": ["KSRTC seat race", "Monsoon without an umbrella", "Power cut during a movie", "Auto uncle knows a shortcut", "Chaya before everything", "Thattukada after 10 pm", "Lulu Mall weekend", "Traffic near the junction", "Beach plan after work", "Maveli in traffic", "Vallamkali cheer squad", "Onam outfit photo", "Family Sadya food coma", "Pookalam deadline", "Rain on laundry day", "One more pazhampori", "Kochi Metro rush", "Where is the next chai shop?"],
    "Chaya, Snacks & Cravings": ["Beef porotta", "Shawarma at midnight", "Pazhampori and tea", "Biryani coma", "Appam and stew", "Puttu and kadala", "One more chaya", "Fries for the table", "I'll just taste yours", "Last piece of chicken", "Parcel for later", "Sudden ice-cream craving", "Menu scrolling for 40 minutes", "Extra cheese, please", "Leftovers at 1 am", "Payasam seconds", "Snack before dinner", "The perfect dip"],
    "College Flashbacks": ["Proxy attendance", "Attendance shortage", "Assignment at 11:58", "Group project carried by one person", "Blank mind in viva", "Backbench meeting", "Lab record panic", "Exam hall pen borrowing", "Bunk for chai", "Internal marks shock", "ID card forgotten", "Last-minute notes", "Canteen credit", "Presentation with no sleep", "Hostel room inspection", "Deadline extension request", "One shared calculator", "Farewell outfit"],
    "Phone & Internet Chaos": ["One percent battery", "Charger works at one angle", "OTP never arrived", "Wi-Fi died during the call", "Autocorrect betrayal", "Phone storage full", "Forgot the screen lock", "Typing then nothing", "Accidental screenshot", "Wrong chat", "App update at the worst time", "Face ID in the dark", "Bluetooth connected to the wrong thing", "Doomscrolling at 2 am", "Alarm snooze marathon", "The algorithm knows too much", "No signal in the lift", "Where did my charger go?"],
    "Money & UPI Panic": ["UPI payment pending", "Bank balance jump scare", "Salary disappeared", "Splitwise reminder", "Subscription I forgot", "EMI notification", "Delivery fee bigger than the snack", "Sale ends tonight", "Cashback that never came", "Card declined", "ATM queue", "₹99 add-on", "I'll save from next month", "Budget spreadsheet", "Bill-splitting maths", "Cousin's investment advice", "Rent plus deposit", "Checking the price before ordering"],
    "Weekend Plans": ["Brunch reservation", "Beach at sunset", "Movie tickets sold out", "One drink turned into three", "Getting ready takes two hours", "Plan cancelled, best day ever", "Last bus home", "Karaoke confidence", "The birthday dinner bill", "A nap before going out", "No plans but still tired", "Where is the after-party?", "Weekend trip packing", "Sunday-night regret", "The outfit debate", "Just one episode", "Dance floor warm-up", "Who is booking the cab?"],
    "Travel & Commute Chaos": ["Maps says five minutes", "Missed the bus by seconds", "Window seat negotiation", "Wrong platform", "Cab cancelled again", "Luggage overweight", "Forgot the power bank", "Group trip planner", "Booked the wrong date", "Traffic says 20 minutes", "Rain at the bus stop", "Beach sand in the bag", "Train berth swap", "Airport snack prices", "One person packed for a month", "Where did we park?", "Road trip playlist fight", "The scenic route"],
    "Family & Relatives": ["So when is the wedding?", "Unsolicited career advice", "Family group good-morning image", "Amma's missed call", "Cousin's wedding season", "One more serving", "Family photo retake", "Relative asks your salary", "Ammachi tells the same story", "Who is this number?", "Forwarded health tip", "Appa's phone needs fixing", "The long goodbye at the door", "A surprise guest", "Sunday lunch at home", "Family WhatsApp voice note", "Do you remember me?", "Take leftovers home"],
    "Malayalam Screen Time": ["Premam", "Bangalore Days", "Kumbalangi Nights", "Aavesham", "Manjummel Boys", "Premalu", "Drishyam", "Romancham", "Minnal Murali", "RDX", "Lucifer", "Thallumaala", "Bramayugam", "Joji", "FDFS plan", "Pause to explain the plot", "Skip intro", "One last episode"],
    "Health & Wellness Delusion": ["Unused gym membership", "Leg day regret", "Step counter guilt", "Bedtime scroll", "One healthy meal", "Water reminder ignored", "New workout plan", "Stretching after sitting all day", "Protein shaker in the bag", "Alarm set for a morning run", "Posture check", "Sleep schedule reset", "Sore after one workout", "Buying vegetables with good intentions", "Meditation interrupted", "Searching symptoms online", "Sunday meal prep", "Starting again on Monday"],
    "Awkward IRL Moments": ["Waved back at nobody", "Said you too to the waiter", "Forgot someone's name", "Walked into the wrong room", "Sent it to the wrong chat", "Accidental phone call", "Awkward elevator silence", "Bumped into your ex", "Laughing before you got the joke", "Someone saw your screen", "Forgot why you entered the room", "Wore your shirt inside out", "Talked while muted", "Said goodbye, then walked the same way", "One-sided high five", "Replied with the wrong emoji", "Your stomach growled in a meeting", "Pretending to recognize someone"],
    "Home & Roommate Chaos": ["Chair covered in clothes", "Dishes soaking since yesterday", "Who finished the milk?", "Shared fridge shelf", "Rent reminder in the group chat", "One missing sock", "Bathroom queue", "The mystery container", "Parcel left at the door", "Lost house key", "Wi-Fi bill split", "Someone moved the fan", "Toilet paper emergency", "Fridge stare at midnight", "Laundry chair is full", "The one clean mug", "Who left the light on?", "Cleaning before the landlord visits"],
    "Random Main-Character Moments": ["Practising a conversation in your head", "Rehearsing the food order", "Dancing when nobody is watching", "Taking 40 selfies for one photo", "Opening the fridge again", "Buying a notebook to get organized", "Imaginary argument in the shower", "Walking in with headphones like a movie", "Pretending not to see someone", "Celebrating a tiny win", "Making a playlist for one mood", "Talking to your pet like a person", "A dramatic sigh", "Putting something somewhere safe", "Saying I deserve a treat", "Being early and confused", "Looking busy when someone walks by", "Main-character walk to the shop"],
}


def initialize_game(players_dict):
    """Create private roles, a randomized clue order, and round counters."""
    player_ids = list(players_dict)
    if len(player_ids) < 3:
        raise ValueError("At least 3 players are required.")
    imposters_count = max(1, min(int(NUMBER_OF_IMPOSTERS), len(player_ids) - 2))
    imposters = set(rng.sample(player_ids, imposters_count))
    category = rng.choice(list(WORD_DATABASE))
    word = rng.choice(WORD_DATABASE[category])
    roles = {
        player_id: {
            "role": "imposter" if player_id in imposters else "crewmate",
            "secret_word": None if player_id in imposters else word,
            "category": category,
        }
        for player_id in player_ids
    }
    crew = [player_id for player_id in player_ids if player_id not in imposters]
    order = crew[:]
    rng.shuffle(order)
    order.extend(player_id for player_id in player_ids if player_id in imposters)
    return {
        "category": category,
        "secret_word": word,
        "imposter_ids": imposters,
        "roles": roles,
        "round": 1,
        "clue_order": order,
        "clue_index": 0,
        "clue_rounds": max(1, int(CLUE_ROUNDS)),
        "guessed": set(),
    }


def choose_first_player(game_data):
    return game_data["clue_order"][0]
