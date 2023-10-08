#! /usr/bin/env python3

__version__ = "0.1"
__author__ = "Joachim Robert, @joachimesque"

from datetime import datetime
from string import Template

import yagmail
import json
import argparse
import os.path

from random import shuffle


def build_email_template(santa, giftee, giftees_so):
    # get the file name from command line arguments
    email_template_file_name = "template." + args.language[0] + ".txt"

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
            "giftees_so_name": giftees_so["name"],
            "giftees_so_email": giftees_so["email"],
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
    # should return a list of lists containing tuples.

    # we intialize the list
    previous_years = []

    # a loop for every year provided, in which we :
    # - create the file name
    # - check if filename exists
    # - open the file
    # - load the file contents as json
    # if the list is the same size as the family data :
    # - transform the list of lists as a list of tuples
    # - append the list of tuples to the list of lists of tuples
    for year in years_list:
        file_name = "draw." + year + ".json"
        if os.path.isfile(file_name):
            file_data = open(file_name, "r")
            file_json_data = json.load(file_data)
            if len(file_json_data) == len(family_data):
                file_json_data = [tuple(i) for i in file_json_data]
                previous_years.append(file_json_data)
                print("Family data added for {}".format(year))
            else:
                print(
                    "Family data skipped for {} due to change \
                    in family size.".format(
                        year
                    )
                )
        else:
            print("Family data skipped for {} due to file not found.".format(year))

    return previous_years


def do_draw(draw_group_size, previous_years, avoids):

    print("Drawing the Secret Santa", end="")

    should_loop = True

    # loop until I say not to
    for loop in range(loop_limit):
        draw_shuf = list(range(draw_group_size))

        # # shuffle the set
        shuffle(draw_shuf)
        print(".", end="")

        duplicate_test = []

        # no self gift
        duplicate_test += [i for i in range(draw_group_size) if draw_shuf[i] == i]
        # let’s not have strict reciprocity santa <-> giftee
        duplicate_test += [
            i
            for i, j in enumerate(draw_shuf)
            if draw_shuf[j] == i and draw_shuf.index(i) == j
        ]

        # no one gets their SO as secret santa
        duplicate_test += [i for i, j in enumerate(draw_shuf) if j in avoids[i]]

        # If no duplicates and stuff like that
        if len(duplicate_test) == 0:
            # one final dot
            print(".")
            return list(draw_shuf)


def write_draw():
    # get the year
    current_year = datetime.now().year
    # here's the name
    file_name = "draw." + str(current_year) + ".json"

    # here's the json
    draw_json = json.dumps(draw)

    # so yeah if the file already exists we ask confirmation for overwriting it
    if os.path.isfile(file_name):
        print("Looks like the file {} already exists.".format(file_name))
        if input("Overwrite? (y/N) ") == "y":
            file_open = open(file_name, "w")
            file_open.write(str(draw_json))
            file_open.close()
            return "File Saved"
        else:
            return "File not overwritten, here's the raw output: {}".format(draw_json)
    else:
        file_open = open(file_name, "w")
        file_open.write(str(draw_json))
        file_open.close()
        return "File Saved"


def send_emails(test=False):
    # so in this one we're sending emails
    print("Sending emails…")
    yag = yagmail.SMTP(settings["gmail_account"])

    print(draw)
    # let's loop all the couples…
    for v, couple in enumerate(draw):
        # …and then loop all the people…
        for w, person in enumerate(couple):
            # …so we can get their name and address…
            santa = family_data[v][w]
            # …and those of their giftees…
            # 1 - w will change 0 to 1 and 1 to 0
            giftee = family_data[int(person / 2)][person % 2]
            # …and the giftees significant other
            giftees_so = family_data[int(person / 2)][1 - person % 2]

            # get the email address
            email_to = santa["email"]

            # get email template in the language specified in command line args
            email_template = build_email_template(santa, giftee, giftees_so)

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
                            santa["name"]
                        )
                    )
                else:
                    # Send the email with "to" !
                    yag.send(to=email_to, subject=email_subject, contents=email_body)
                    print("The email to {} has been sent!".format(santa["name"]))

    return "All mail sent!"


def better_print(draw, family_data):
    for person in list(range(len(family_data))):
        print(f"{family_data[person]['name']} -> {family_data[draw[person]]['name']}")


if __name__ == "__main__":

    # When there's lots of constraints the draw can be very long.
    # We don't want to hog an old machine, do we?
    loop_limit = 250

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

    avoids = [i["avoid"] for i in family_data]

    # --no-dupes 2016 2015 2014
    years_list = args.year
    previous_years = get_previous_years(years_list)

    # the main thingy
    draw = do_draw(len(family_data), previous_years, avoids)

    # if it's not a --dry-run
    if not args.dry_run:
        # if it's been told to --send-emails
        if args.send_emails:
            print(send_emails())

        # if it's been told to --test-emails
        if args.test_emails:
            print(send_emails(test=True))

        print(write_draw())

    # if it IS a --dry-run
    else:
        if args.send_emails or args.test_emails:
            print("-----------------")
            print("It's a dry run, the emails were not sent.")

        print("-----------------")
        print("Final draw:")
        print(draw)
        better_print(draw, family_data)
        print("No email set, no file written.")
        print("If you're satisfied, run the command with --send-emails")
