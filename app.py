import hashlib
import json
import os

import pygsheets
from pygsheets import AuthenticationError
from json import JSONDecodeError
from groq import Groq
from replit import db

WRITE_COL = "category"
SUMMARY_COL = "description"

SHEET_NAME = os.getenv("SHEET_NAME")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Support Requests")
SA_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def map_keys_to_cols(row: dict) -> dict:
    """
    Map dictionary keys to Google Sheets columns.
    Maps keys to columns such as 'A' for 1, 'B' for 2, etc.
    """
    column_map = {}
    for idx, key in enumerate(row.keys(), start=1):
        column_letter = chr(64 + idx)
        column_map[key] = column_letter
    return column_map
  


def hash_row(row: dict) -> str:
  """
  Hash a row to be used as a unique identifier.
  """
  row_string = json.dumps(row, sort_keys=True)
  return hashlib.sha256(row_string.encode('utf-8')).hexdigest()


def generate_category(row: dict) -> str | None:
  """
  Generate a support category based on a report description.
  """

  categories = [
      "Technical Issue", "Billing Issue", "General Inquiry",
      "Product Feedback", "Feature Request", "Security Concern"
  ]

  prompt = f"""
    Your job is to categorize support requests. 
    You will be supplied with a request and you will categorize it as one of:
    {', '.join(categories)}
    You will return ONLY the category and NO OTHER text. 
  """
  user_request = f"""
    Below is the request, enclosed in triple backticks (```)
    ```
    {row.get(SUMMARY_COL)}
    ```
    """

  completion = client.chat.completions.create(
      model="llama3-70b-8192",
      messages=[
          {
              "role": "system",
              "content": prompt
          },
          {
              "role": "user",
              "content": user_request
          },
      ],
      max_tokens=50,
      seed=1337,
  )
  return completion.choices[0].message.content


if __name__ == "__main__":
  import time
  time.sleep(10)
  # Authorize
  try:
    gc = pygsheets.authorize(service_account_env_var="SERVICE_ACCOUNT_JSON")
  except JSONDecodeError as e:
    print("No service account JSON found, please configure the sheet.")
    raise e
  except AuthenticationError as e:
    print("Authentication error, please configure the sheet.")
    raise e
  # Open the Google Sheet
  sheet = gc.open(SHEET_NAME)
  worksheet = sheet.worksheet_by_title(WORKSHEET_NAME)

  # Skip header
  row_num = 2

  # Get records
  records = worksheet.get_all_records()

  # Find sheet column (e.g. "A") by column index
  cols = map_keys_to_cols(records[0])

  for row in records:

    # Create a unique hash to check for changes
    row_hash = hash_row(row)

    db_record = f"row_{row_num}"

    # Check if hash in KV store
    if db.get(db_record) != row_hash:
      print(db.get(db_record))
      print(row_hash)

      # Generate category
      category = generate_category(row=row)

      # Get cell
      cell = f"{cols[WRITE_COL]}{row_num}"

      # Update cell
      worksheet.update_value(cell, category)

      # Store hash
      db[db_record] = row_hash
      print(f"Storing hash: {row_num}")

    else:
      print(f"{row_num} hashed, skipping")

    row_num += 1
