"""
Credit card fraud detection
 ~ Shane Short
"""

import random
import datetime
import hashlib
import time
import unittest
# non standard libraries
import numpy as np


def luhn_check_dig(num):
    """
    Function to compute the Luhn Algorithms check sum digit for a given card number
        :param num (int): A randomly generated 15-digit number
        :return check_sim (int): The associated check sum digit for the given random number
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
        :return cardno (int): A valid card number
    """
    payload = int(''.join(["{}".format(random.randint(0, 9)) for num in range(0, 15)]))
    check_dig = luhn_check_dig(payload)
    cardno = int(str(payload) + str(check_dig))
    return cardno


def random_date(start, end):
    """
    Function to generate a random date between two given values
        :param start (datetime object): start of the given range
        :param end (datetime object): end of the given range
        :return start + timedelta(seconds=random_second) (datetime object): A random time within a range
    """
    # range of time in days and seconds
    delta = end - start

    # range in seconds
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds

    # random increment in this interval
    random_second = random.randrange(int_delta)

    return start + datetime.timedelta(seconds=random_second)


def generate_trans(card_number, timestamp):
    """
    Function to generate a semi-realistic distribution of transactions
        :param card_number (int): A valid card number in plain text format
        :param timestamp (datetime object): Time the transaction occurred
        :return hashed_card.hexdigest() (str): hexadecimal encoding of the md5 hashed card number
        :return timestamp (datetime object): Time the transaction occurred
        :return amt (float): Amount spent
    """
    # generate a transaction amount
    # lets assume small transactions are more common than large ones
    # and that this distribution is approximately gaussian
    # mean and standard deviation to generate the distribution of transaction amounts
    mu, sigma = 0, 100.0
    amt = np.abs(np.random.normal(mu, sigma, 1))[0]

    # Let's use md5 to handle the string hashing
    hashed_card = hashlib.md5(str(card_number).encode())

    return hashed_card.hexdigest(), timestamp, amt


def flag_fraudulent_activity(transactions, range, threshold, granularity):
    """
    Function to flag potentially fraudulent transaction activity
        :param transactions (list): A list of transaction data in comma separated string format
            - '<card hash>,<timestamp>,<amount>'
        :param range (tuple): The space in time over which transaction take place
        :param threshold (int): The daily spending threshold above which activity is flagged as fraudulent
        :param granularity (int): The increment (in second) by which each timeseries window is shifted
        :return flagged_cards (list): A list of the card hashes which have been identified as fraudulent
    """
    fraudulent_cards = []
    # set the initial starting point of the sliding window
    window_centre = range[0]

    # convert trans into an indexible array
    transactions = [el.split(',') for el in transactions]

    # get unique card hashes
    unique_hashes = list(set([x[0] for x in transactions]))
    print(f"\nunique cards in dataset: {unique_hashes}\n")

    while window_centre < range[1]:

        # create sliding time window values
        window_centre += datetime.timedelta(seconds=granularity)
        window_start = window_centre + datetime.timedelta(seconds=-3600 * 12)
        window_end = window_centre + datetime.timedelta(seconds=3600 * 12)

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
                print(f"Card hash {card_num} \n Suspicious activity in 24 hours around {window_centre}")
                print(f"total spend on this day by card {card_num}: {amt_per_day[unique_hashes.index(card_num)]} \n")
                fraudulent_cards.append(card_num)

    # drop duplicate card hashes by casting to a set and back to a list
    unique_hashes = (list(set(fraudulent_cards)))

    return unique_hashes


class TestCases(unittest.TestCase):

    def test_single_trans(self):
        """
        This test case should return a single flagged card number ('test_card_a') as fraudulent
            :param d1 (datetime object): The start of the time range transactions may occur in
            :param d2 (datetime object): The end of the time range transactions may occur in
            :param grain (int): The granularity of timeseries windows (in seconds)
            :return (str): Pass or fail indicator
        """
        # Window of time transactions may occur in
        d1 = datetime.datetime.strptime('1/1/2021 12:00 AM', '%m/%d/%Y %I:%M %p')
        d2 = datetime.datetime.strptime('1/1/2022 12:00 AM', '%m/%d/%Y %I:%M %p')

        # random date in the range
        stamp = random_date(d1, d2)
        str_stamp = stamp.strftime('%Y-%m-%dT%H:%M:%S')

        # generate a single transaction
        single_transaction = [f"test_card_a,{str_stamp},10"]

        # check for any transactions exceeding the threshold (threshold = 0)
        flagged_cards = flag_fraudulent_activity(single_transaction, (d1, d2), 0, 3600 * 24)
        print(f"Single transaction test, flagged card number: \n{flagged_cards}")

        self.assertEqual(flagged_cards, ['test_card_a'], "Should flag test_card_a")

    def test_multiple_trans(self):
        """
        This test case should return a single flagged card number ('test_card_b') as fraudulent
            :param d1 (datetime object): The start of the time range transactions may occur in
            :param d2 (datetime object): The end of the time range transactions may occur in
            :param grain (int): The granularity of timeseries windows (in seconds)
            :return (str): Pass or fail indicator
        """
        # Window of time transactions may occur in
        d1 = datetime.datetime.strptime('1/1/2021 12:00 AM', '%m/%d/%Y %I:%M %p')
        d2 = datetime.datetime.strptime('1/1/2022 12:00 AM', '%m/%d/%Y %I:%M %p')

        # random date in the range
        stamp = random_date(d1, d2)
        str_stamp_a = stamp.strftime('%Y-%m-%dT%H:%M:%S')
        stamp = random_date(d1, d2)
        str_stamp_b = stamp.strftime('%Y-%m-%dT%H:%M:%S')

        # generate a pair of transactions, one legitimate, one fraudulent
        two_transactions = [f"test_card_a,{str_stamp_a},10", f"test_card_b,{str_stamp_b},1000"]
        # check for any transactions exceeding the threshold (threshold = 0)
        flagged_cards = flag_fraudulent_activity(two_transactions, (d1, d2), 500, 3600 * 24)
        print(f"Two transaction (1 fraudulent) test, flagged card number: \n{flagged_cards}")

        self.assertEqual(flagged_cards, ['test_card_b'], "Should flag test_card_b")

    def test_multiple_trans_legit(self):
        """
        This test case should return no card numbers as fraudulent
            :param d1 (datetime object): The start of the time range transactions may occur in
            :param d2 (datetime object): The end of the time range transactions may occur in
            :param grain (int): The granularity of timeseries windows (in seconds)
            :return (str): Pass or fail indicator
        """
        # Window of time transactions may occur in
        d1 = datetime.datetime.strptime('1/1/2021 12:00 AM', '%m/%d/%Y %I:%M %p')
        d2 = datetime.datetime.strptime('1/1/2022 12:00 AM', '%m/%d/%Y %I:%M %p')

        # random date in the range
        stamp = random_date(d1, d2)
        str_stamp_a = stamp.strftime('%Y-%m-%dT%H:%M:%S')
        stamp = random_date(d1, d2)
        str_stamp_b = stamp.strftime('%Y-%m-%dT%H:%M:%S')

        # generate a pair of transactions, one legitimate, one fraudulent
        two_transactions = [f"test_card_a,{str_stamp_a},10", f"test_card_b,{str_stamp_b},400"]
        # check for any transactions exceeding the threshold (threshold = 0)
        flagged_cards = flag_fraudulent_activity(two_transactions, (d1, d2), 500, 3600 * 24)
        print(f"Two legitimate transactions test, flagged card number: \n{flagged_cards}")

        self.assertEqual(flagged_cards, [], "Should flag no cards")

    def test_multiple_trans_sum(self):
        """
        This test case should return 'test_card_a' as fraudulent due to the sum of transactions in a day
        exceeding the threshold
            :param d1 (datetime object): The start of the time range transactions may occur in
            :param d2 (datetime object): The end of the time range transactions may occur in
            :param grain (int): The granularity of timeseries windows (in seconds)
            :return (str): Pass or fail indicator
        """
        # Window of time transactions may occur in
        d1 = datetime.datetime.strptime('1/1/2021 12:00 AM', '%m/%d/%Y %I:%M %p')
        d2 = datetime.datetime.strptime('1/1/2022 12:00 AM', '%m/%d/%Y %I:%M %p')

        # random date in the range
        stamp = random_date(d1, d2)
        str_stamp_a = stamp.strftime('%Y-%m-%dT%H:%M:%S')
        stamp += datetime.timedelta(seconds=10)
        str_stamp_b = stamp.strftime('%Y-%m-%dT%H:%M:%S')

        # generate a pair of transactions, one legitimate, one fraudulent
        two_transactions = [f"test_card_a,{str_stamp_a},10", f"test_card_a,{str_stamp_b},495"]
        # check for any transactions exceeding the threshold (threshold = 0)
        flagged_cards = flag_fraudulent_activity(two_transactions, (d1, d2), 500, 3600 * 24)
        print(f"Two transactions summing to beyond threshold test, flagged card number: \n{flagged_cards}")

        self.assertEqual(flagged_cards, ['test_card_a'], "Should flag 'test_card_a'")


if __name__ == '__main__':

    # Our first task is to generate some sample data to work with

    # Window of time transactions may occur in
    d1 = datetime.datetime.strptime('1/1/2021 12:00 AM', '%m/%d/%Y %I:%M %p')
    d2 = datetime.datetime.strptime('1/1/2022 12:00 AM', '%m/%d/%Y %I:%M %p')

    # create a list to store our sample data in
    trans = []

    num_cards = int(input("How many cards are we generating? \n"))
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

    print(f"\n{len(trans)} transactions generated")

    # get unique card hashes from list trans
    elmnts = list(set([x[0] for x in [el.split(',') for el in trans]]))
    print(f"generated sample data for card hashes: ({elmnts})")

    threshold = int(input("Enter a price threshold: \n"))

    grain = 3600 * int(input("Enter a range for each timeseries window (in hours): \n"))

    if input("Run unit tests (y/n)?\n") == 'y':
        print("\nRunning unit tests")
        unittest.main()
    else:
        # Grab Current Time Before Running the fraud detection step
        start = time.time()

        # pass transaction data to fraud detection function
        flagged_cards = flag_fraudulent_activity(trans, (d1, d2), threshold, grain)
        print(f"{len(flagged_cards)} card hashes flagged as potentially fraudulent:\n{flagged_cards}")

        # Grab Current Time After Running the Code
        end = time.time()

        # Subtract Start Time from The End Time
        total_time = end - start
        print("\nTime for execution of fraud detection step (not including data generation):\n" + str(total_time))
