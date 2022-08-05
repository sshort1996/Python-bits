"""
Credit card fraud detection
 ~ Shane Short
"""

import random
import datetime
import hashlib
import time
# non standard libraries
import numpy as np


def luhn_check_dig(num):
    """
    Function to compute the Luhn Algorithms check sum digit for a given card number
    Parameters:
                num (int): A randomly generated 15-digit number
        Returns:
                check_sim (int): The associated check sum digit for the given random number
    """
    str1 = (str(num)[::-1])[0::2]
    str2 = (str(num)[::-1])[1::2]
    doubles = [2 * int(x) for x in str2]
    res = sum([sum([int(a) for a in str(x)]) for x in doubles]) + sum([int(x) for x in str1])
    check_sum = 10 - (res % 10)
    return check_sum


def gen_card_no():
    """
    Function to generate a random valid card number
        Parameters:
        Returns:
                cardno (int): A valid card number
    """
    payload = int(''.join(["{}".format(random.randint(0, 9)) for num in range(0, 15)]))
    check_dig = luhn_check_dig(payload)
    cardno = int(str(payload) + str(check_dig))
    return cardno


def random_date(start, end):
    """
    Function to generate a random date between two given values
        Parameters:
                start (datetime object): start of the given range
                end (datetime object): end of the given range
        Returns:
                start + timedelta(seconds=random_second) (datetime object): A random time within a range
    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + datetime.timedelta(seconds=random_second)


def generate_trans(card_number, range):
    """
    Function to generate a semi-realistic distribution of transactions
        Parameters:
                card_number (int): A valid card number in plain text format
                range (tuple): The space in time over which transaction take place
        Returns:
                hashed_card.hexdigest() (str): hexadecimal encoding of the md5 hashed card number
                timestamp (datetime object): Time the transaction occurred
                amt (float): Amount spent
    """
    # generate a timestamp
    timestamp = random_date(range[0], range[1]).strftime('%Y-%m-%dT%H:%M:%S')

    # generate a transaction amount
    # lets assume small transactions are more common than large ones
    # and that this difference is approximately gaussian
    # mean and standard deviation to generate the distribution of transaction amounts
    mu, sigma = 0, 100.0
    amt = np.abs(np.random.normal(mu, sigma, 1))[0]

    # Let's use md5 to handle the string hashing
    hashed_card = hashlib.md5(str(card_number).encode())

    return hashed_card.hexdigest(), timestamp, amt


def flag_fraudulent_activity(transactions, range, threshold):
    """
    Function to flag potentially fraudulent transaction activity
        Parameters:
                transactions (dict): A dictionary of transaction data
                    key:
                        - hashed card number
                    values:
                        - transaction timestamp
                        - transaction amount
                range (tuple): The space in time over which transaction take place
                threshold (int): The daily spending threshold above which activity is flagged as fraudulent

        Returns:
                flagged_cards (list): A list of the card hashes which have been identified as fraudulent
    """
    fraudulent_cards = []
    # set the initial starting point of the sliding window
    window_centre = range[0]

    while window_centre < range[1]:

        # create sliding time window values
        window_centre += datetime.timedelta(seconds=3600 * 6)
        window_start = window_centre + datetime.timedelta(seconds=-3600 * 12)
        window_end = window_centre + datetime.timedelta(seconds=3600 * 12)
        # print(f"24-hour window from {window_start} to {window_end}")

        # determine if each transaction dict entry falls within this window
        for key, value in transactions.items():
            # set var for spend per day
            amt_per_day = 0
            for transaction in value:
                time = datetime.datetime.strptime(transaction[0], '%Y-%m-%dT%H:%M:%S')
                if window_start <= time <= window_end:
                    amt_per_day += transaction[1]
            if amt_per_day > threshold:
                print("Potential fraudulent activity flagged.")
                print(f"Card hash {key} \n in 24 hours around {window_centre}")
                print(f"total spend on this day by card {key}: {amt_per_day} \n")
                fraudulent_cards.append(key)

    # drop duplicate card hashes by casting to a set and back to a list
    unique_hashes = (list(set(fraudulent_cards)))

    return unique_hashes


if __name__ == '__main__':

    # Our first task is to generate some sample data to work with

    # Window of time transactions may occur in
    d1 = datetime.datetime.strptime('1/1/2021 12:00 AM', '%m/%d/%Y %I:%M %p')
    d2 = datetime.datetime.strptime('1/1/2022 12:00 AM', '%m/%d/%Y %I:%M %p')

    # create a dictionary to store our sample data in
    trans = dict()

    num_cards = int(input("How many cards are we generating? "))
    for card in range(num_cards):
        # create the card no. using a Luhn algorithm check sum digit appended to a random 15-digit number
        card_num = gen_card_no()

        # loop over each card number to generate a good volume of data
        for i in range(random.randint(200, 2000)):
            # return a transaction
            hashed_card_no, timestamp, amt = generate_trans(card_num, (d1, d2))
            # some logic for writing multiple values to the `card_num` key
            if hashed_card_no in trans:
                # append the new tuple to the existing array at this slot
                trans[hashed_card_no].append((timestamp, amt))
            else:
                # create a new array in this slot
                trans[hashed_card_no] = [(timestamp, amt)]

        # print(f"Sample card transactions for a single customer \n {trans[hashed_card_no]}")

    print(f"generated sample data for card hashes: ({trans.keys()})")

    threshold = int(input("Enter a price threshold: "))

    # Grab Currrent Time Before Running the fraud detection step
    start = time.time()

    # pass transaction data to fraud detection function
    flagged_cards = flag_fraudulent_activity(trans, (d1, d2), threshold)
    print(f"{len(flagged_cards)} card hashes flagged as potentially fraudulent:\n{flagged_cards}")

    # Grab Currrent Time After Running the Code
    end = time.time()

    # Subtract Start Time from The End Time
    total_time = end - start
    print("Time for execution of fraud detection step (not including data generation):\n" + str(total_time))

    # Time for execution of fraud detection step (not including data generation):
    # 8.469312906265259

    """
    This method fulfills the task as laid out in the requirements, however we can potentially
    improve on the method by accounting for the different spending habits of unique credit
    card users.
    Rather than using a fixed threshold we might try flagging a card if a daily
    spending total exceeds some percentage of the mean daily spending for that user.
    
    One possible issue to be aware of here:
        - Any average daily spending threshold will have to be first estimated over a statistically
        significant number of days to avoid flagging accounts incorrectly. Consider a user who on 
        day one of the time period makes zero transactions, then on day two makes a transaction. The 
        current algorithm would flag this as fraud immediately, even if the spending on day 2 was a 
        relatively small amount. To avoid this we should use a period of the available data (1 month
        for example) to first calculate a baseline mean daily spend before then attempting to detect
        fraudulent transactions in the remainder of the data set.   
    """

    # maybe come back and try this tomorrow?
