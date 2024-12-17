import requests
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from unidecode import unidecode
from rapidfuzz import fuzz
import os
import re

# Telegram bot token
TOKEN = '7785571101:AAFwPqGoyMN-yyZRbH2lYtR4Tbg0-Wd6xmE'  # Replace with your bot token
EXCEL_FILE_PATH = 'orders.xlsx'    # Path to save the Excel file

# Define group chat ids based on state-district
GROUP_MAPPING = {
    "Madhya Pradesh": {
        "Gwalior": "-1002420457309",  # Gwalior group ID
        "Bhopal": "-1002307200516"    # Bhopal group ID
    },
    "Maharashtra": {
        "Mumbai": "-1002420457300",   # Mumbai group ID
        "Pune": "-1002420457301"      # Pune group ID
    }
}

# Function to get state and district by pin code using Postalpincode.in API
def get_location_by_pin(pin_code):
    url = f'https://api.postalpincode.in/pincode/{pin_code}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data[0]['Status'] == 'Success' and len(data[0]['PostOffice']) > 0:
                state = data[0]['PostOffice'][0].get('State', '')
                district = data[0]['PostOffice'][0].get('District', '')
                return state, district
        return None, None
    except Exception as e:
        print(f"Error fetching data for pin code {pin_code}: {e}")
        return None, None

# Function to perform transliteration and normalization
def normalize_text(text):
    if text:
        text = unidecode(text)  # Convert Hindi/Unicode text to English characters
        text = text.strip().lower()  # Remove extra spaces and convert to lowercase
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    return text

# Function to match state and district using fuzzy matching
def fuzzy_match(user_state, user_district, api_state, api_district, threshold_state=70, threshold_district=70):
    # Normalize the input and API response
    user_state_norm = normalize_text(user_state)
    user_district_norm = normalize_text(user_district)
    api_state_norm = normalize_text(api_state)
    api_district_norm = normalize_text(api_district)

    # Calculate similarity scores
    state_similarity = fuzz.ratio(user_state_norm, api_state_norm)
    district_similarity = fuzz.ratio(user_district_norm, api_district_norm)

    # Debugging similarity scores
    print(f"Fuzzy Match Debugging:")
    print(f"User State: {user_state_norm}, API State: {api_state_norm}, Similarity: {state_similarity}")
    print(f"User District: {user_district_norm}, API District: {api_district_norm}, Similarity: {district_similarity}")

    # Check if both state and district match the threshold or one is higher
    if state_similarity >= threshold_state and district_similarity >= threshold_district:
        return True, "Match successful"
    else:
        # Prepare error message with suggestions
        error_message = (
            f"Aapne jo State aur District diya hai, usmein galti lag rahi hai:\n"
            f"- Diya gaya State: '{user_state}', Sahi hona chahiye: '{api_state}'\n"
            f"- Diya gaya District: '{user_district}', Sahi hona chahiye: '{api_district}'\n"
            f"Kripya sahi information bheje."
        )
        return False, error_message

# Function to save order to Excel
def save_order_to_excel(order_data):
    if os.path.exists(EXCEL_FILE_PATH):
        df = pd.read_excel(EXCEL_FILE_PATH)
    else:
        df = pd.DataFrame(columns=["Name", "Address", "Pin Code", "District", "State", "Phone Number", "Order Details"])

    # Append the new order
    df = pd.concat([df, pd.DataFrame([order_data])], ignore_index=True)
    df.to_excel(EXCEL_FILE_PATH, index=False)

# Function to extract order details from user message using regex
def extract_order_details(user_message):
    # Define regex patterns for each field
    patterns = {
        "name": r"Name[:]?\s*(.+?)(?=\s*(Address|$))",
        "address": r"Address[:]?\s*(.+?)(?=\s*(Pin Code|$))",
        "pin_code": r"Pin Code[:]?\s*(\d{6})",
        "district": r"District[:]?\s*(.+?)(?=\s*(State|$))",
        "state": r"State[:]?\s*(.+?)(?=\s*(Phone|$))",
        "phone": r"Phone Number[:]?\s*(\d{10})",
        "order_details": r"Order Details[:]?\s*(.+)"
    }

    extracted_details = {}

    # Loop through the patterns and extract data
    for field, pattern in patterns.items():
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            extracted_details[field] = match.group(1).strip()

    return extracted_details

# Function to handle orders
async def handle_order(update: Update, context: CallbackContext):
    user_message = update.message.text
    try:
        # Extract order details from the user message using regex
        extracted_details = extract_order_details(user_message)

        # Debug extracted details
        print(f"Extracted Details: {extracted_details}")

        # Check if all required fields are present
        required_fields = ["name", "address", "pin_code", "district", "state", "phone", "order_details"]
        if not all(field in extracted_details for field in required_fields):
            await update.message.reply_text("Kuch details missing hain, kripya sabhi fields bhar ke bhejein.\nFormat: Name, Address, Pin Code, District, State, Phone Number, Order Details.")
            return

        # Extracted details from the user input
        user_name = extracted_details["name"]
        user_address = extracted_details["address"]
        pin_code = extracted_details["pin_code"]
        user_district = extracted_details["district"]
        user_state = extracted_details["state"]
        user_phone = extracted_details["phone"]
        order_details = extracted_details["order_details"]

        # Get state and district from API using pin code
        api_state, api_district = get_location_by_pin(pin_code)

        if api_state and api_district:
            # Step 1: Match user provided state and district with API response
            if user_state.lower() == api_state.lower() and user_district.lower() == api_district.lower():
                # If state and district match directly, send order to the group
                if api_state in GROUP_MAPPING and api_district in GROUP_MAPPING[api_state]:
                    group_id = GROUP_MAPPING[api_state][api_district]
                    print(f"Direct match found. Sending message to group ID: {group_id}")
                    try:
                        # Send the order details to the group
                        await context.bot.send_message(group_id, f"New Order Received:\n\n"
                                                                 f"Name: {user_name}\nAddress: {user_address}\n"
                                                                 f"Pin Code: {pin_code}\nDistrict: {user_district}\n"
                                                                 f"State: {user_state}\nPhone: {user_phone}\n"
                                                                 f"Order Details: {order_details}")
                        await update.message.reply_text(f"Order valid hai aur direct matching basis par group mein bhej diya gaya.")
                        
                        # Save the order to Excel
                        order_data = {
                            "Name": user_name,
                            "Address": user_address,
                            "Pin Code": pin_code,
                            "District": user_district,
                            "State": user_state,
                            "Phone Number": user_phone,
                            "Order Details": order_details
                        }
                        save_order_to_excel(order_data)
                    except Exception as e:
                        print(f"Error sending message to group: {e}")
                        await update.message.reply_text(f"Order valid hai, lekin group mein bhejne mein error aayi.")
                else:
                    await update.message.reply_text("State aur District match hone par bhi group mapping nahi mili.")
            else:
                # Step 2: If state and district don't match, perform fuzzy matching
                is_valid, message = fuzzy_match(user_state, user_district, api_state, api_district)

                if is_valid:
                    # If fuzzy match is successful, send to group
                    order_data = {
                        "Name": user_name,
                        "Address": user_address,
                        "Pin Code": pin_code,
                        "District": user_district,
                        "State": user_state,
                        "Phone Number": user_phone,
                        "Order Details": order_details
                    }
                    save_order_to_excel(order_data)

                    # After fuzzy match, fetch group ID based on API state and district
                    if api_state in GROUP_MAPPING and api_district in GROUP_MAPPING[api_state]:
                        group_id = GROUP_MAPPING[api_state][api_district]
                        print(f"Fuzzy match successful. Sending message to group ID: {group_id}")
                        try:
                            # Send the order details to the group
                            await context.bot.send_message(group_id, f"New Order Received:\n\n"
                                                                     f"Name: {user_name}\nAddress: {user_address}\n"
                                                                     f"Pin Code: {pin_code}\nDistrict: {user_district}\n"
                                                                     f"State: {user_state}\nPhone: {user_phone}\n"
                                                                     f"Order Details: {order_details}")
                            await update.message.reply_text(f"Order valid hai aur fuzzy match basis par group mein bhej diya gaya.")
                        except Exception as e:
                            print(f"Error sending message to group: {e}")
                            await update.message.reply_text(f"Order valid hai, lekin group mein bhejne mein error aayi.")
                else:
                    # Step 3: If no match, send the order based on district
                    await update.message.reply_text(f"State aur District match nahi hua. Aapke district ke basis par order send kiya jaa raha hai.")
                    # Here you can send the order to a default district group based on user district
                    if user_state in GROUP_MAPPING and user_district in GROUP_MAPPING[user_state]:
                        group_id = GROUP_MAPPING[user_state][user_district]
                        try:
                            # Send the order details to the group
                            await context.bot.send_message(group_id, f"New Order Received (Direct Send based on District):\n\n"
                                                                     f"Name: {user_name}\nAddress: {user_address}\n"
                                                                     f"Pin Code: {pin_code}\nDistrict: {user_district}\n"
                                                                     f"State: {user_state}\nPhone: {user_phone}\n"
                                                                     f"Order Details: {order_details}")
                            await update.message.reply_text(f"Order directly district ke basis par group mein bhej diya gaya.")
                            
                            # Save the order to Excel
                            order_data = {
                                "Name": user_name,
                                "Address": user_address,
                                "Pin Code": pin_code,
                                "District": user_district,
                                "State": user_state,
                                "Phone Number": user_phone,
                                "Order Details": order_details
                            }
                            save_order_to_excel(order_data)
                        except Exception as e:
                            print(f"Error sending message to group: {e}")
                            await update.message.reply_text(f"Order send karte waqt error aayi.")
                    else:
                        await update.message.reply_text(f"Koi valid group mapping nahi mili aapke district ke liye.")
        else:
            # Fallback when API fails
            await update.message.reply_text("Diya gaya Pin Code invalid hai ya API response nahi mila. Aapke district ke basis par order send kiya jaa raha hai.")
            if user_state in GROUP_MAPPING and user_district in GROUP_MAPPING[user_state]:
                group_id = GROUP_MAPPING[user_state][user_district]
                try:
                    # Send the order details to the group
                    await context.bot.send_message(group_id, f"New Order Received (Direct Send based on District):\n\n"
                                                             f"Name: {user_name}\nAddress: {user_address}\n"
                                                             f"Pin Code: {pin_code}\nDistrict: {user_district}\n"
                                                             f"State: {user_state}\nPhone: {user_phone}\n"
                                                             f"Order Details: {order_details}")
                    await update.message.reply_text(f"Order directly district ke basis par group mein bhej diya gaya.")
                    
                    # Save the order to Excel
                    order_data = {
                        "Name": user_name,
                        "Address": user_address,
                        "Pin Code": pin_code,
                        "District": user_district,
                        "State": user_state,
                        "Phone Number": user_phone,
                        "Order Details": order_details
                    }
                    save_order_to_excel(order_data)
                except Exception as e:
                    print(f"Error sending message to group: {e}")
                    await update.message.reply_text(f"Order send karte waqt error aayi.")
            else:
                await update.message.reply_text(f"Koi valid group mapping nahi mili aapke district ke liye.")
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Kuch error aayi. Kripya dobara try karein.")
        

# Telegram bot handler setup
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Hello! Please send the order details.')

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))

    app.run_polling()

if __name__ == '__main__':
    main()
