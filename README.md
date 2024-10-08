# Bookworm

## My personal bookkeeping software

### Description

For months, I have been trying to properly track my expenses because I want to be fiscally responsible with my money.
However, I have 7 different accounts to look at when reviewing my account activity over the past month, so that can be extremely tedious.

My solution for this was to create a `Python` script that helps me manage all of that data. I used the `Pandas` library to work with all of the csv files I have.

### How to use the script

The script has 2 functionalities:

**preprocess**

- manually download your account activity as csv files for a specific month
- create a folder for that month inside of the data folder
- place your csv files into an "input" folder
- run the following command: `python3 bookworm.py preprocess <month>`
- preprocess will normalize all of the data and join it together into 1 csv file called `preprocessed-transactions.csv`

**summarize**

- once you have manually reviewed these preprocessed transactions, you can place them into a file called `transactions.csv`
- run the following command: `python3 bookworm.py summarize <month>`
- this should create a `summary.txt` file which summarizes your expenses for the month
