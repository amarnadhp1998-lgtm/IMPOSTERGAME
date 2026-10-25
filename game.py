"""Core rules and state helpers for the Imposter word game."""

import secrets

from config import CLUE_ROUNDS, NUMBER_OF_IMPOSTERS

rng = secrets.SystemRandom()

WORD_DATABASE = {
    "Animals": ["Parrot", "Tiger", "Elephant", "Penguin", "Dolphin", "Cat", "Dog", "Monkey", "Lion", "Snake", "Cow", "Goat", "Chicken", "Crow", "Fish"],
    "Food": ["Pizza", "Biryani", "Burger", "Chocolate", "Pasta", "Porotta", "Beef Fry", "Chicken Fry", "Dosa", "Idli", "Appam", "Puttu", "Kadala Curry", "Samosa", "Shawarma", "Alfaham", "Pazhampori", "Unniyappam", "Payasam", "Kappa", "Fish Curry", "Chatti Pathiri", "Beef Porotta"],
    "Malayali": ["Maveli", "Pookalam", "Sadya", "Vallamkali", "Kasavu", "Chenda", "Payasam", "Thattukada", "Porotta", "Kattan Chaya", "Nadan Chaya", "Kappa", "Kallu Shappu", "Auto", "KSRTC", "Kochi", "Munnar", "Alappuzha", "Varkala", "Kovalam", "Fort Kochi", "Lulu Mall", "Nadapuram", "Toddy"],
    "Onam": ["Maveli", "Pookalam", "Sadya", "Vallamkali", "Kasavu", "Thiruvathira", "Payasam", "Chenda", "Atham", "Pulikali", "Onakkodi", "Oonjal", "Banana Leaf", "Sadhya", "Mahabali"],
    "Malayalam Movies": ["Premam", "Bangalore Days", "Kumbalangi Nights", "Aavesham", "Romancham", "Manjummel Boys", "Premalu", "Drishyam", "Lucifer", "Bheeshmaparvam", "Ranam", "Thallumaala", "Jaya Jaya Jaya Jaya Hey", "Home", "Minnal Murali", "Joji", "Virus", "Hridayam", "Turbo", "Kannur Squad", "Neru", "ARM", "RDX", "Bramayugam", "Trance"],
    "Movie Characters": ["Ranga", "George", "Aju", "Kuttan", "Dasan", "Vijayan", "Induchoodan", "Mangalassery Neelakandan", "Spadikam", "Aadu Thoma", "Shaji", "Kochunni", "Minnal Murali", "Jomon", "Koshy", "Ayyappan", "Ambaan", "Ravi", "Sushin", "Kuttettan"],
    "Funny Things": ["Autocorrect", "Pookie", "Typing", "Ghosting", "Crush", "Ex", "Screenshot", "Selfie", "Reel", "Meme", "Alarm", "Snooze", "Mosquito", "Traffic", "Power Cut", "WiFi", "Low Battery", "OTP", "Spam Call", "Wrong Number", "Group Chat", "Family Group", "Voice Note", "Missed Call", "Online Class"],
    "Youngster": ["Instagram", "WhatsApp", "Snapchat", "YouTube", "Netflix", "Spotify", "Reels", "Meme", "Viral", "Influencer", "DM", "Like", "Comment", "Story", "Followers", "Unfollow", "Streak", "Snap", "FOMO", "Vibe", "Crush", "Situationship", "Ghosting", "Red Flag", "Green Flag", "Bro", "Bestie", "POV", "GOAT"],
    "College Life": ["Assignment", "Attendance", "Proxy", "Internal", "Semester", "Backlog", "Viva", "Record", "Lab", "Canteen", "Hostel", "Roommate", "Professor", "Exam", "Night Out", "Bunk", "Last Bench", "Freshers", "Farewell", "Group Project", "Deadline", "Notes", "Calculator", "Library", "ID Card"],
    "Kerala Life": ["KSRTC", "Auto", "Bus Stop", "Chaya", "Thattukada", "Lulu Mall", "Beach", "Monsoon", "Umbrella", "Raincoat", "Traffic", "Pothole", "Horn", "Petrol Pump", "Tea Shop", "Bakery", "Fish Market", "Temple", "Church", "Mosque", "Wedding", "Reception", "Matrimony", "Ammachi", "Appan", "Chechi", "Chettan", "Mon", "Mole"],
    "Music": ["DJ", "Concert", "Playlist", "Spotify", "Headphones", "Earbuds", "Guitar", "Drums", "Singer", "Rap", "Beat", "Remix", "Dance", "DJ Party", "Karaoke", "Music Video", "Album", "Vibe", "Bass", "Mic"],
    "Sports": ["Cricket", "Football", "FIFA", "Messi", "Ronaldo", "Virat Kohli", "Dhoni", "Six", "Wicket", "Goal", "Penalty", "VAR", "Stadium", "Jersey", "Bat", "Ball", "Boot", "Referee", "World Cup", "IPL"],
    "Internet": ["Meme", "Troll", "Viral", "Algorithm", "Comment Section", "DM", "Screenshot", "Reaction", "Sticker", "GIF", "Emoji", "Hashtag", "Trending", "Clickbait", "Thumbnail", "Subscriber", "Follower", "Notification", "Password", "Captcha", "Google", "ChatGPT", "AI", "Bot"],
    "Relationships": ["Crush", "Date", "Breakup", "Ex", "Proposal", "Wedding", "Love", "Friendzone", "Ghosting", "Bestie", "Couple", "Jealousy", "Texting", "Call", "DM", "Situationship", "Red Flag", "Green Flag", "Single", "Blind Date"],
    "Random": ["Slipper", "Umbrella", "Helmet", "Remote", "Charger", "Power Bank", "Toothbrush", "Pillow", "Blanket", "Mirror", "Wallet", "Sunglasses", "Backpack", "Bottle", "Fan", "AC", "Fridge", "Washing Machine", "Pressure Cooker", "Mosquito Coil"],
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
