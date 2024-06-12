import os
import random

import pygsheets
from faker import Faker
from groq import Groq

SHEET_NAME = os.getenv("SHEET_NAME", "Fake Customer Support")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Support Requests")
SA_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

# Function to generate a new sample support request
# Keywords and phrases for tech support text blurbs
keywords = [
    "integration issue",
    "API error",
    "authentication failure",
    "response time",
    "latency",
    "timeout",
    "data sync problem",
    "server error",
    "connection lost",
    "user interface",
    "dashboard",
    "analytics",
    "bot training",
    "model update",
    "subscription",
    "billing",
    "account access",
    "feature request",
    "bug report",
    "documentation",
    "support ticket",
    "customer feedback",
    "performance",
    "scalability",
    "security",
    "compliance",
    "user experience",
    "version upgrade",
    "deployment",
    "maintenance",
]


# Function to generate a realistic support request description
def generate_support_description(customer_id, product_id, order_id,
                                 request_type, status):
  prompt = f"""
    Generate a detailed customer support request description for the following scenario:

    - Issue type: {random.choice(keywords)}
    - Product id: {product_id}
    - Customer id: {customer_id}
    - Order id: {order_id}
    - Request type: {request_type}
    - Status: {status}
    """

  completion = client.chat.completions.create(
      model="llama3-70b-8192",
      messages=[
          {
              "role":
              "system",
              "content":
              "You are a bot that generates random customer support requests for a fictional ecommerce store. Return the generated request and NOTHING else. Do not enclose your response in quotes",
          },
          {
              "role": "user",
              "content": prompt
          },
      ],
      max_tokens=100,
  )

  description = completion.choices[0].message.content
  return description


# Function to generate a new sample support request
def generate_support_request():
  request_id = random.randint(1, 5000)
  customer_id = random.randint(1, 50)
  request_date = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
  request_type = random.choice([
      "Technical Issue", "Billing Issue", "General Inquiry",
      "Product Feedback", "Feature Request"
  ])
  status = random.choice(["Open", "In Progress", "Closed"])
  description = generate_support_description(request_id, customer_id,
                                             request_type, request_type,
                                             status)
  return [request_id, customer_id, request_date, status, description]


# Function to insert a new support request into the Google Sheet
def insert_support_request(new_request):
  # Find the next empty row
  next_row = len(
      worksheet.get_all_values(include_tailing_empty_rows=False)) + 1
  # Update the row with new request data
  worksheet.update_row(next_row, new_request)


if __name__ == "__main__":
  client = Groq(api_key=os.getenv("GROQ_API_KEY"))

  gc = pygsheets.authorize(service_account_json=SA_JSON)

  # Open the Google Sheet
  sheet = gc.open(SHEET_NAME)
  worksheet = sheet.worksheet_by_title(WORKSHEET_NAME)

  fake = Faker()

  print("Connected to the Google Sheet!")
  NUM_TICKETS = 30
  ticket_num = 0

  try:
    while ticket_num < NUM_TICKETS:
      new_request = generate_support_request()
      insert_support_request(new_request)
      ticket_num += 1
      print(f"Processed: ticket {ticket_num}")
  except KeyboardInterrupt:
    print("Process interrupted by user.")
  finally:
    print("Done.")
