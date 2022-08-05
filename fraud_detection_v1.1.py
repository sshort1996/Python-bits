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


def generate_trans(card_number, timestamp):
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
    # generate a transaction amount
    # lets assume small transactions are more common than large ones
    # and that this difference is approximately gaussian
    # mean and standard deviation to generate the distribution of transaction amounts
    mu, sigma = 0, 100.0
    amt = np.abs(np.random.normal(mu, sigma, 1))[0]

    # Let's use md5 to handle the string hashing
    hashed_card = hashlib.md5(str(card_number).encode())

    return hashed_card.hexdigest(), timestamp, amt


def flag_fraudulent_activity(transactions, range, threshold, granularity):
    """
    Function to flag potentially fraudulent transaction activity
        Parameters:
                transactions (list): A list of transaction data in comma separated string format
                    - '<card hash>,<timestamp>,<amount>'
                range (tuple): The space in time over which transaction take place
                threshold (int): The daily spending threshold above which activity is flagged as fraudulent

        Returns:
                flagged_cards (list): A list of the card hashes which have been identified as fraudulent
    """
    fraudulent_cards = []
    # set the initial starting point of the sliding window
    window_centre = range[0]

    # convert trans into an indexible array
    transactions = [el.split(',') for el in transactions]

    # get unique card hashes
    unique_hashes = list(set([x[0] for x in transactions]))
    print(f"unique cards in dataset: {unique_hashes}")

    while window_centre < range[1]:

        # create sliding time window values
        window_centre += datetime.timedelta(seconds=granularity)
        window_start = window_centre + datetime.timedelta(seconds=-3600 * 12)
        window_end = window_centre + datetime.timedelta(seconds=3600 * 12)
        # print(f"24-hour window from {window_start} to {window_end}")

        # create a zero entry in a list for each card present
        amt_per_day = [0]*len(unique_hashes)

        # determine if each transaction dict entry falls within this window
        for i in transactions:
            # time of current transaction
            time = datetime.datetime.strptime(i[1], '%Y-%m-%dT%H:%M:%S')
            # check time is within the target window
            if window_start <= time <= window_end:
                # add transaction amount to that cards amount total per window
                amt_per_day[unique_hashes.index(i[0])] += float(i[2])

        # check is daily total greater than the threshold amount
        for card_num in unique_hashes:
            if amt_per_day[unique_hashes.index(card_num)] > threshold:
                print("Potential fraudulent activity flagged.")
                print(f"Card hash {card_num} \n in 24 hours around {window_centre}")
                print(f"total spend on this day by card {card_num}: {amt_per_day[unique_hashes.index(card_num)]} \n")
                fraudulent_cards.append(card_num)

    # drop duplicate card hashes by casting to a set and back to a list
    unique_hashes = (list(set(fraudulent_cards)))

    return unique_hashes


if __name__ == '__main__':

    # Our first task is to generate some sample data to work with

    # Window of time transactions may occur in
    d1 = datetime.datetime.strptime('1/1/2021 12:00 AM', '%m/%d/%Y %I:%M %p')
    d2 = datetime.datetime.strptime('1/1/2022 12:00 AM', '%m/%d/%Y %I:%M %p')

    # create a list to store our sample data in
    trans = []

    num_cards = int(input("How many cards are we generating? "))
    for card in range(num_cards):
        # create the card no. using a Luhn algorithm check sum digit appended to a random 15-digit number
        card_num = gen_card_no()

        # generate transaction data in chronological order
        stamp = d1
        while stamp < d2:
            stamp = random_date(stamp, stamp + datetime.timedelta(seconds=3600 * 24))
            str_stamp = stamp.strftime('%Y-%m-%dT%H:%M:%S')
            # return a transaction
            hashed_card_no, str_stamp, amt = generate_trans(card_num, str_stamp)
            trans.append(f"{hashed_card_no},{str_stamp},{amt}")

    print(f"{len(trans)} transactions generated")

    elmnts = list(set([x[0] for x in [el.split(',') for el in trans]]))
    print(f"generated sample data for card hashes: ({elmnts})")

    threshold = int(input("Enter a price threshold: "))

    grain = 3600 * int(input("Enter a range for each timeseries window (in hours): "))

    # Grab Currrent Time Before Running the fraud detection step
    start = time.time()

    # pass transaction data to fraud detection function
    flagged_cards = flag_fraudulent_activity(trans, (d1, d2), threshold, 3600 * 6)
    print(f"{len(flagged_cards)} card hashes flagged as potentially fraudulent:\n{flagged_cards}")

    # Grab Currrent Time After Running the Code
    end = time.time()

    # Subtract Start Time from The End Time
    total_time = end - start
    print("Time for execution of fraud detection step (not including data generation):\n" + str(total_time))

# With transaction data stored as a numpy array
# Time for execution of fraud detection step (not including data generation):
# 7.170684814453125

# With transaction data stored as a list
# Time for execution of fraud detection step (not including data generation):
# 6.732208251953125
