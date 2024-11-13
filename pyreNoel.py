#! /usr/bin/env python3

__version__ = "0.1"
__author__ = "Joachim Robert, @joachimesque"

from datetime import datetime
from string import Template

import yagmail
import json
import argparse
import os.path
import pprint #for debugging purposes
import time

from random import shuffle


# When there's lots of constraints the draw can be very long.
# We don't want to hog an old machine, do we?
LOOP_LIMIT = 250


def build_email_template(santa, giftee):
    # get the file name from command line arguments
    email_template_file_name = f"template.{args.language[0]}.txt"

    if giftee["so_name"] == "" and giftee["so_email"] == "":
        no_so_file_name = f"template.{args.language[0]}.no-so.txt"
        
        if os.path.isfile(no_so_file_name):
            email_template_file_name = no_so_file_name

    # if file exists
    if os.path.isfile(email_template_file_name):
        # open it
        email_template_file = open(email_template_file_name)
        # read it
        email_template = Template(email_template_file.read())
        # get email variables from function arguments
        email_data = {
            "santa_name": santa["name"],
            "giftee_name": giftee["name"],
            "giftees_so_name": giftee["so_name"],
            "giftees_so_email": giftee["so_email"],
            "reply_email": settings["reply_email"],
            "reply_name": settings["reply_name"],
        }

        # substitute the template
        result = email_template.substitute(email_data)

        return result

    else:
        print("Language not found. Aborting everything.")
        quit()


def get_config_data(config_data_file="data.json"):
    if os.path.isfile(config_data_file):
        file_data = open(config_data_file, "r")
        file_json_data = json.load(file_data)
        return file_json_data
    else:
        return False


def get_previous_years(years_list):
    # should return a list of lists.

    # we intialize the list
    previous_years = []

    for year in years_list:
        file_name = "draw." + year + ".json"
        if os.path.isfile(file_name):
            file_data = open(file_name, "r")
            file_json_data = json.load(file_data)
            previous_years.append(file_json_data)
            print("Family data added for {}".format(year))

        else:
            print("Family data skipped for {} due to file not found.".format(year))

    return previous_years


def get_draw(family_data):

    print("Drawing the Secret Santa", end="")

    should_loop = True

    # loop until I say not to
    for loop in range(LOOP_LIMIT):
        shuffled = [i for i in family_data]
        # shuffle the array
        shuffle(shuffled)

        for i, j in enumerate(shuffled):
            family_data[i]["should_gift"] = j["id"]

        # 👻
        for i, j in enumerate(family_data):
            if "force" in j:
                gifter_initial = j["should_gift"]
                forced = j["force"]

                other = [p for p, q in enumerate(family_data) if q["should_gift"] == forced][0]

                family_data[other]["should_gift"] = gifter_initial
                family_data[i]["should_gift"] = forced

        print(".", end="")

        duplicate_test = []

        for person in family_data:

            # no self gift
            if person["id"] == person["should_gift"]:
                duplicate_test += "self gift"

            # let’s not have strict reciprocity santa <-> giftee
            giftee = [i for i in family_data if i["id"] == person["should_gift"]][0]
            if giftee["should_gift"] == person["id"]:
                duplicate_test += f"reciprocity {person['name']} {giftee['name']}"

            # no one gets their SO or previous giftees as secret santa
            if person["should_gift"] in person["avoid"]:
                duplicate_test += f"avoid {person['should_gift']}, {person['avoid']}"

        # If no duplicates and stuff like that
        if len(duplicate_test) == 0:
            # one final dot
            print(".")
            return family_data
    else:
        print(".")
        print(f"Maximum tries ({LOOP_LIMIT}) reached. Please try again.")
        exit()


def write_draw(draw, disabled):
    # get the year
    current_year = datetime.now().year
    # here's the name
    file_name = f"draw.{str(current_year)}.json"

    data = {person["id"]: person["should_gift"] for person in draw}

    for d in disabled:
        data[d] = None

    data = dict(sorted(data.items()))

    # here's the json
    data_json = json.dumps(data)

    # so yeah if the file already exists we ask confirmation for overwriting it
    if os.path.isfile(file_name):
        print("Looks like the file {} already exists.".format(file_name))
        if input("Overwrite? (y/N) ") == "y":
            file_open = open(file_name, "w")
            file_open.write(str(data_json))
            file_open.close()
            return "File Saved"
        else:
            return "File not overwritten, here's the raw output: {}".format(data_json)
    else:
        file_open = open(file_name, "w")
        file_open.write(str(data_json))
        file_open.close()
        return "File Saved"


def send_emails(draw, test=False):
    # so in this one we're sending emails
    print("Sending emails…")
    yag = yagmail.SMTP(settings["gmail_account"])

    for person in draw:
        giftee = next(i for i in draw if i["id"] == person["should_gift"])

        # get the email address
        email_to = person["email"]

        # get email template in the language specified in command line args
        email_template = build_email_template(person, giftee)

        if email_template:
            # get the subject (it's the first line)
            email_subject = email_template.splitlines()[0]
            # get the body (it's all the lines after the two first lines)
            email_body = email_template.split("\n", 2)[2]

            if test:
                # Send the email without "to" !
                yag.send(subject=email_subject, contents=email_body)
                print(
                    "The TEST email to {} has been sent to you!".format(
                        person["name"]
                    )
                )
            else:
                # Send the email with "to" !
                yag.send(to=email_to, subject=email_subject, contents=email_body)
                print("The email to {} has been sent!".format(person["name"]))

        time.sleep(1)

    return "All mail sent!"


def pretty_print(draw):
    for person in draw:
        print(
            f"{person['name']} -> {[i['name'] for i in family_data if i['id'] == person['should_gift']][0]}"
        )


if __name__ == "__main__":
    # Args parser
    parser = argparse.ArgumentParser(
        description="A Secret Santa drawer for the whole family, \
          but only if no one is single.\nUsed without arguments, it \
          only writes an output file."
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Will draw, but won’t send emails and won’t write the \
          output file.",
    )
    parser.add_argument(
        "-s",
        "--send-emails",
        action="store_true",
        help="Will draw, send emails and write the output file.",
    )
    parser.add_argument(
        "-t",
        "--test-emails",
        action="store_true",
        help="Will draw, send test emails (to yourself) and write the \
          output file.",
    )
    parser.add_argument(
        "-p",
        "--previous-years",
        nargs="+",
        action="store",
        dest="year",
        default=[],
        help="The draw will avoid duplicating results from previous \
          years.",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        nargs=1,
        action="store",
        dest="config_file",
        default=["data.json"],
        help="Will use the specified config file. Defaults to data.json.",
    )
    parser.add_argument(
        "-l",
        "--lang",
        nargs=1,
        action="store",
        dest="language",
        default=["en"],
        help="Loads an email template in \
          the specified language. The file template must be present in the \
          same dir as the script.",
    )

    args = parser.parse_args()

    # get all the configuration data
    config_data = get_config_data(args.config_file[0])
    if config_data:
        family_data = config_data["family"]
        settings = config_data["settings"]
    else:
        print("Data file not found. Check the filename.")
        quit()

    # --no-dupes 2016 2015 2014
    years_list = args.year
    previous_years = get_previous_years(years_list)

    # {'0': [4, 3, 11], '1': [2, 2, 5], '2': [11, 10, 4], '3': [6, 6, 1], '4': [9, 0, 7], '5': [1, 11, 8], '6': [8, 5, 0], '7': [3, 8, 10], '8': [7, 4, 6], '9': [10, 1, None], '10': [5, 9, 3], '11': [0, 7, 2]}
    years = {key: [year[key] for year in previous_years] for key in previous_years[0]}
    
    # List all disabled items with a tuple (index in family_data, value of "id" in the item object)
    disabled = [(c, i["id"]) for c, i in enumerate(family_data) if ("disabled" in i and i["disabled"] is True)]

    # Delete disabled items
    for d in disabled:
        del family_data[d[0]]

    # Turn tuple into single
    disabled = [i[1] for i in disabled]

    for count, value in enumerate(family_data):
        family_data[count]["so_name"] = next(i["name"] for i in family_data if i["id"] == value["avoid"][0]) if len(value["avoid"]) > 0 else ""
        family_data[count]["so_email"] = next(i["email"] for i in family_data if i["id"] == value["avoid"][0]) if len(value["avoid"]) > 0 else ""
        family_data[count]["avoid"].extend(years[str(value["id"])])
        family_data[count]["avoid"].extend(disabled)

    # the main thingy
    draw = get_draw(family_data)

    # if it's not a --dry-run
    if not args.dry_run:
        # if it's been told to --send-emails
        if args.send_emails:
            print(send_emails(draw))

        # if it's been told to --test-emails
        if args.test_emails:
            print(send_emails(draw, test=True))

        print(write_draw(draw, disabled))

    # if it IS a --dry-run
    else:
        if args.send_emails or args.test_emails:
            print("-----------------")
            print("It's a dry run, the emails were not sent.")

        print("-----------------")
        print("Final draw:")
        # print(draw)
        pretty_print(draw)
        print("No email set, no file written.")
        print("If you're satisfied, run the command with --send-emails")
