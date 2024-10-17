#! /usr/bin/python3

import sys
import pandas as pd
import json

# region initialization

# constants
CONFIG_PATH = "config.json"
ORDERED_COL_NAMES = ["Account", "Date", "Category", "Tags", "Cost", "Description"]
SEPARATOR = "-" * 33

# reading configuration from a json file
with open(CONFIG_PATH, "r") as file:
    config = json.load(file)

CATEGORIES = config["Categories"]
TAGS = config["Tags"]
PRECENDENCES = config["Precendences"]

# user input validation
def get_user_args():
    ACTIONS = ["preprocess", "summarize"]
    MONTHS = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]

    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <action> <month>")
        sys.exit(1)

    action = sys.argv[1].lower()
    month = sys.argv[2].lower()

    if action not in ACTIONS:
        print("error: action must be either 'preprocess' or 'summarize'.")
        sys.exit(1)

    if month not in MONTHS:
        print("error: month must be one of the 12 months.")
        sys.exit(1)

    return action, month

# endregion

# region preprocess data

# normalizing data
def normalize_wells_fargo_data(account_name, csv_file_path):
    WF_COL_INDEXES = [0, 1, 4]
    WF_COL_NAMES = ["Date", "Cost", "Description"]

    wf_data = pd.read_csv(
        csv_file_path,
        header = None,
        usecols = WF_COL_INDEXES,
        names = WF_COL_NAMES
    )

    wf_data["Account"] = account_name
    wf_data["Category"] = ""
    wf_data["Tags"] = ""
    wf_data["Cost"] = wf_data["Cost"] * -1

    return wf_data[ORDERED_COL_NAMES]

def normalize_amex_data(account_name, csv_file_path):
    amex_data = pd.read_csv(csv_file_path)

    amex_data.rename(
        columns = {"Amount": "Cost"},
        inplace = True
    )

    amex_data["Account"] = account_name
    amex_data["Category"] = ""
    amex_data["Tags"] = ""

    return amex_data[ORDERED_COL_NAMES]

def normalize_chase_data(csv_file_path):
    CHASE_ACCOUNT_NAME = "Chase"

    CHASE_COL_INDEXES = [0, 2, 5]
    CHASE_COL_NAMES = ["Date", "Description", "Cost"]

    chase_data = pd.read_csv(
        csv_file_path,
        usecols = CHASE_COL_INDEXES
    )

    chase_data.columns = CHASE_COL_NAMES

    chase_data["Account"] = CHASE_ACCOUNT_NAME
    chase_data["Category"] = ""
    chase_data["Tags"] = ""
    chase_data["Cost"] = chase_data["Cost"] * -1

    return chase_data[ORDERED_COL_NAMES]

def normalize_apple_data(csv_file_path):
    APPLE_ACCOUNT_NAME = "Apple"

    APPLE_COL_INDEXES = [0, 2, 6]
    APPLE_COL_NAMES = ["Date", "Description", "Cost"]

    apple_data = pd.read_csv(
        csv_file_path,
        usecols = APPLE_COL_INDEXES
    )

    apple_data.columns = APPLE_COL_NAMES

    apple_data["Account"] = APPLE_ACCOUNT_NAME
    apple_data["Category"] = ""
    apple_data["Tags"] = ""

    return apple_data[ORDERED_COL_NAMES]

def normalize_discover_data(csv_file_path):
    DISCOVER_ACCOUNT_NAME = "Discover"

    DISCOVER_COL_INDEXES = [0, 2, 3]
    DISCOVER_COL_NAMES = ["Date", "Description", "Cost"]

    discover_data = pd.read_csv(
        csv_file_path,
        usecols = DISCOVER_COL_INDEXES
    )

    discover_data.columns = DISCOVER_COL_NAMES

    discover_data["Account"] = DISCOVER_ACCOUNT_NAME
    discover_data["Category"] = ""
    discover_data["Tags"] = ""

    return discover_data[ORDERED_COL_NAMES]

def normalize_data(month):
    WF_CHECKING_CSV_PATH = "data/" + month + "/input/wf-checking.csv"
    WF_SAVINGS_CSV_PATH = "data/" + month + "/input/wf-savings.csv"
    checking = normalize_wells_fargo_data("Wells Fargo Checking", WF_CHECKING_CSV_PATH)
    savings = normalize_wells_fargo_data("Wells Fargo Savings", WF_SAVINGS_CSV_PATH)
    
    AMEX_GOLD_CSV_PATH = "data/" + month + "/input/amex-gold.csv"
    AMEX_BLUE_CSV_PATH = "data/" + month + "/input/amex-blue.csv"
    amex_gold = normalize_amex_data("Amex Gold", AMEX_GOLD_CSV_PATH)
    amex_blue = normalize_amex_data("Amex Blue", AMEX_BLUE_CSV_PATH)

    CHASE_CSV_PATH = "data/" + month + "/input/chase.csv"
    chase = normalize_chase_data(CHASE_CSV_PATH)
    
    APPLE_CSV_PATH =  "data/" + month + "/input/apple.csv"
    apple = normalize_apple_data(APPLE_CSV_PATH)
    
    DISCOVER_CSV_PATH  = "data/" + month + "/input/discover.csv"
    discover = normalize_discover_data(DISCOVER_CSV_PATH)

    return pd.concat([checking, savings, amex_gold, amex_blue, chase, apple, discover], ignore_index=True)

# tagging transactions
def assign_tags(row, col, categories):
    tags = []

    for category, keywords in categories.items():
        if any(keyword in row[col] for keyword in keywords):
            tags.append(category)

    return ";".join(tags)

# main logic for preprocessing
def preprocess_transactions(month):    
    # normalizing data
    preprocessed_transactions = normalize_data(month)

    # convert all strings to uppercase
    preprocessed_transactions = preprocessed_transactions.applymap(lambda value: value.upper() if isinstance(value, str) else value)

    # assigning tags
    preprocessed_transactions["Tags"] = preprocessed_transactions.apply(lambda row: assign_tags(row, "Description", TAGS), axis=1)
    preprocessed_transactions["Category"] = preprocessed_transactions.apply(lambda row: assign_tags(row, "Tags", CATEGORIES), axis=1)

    # replacing empty categories w/ misc
    preprocessed_transactions["Category"] = preprocessed_transactions["Category"].replace("", "Misc")

    # saving preprocessed data
    PREPROCESSED_TRANSACTIONS_CSV_PATH = "data/" + month + "/output/preprocessed-transactions.csv"
    preprocessed_transactions.to_csv(PREPROCESSED_TRANSACTIONS_CSV_PATH, index=False)

# endregion

# region summarize data

# creating tag cost data
def reduce_tags(tags):
    if pd.isna(tags) or tags == "":
        return ""
    
    tag_list = tags.split(";")
    
    tag_precedence = { tag: PRECENDENCES.get(tag, float("inf")) for tag in tag_list }

    selected_tag = max(tag_precedence, key = tag_precedence.get)

    return selected_tag

def create_tag_costs(transactions):
    transactions["Tags"] = transactions["Tags"].apply(reduce_tags)

    tag_costs = transactions.groupby(["Category", "Tags"])["Cost"].sum().reset_index()
    tag_costs.columns = ["Category", "Tag", "Total Cost"]

    return tag_costs.sort_values(by = "Total Cost", ascending = False)

# create summary output
def format_currency(num):
    num_rounded = round(num, 2)
    return f"{num_rounded:.2f}"

def create_tags_summary(tag_costs, category):
    summary_text = ""

    for _, row in tag_costs[tag_costs["Category"] == category].iterrows():
        tag = row["Tag"]
        cost = row["Total Cost"]

        summary_text += f"{tag:<20} : {format_currency(cost):>10}\n"

    return summary_text

def create_needs_summary(total_needs, needs_budget_amount, tag_costs):
    needs_difference = needs_budget_amount - total_needs

    summary_text = f"\n{'NEEDS':<20} : {format_currency(total_needs):>10}"
    summary_text += f"\n{'EXPECTED NEEDS':<20} : {format_currency(needs_budget_amount):>10}\n"

    needs_over_under = "under" if needs_difference >= 0 else "over"
    summary_text += f"\nAmount {needs_over_under} by {format_currency(needs_difference)}\n\n"

    summary_text += create_tags_summary(tag_costs, "Needs")
    
    summary_text += f"\n{SEPARATOR}\n"

    return summary_text

def create_wants_summary(total_wants, wants_budget_amount, tag_costs):
    wants_difference = wants_budget_amount - total_wants

    summary_text = f"\n{'WANTS':<20} : {format_currency(total_wants):>10}"
    summary_text += f"\n{'EXPECTED WANTS':<20} : {format_currency(wants_budget_amount):>10}\n"
    
    wants_over_under = "under" if wants_difference >= 0 else "over"
    summary_text += f"\nAmount {wants_over_under} by {format_currency(wants_difference)}\n\n"

    summary_text += create_tags_summary(tag_costs, "Wants")

    summary_text += f"\n{SEPARATOR}\n"

    return summary_text

def create_savings_summary(total_savings, savings_budget_amount, tag_costs):
    savings_difference = savings_budget_amount - total_savings

    summary_text = f"\n{'SAVINGS':<20} : {format_currency(total_savings):>10}"
    summary_text += f"\n{'EXPECTED SAVINGS':<20} : {format_currency(savings_budget_amount):>10}\n"
    
    savings_over_under = "under" if savings_difference >= 0 else "over"
    summary_text += f"\nAmount {savings_over_under} by {format_currency(savings_difference)}\n\n"

    summary_text += create_tags_summary(tag_costs, "Savings")
    summary_text += f"\n{SEPARATOR}\n"

    return summary_text

def create_summary(month, transactions):
    # getting costs by category
    total_costs = transactions.groupby("Category")["Cost"].sum().reset_index()
    total_costs.columns = ["Category", "Total Cost"]

    # getting the total income made for this month
    total_income = total_costs[total_costs["Category"] == "Income"]["Total Cost"].sum() * -1
    # creating summary text
    summary_text = f"\n{month.upper()} EXPENSES OVERVIEW\n\n{SEPARATOR}\n"
    # adding income to summary
    summary_text += f"INCOME: {format_currency(total_income)}\n{SEPARATOR}\n"

    # getting costs by tag
    tag_costs = create_tag_costs(transactions[transactions["Category"] != "Income"].copy())

    # creating summary for needs
    total_needs = total_costs[total_costs["Category"] == "Needs"]["Total Cost"].sum()
    needs_budget_amount = total_income * .5
    summary_text += create_needs_summary(total_needs, needs_budget_amount, tag_costs)

    # creating summary for wants
    total_wants = total_costs[total_costs["Category"] == "Wants"]["Total Cost"].sum()
    wants_budget_amount = total_income * .3
    summary_text += create_wants_summary(total_wants, wants_budget_amount, tag_costs)
    
    # creating summary for savings
    total_savings = total_costs[total_costs["Category"] == "Savings"]["Total Cost"].sum()
    savings_budget_amount = total_income * .2
    summary_text += create_savings_summary(total_savings, savings_budget_amount, tag_costs)

    return summary_text

# main logic for summarizing
def generate_expenses_summary(month):
    PROCESSED_TRANSACTIONS_CSV_PATH = "data/" + month + "/transactions.csv"
    SUMMARY_TXT_FILE_PATH = "data/" + month + "/output/summary.txt"

    # manually processed data:
    #   updated categories + added tags
    #   removed rows creating 0 sums like transfers
    #   added rows for savings
    transactions = pd.read_csv(PROCESSED_TRANSACTIONS_CSV_PATH)

    # replacing empty tags w/ misc
    transactions["Tags"] = transactions["Tags"].replace("", "Misc")

    # create summarized data
    summary_txt = create_summary(month, transactions)

    # saving summarized data
    with open(SUMMARY_TXT_FILE_PATH, "w") as file:
        file.write(summary_txt)
    
# endregion

# main logic
def main():
    action, month = get_user_args()
    
    if action == "preprocess":
        preprocess_transactions(month)
        output = f"bookworm: {month} preprocessing complete!"
    elif action == "summarize":
        generate_expenses_summary(month)
        output = f"bookworm: {month} summarization complete!"

    print(output)

if __name__ == "__main__":
    main()
