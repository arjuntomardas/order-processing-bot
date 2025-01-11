# order-processing-bot
# Telegram Order Management Bot

Hindi and English explain 

## Introduction
This bot is designed to handle **order management** through Telegram. Users can send their **order details** in a structured or semi-structured format, and the bot will validate, process, and forward the details to the respective Telegram group based on the location (state and district). Additionally, the bot saves all the orders in an **Excel file** for record-keeping.

---

## Features
- Accepts **order details** in text format from users.
- Validates location (State and District) using **Pin Code API**.
- Performs **fuzzy matching** if user input doesn't exactly match the API response.
- Saves valid orders to an **Excel file** (`orders.xlsx`).
- Forwards the order to the correct **Telegram group** based on location.
- Provides detailed feedback in case of errors or invalid input.

---

## Requirements
- Python 3.7 or higher
- Telegram Bot API token
- Libraries:
  - `requests`
  - `pandas`
  - `openpyxl`
  - `telegram`
  - `python-telegram-bot`
  - `rapidfuzz`
  - `unidecode`

Install the required libraries:
```bash
pip install requests pandas openpyxl python-telegram-bot rapidfuzz unidecode
Workflow
User Sends Order Details:

Format:
Name: [User Name]  
Address: [User Address]  
Pin Code: [6-digit Pin Code]  
District: [District Name]  
State: [State Name]  
Phone Number: [10-digit Mobile Number]  
Order Details: [Order Description]

•Example 
Name: Arjun Kumar  
Address: 123, MG Road  
Pin Code: 452001  
District: Indore  
State: Madhya Pradesh  
Phone Number: 9876543210  
Order Details: 5 boxes of apples


Group Mapping
The bot uses a predefined mapping of states and districts to group IDs:
GROUP_MAPPING = {
    "Madhya Pradesh": {
        "Gwalior": "-1002420457309",
        "Bhopal": "-1002307200516"
    },
    "Maharashtra": {
        "Mumbai": "-1002420457300",
        "Pune": "-1002420457301"
    }
}
Modify GROUP_MAPPING to add or update group IDs for different locations.
File Structure
orders.xlsx: Stores all the processed orders with columns:
Name
Address
Pin Code
District
State
Phone Number
Order Details

Running the Bot
Replace the placeholder bot token in the script: 
TOKEN = 'YOUR_BOT_TOKEN'

Hindi explanation 

Bot Workflow (Bot ka kaam karne ka tarika)
Aapke bot ka workflow kaafi organized aur detailed hai. Yeh bot user se order details leta hai, unko validate karta hai, aur details ko Excel file me save karke sahi Telegram group me bhejta hai. Neeche poora workflow step-by-step Hindi me samjhaya gaya hai:

User Interaction (User se interaction):
Jab koi user bot se baat karta hai, to user ko order details ek specific format me bhejni hoti hai.
Format:
Name: [User Name]  
Address: [User Address]  
Pin Code: [6-digit Pin Code]  
District: [District Name]  
State: [State Name]  
Phone Number: [10-digit Mobile Number]  
Order Details: [Order ka description]  
. Message Handling (Message ko samajhna):
Bot user ke message ko regex pattern matching ki madad se analyze karta hai.
Message me jo fields hain (Name, Address, Pin Code, etc.), unko alag-alag extract kiya jata hai.
Agar koi required field missing hoti hai, to bot user ko notify karta hai ki details incomplete hain.

Pin Code Validation (Pin Code se location validate karna):
Bot Postalpincode.in API ka use karke user ke diye gaye Pin Code se State aur District ki information leta hai.
Agar API response successful hota hai, to State aur District ko user ke diye gaye data ke saath compare kiya jata hai:
Direct Match: Agar State aur District directly match karte hain, to data ko validate karte hain.
Fuzzy Matching: Agar direct match na ho, to fuzzy logic ka use karke approximate match check kiya jata hai.. 

Order Validation (Order validate karna):
Agar State aur District match ho jata hai (directly ya fuzzy matching ke through), to order ko valid mana jata hai.
Agar match na ho, to user ko correct information dene ka error message bheja jata hai.
5. Group Mapping (Group me order bhejna):
Valid State aur District ke basis par GROUP_MAPPING dictionary me se sahi Telegram group ka ID nikala jata hai.
Us group me order details bhej di jati hain.

Save to Excel (Order ko Excel file me save karna):
Order ki saari details ek Excel file (orders.xlsx) me save ki jati hain:
Fields: Name, Address, Pin Code, District, State, Phone Number, Order Details.
Agar Excel file pehle se exist nahi karti, to bot nayi file banata hai aur order details add karta hai.

Error Handling (Galtiyon ko handle karna):
Agar Pin Code invalid hota hai ya API ka response nahi milta, to bot default group mapping ke basis par order bhejne ki koshish karta hai.
Agar group mapping me bhi issue hota hai, to user ko notify karta hai ki unka district valid nahi hai.

Response to User (User ko feedback dena):
Jab order successfully process ho jata hai, to user ko message bheja jata hai:
"Aapka order valid hai aur group me bhej diya gaya."
Agar order valid nahi hota, to bot user ko proper feedback deta hai ki kya galti hui aur kaise sahi karein.

Bot ka Use Case:
Yeh bot kaam karta hai un businesses ke liye jo alag-alag locations me orders receive karte hain aur unhe alag groups me distribute karte hain (based on State aur District).