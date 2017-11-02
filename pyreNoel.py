#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

import yagmail
import json
import sys
import argparse
import os.path

from random import shuffle

__version__ = 0.1

# When there's lots of constraints the draw can be very long.
# We don't want to hog an old machine, do we?
loop_limit = 250

# Args parser
parser = argparse.ArgumentParser(
  description='A Secret Santa drawer for the whole family, but only if no one is single.\nUsed without arguments, it only writes an output file.')
parser.add_argument('-d', '--dry-run', action="store_true",
                    help='Will draw, but won’t send emails and won’t write the output file.')
parser.add_argument('-s', '--send-emails', action="store_true",
                    help='Will draw, send emails and write the output file.')
parser.add_argument('-t', '--test-emails', action="store_true",
                    help='Will draw, send test emails (to yourself) and write the output file.')
parser.add_argument('-p', '--previous-years', nargs='+', action='store', dest='year',
                    default=[], help='The draw will avoid duplicating results from previous years.')
parser.add_argument('-c', '--config-file', nargs=1, action='store', dest='config_file',
                    default=['data.json'], help='Will use the specified config file. Defaults to data.json.')

args = parser.parse_args()

def get_config_data(config_data_file = 'data.json'):
  if os.path.isfile(config_data_file):
    file_data = open(config_data_file, 'r')
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
      file_data = open(file_name, 'r')
      file_json_data = json.load(file_data)
      if len(file_json_data) == len(family_data):
        file_json_data = [tuple(i) for i in file_json_data]
        previous_years.append(file_json_data)
        print "Family data added for {}".format(year)
      else:
        print "Family data skipped for {} due to change in family size.".format(year)
    else:
      print "Family data skipped for {} due to file not found.".format(year)


  return previous_years

def check_against_previous_years(draw_shuf, x, i):
  # loop for every previous year's list
  for j in range(len(previous_years)):
    # if the value is the same as in a previous list…
    if previous_years[j][i][x] == draw_shuf[i]:
      # … go back to the start of the loop
      return False


def do_draw(draw_group_size, previous_years):
  draw = []

  for x in range(0,2):
    # create the set
    draw_shuf = range(draw_group_size)

    loop_checker = 0
      
    # loop until I say not to
    while True:

      # well, don't loop too much tho
      if loop_checker > loop_limit:
        print "Error: Too many tries"
        quit()
      else:
        loop_checker += 1
      # the big question is, should I have made a
      # for loop in len(range(loop_checker))
      # instead of a while True ?

      # shuffle the set
      shuffle(draw_shuf)
      


      # if the value is the same as its place in the list…
      # (so no one gets their SO as secret santa)
      duplicate_test = [i for i, j in zip(range(len(draw_shuf)),draw_shuf) if i == j]
      # … go back to the start of the loop
      if duplicate_test: pass

      # if the value is the same as in the previous years…
      for year in range(len(previous_years)):
        duplicate_test += [i[x] for i, j in zip(previous_years[year],draw_shuf) if i[x] == j]
      # … go back to the start of the loop
      if duplicate_test: pass

      # We don't want both in a couple to gift to the same couple, do we?…
      if x > 0:
        duplicate_test += [i for i, j in zip(draw[0],draw_shuf) if i == j]
      # … No. Go back to the start of the loop
      if duplicate_test: pass

      # if all the values are good and unique
      if not duplicate_test:
        # insert the current shuffle in the output list as a list
        draw.insert(x,draw_shuf)
        # now I say don't loop no more
        break

  # make tuples out of two lists
  draw = zip(draw[0], draw[1])
  return draw
  
def write_draw():
  # get the year
  current_year = datetime.now().year
  # here's the name
  file_name = 'draw.' + str(current_year) + '.json'

  # here's the json
  draw_json = json.dumps(draw)

  # so yeah if the file already exists we ask confirmation for overwriting it.
  if os.path.isfile(file_name):
    print "Looks like the file {} already exists.".format(file_name)
    if raw_input('Overwrite? (y/N) ') == "y":
      file_open = open(file_name, 'w')
      file_open.write(str(draw_json))
      file_open.close()
      return "File Saved"
    else:
      return "File not overwritten, here's the raw output: {}".format(draw_json)


def send_emails(test = False):
  # so in this one we're sending emails
  
  yag = yagmail.SMTP(settings['gmail_account']) 
  
  # let's loop all the couples…
  for v, couple in enumerate(draw):
    # …and then loop all the people…
    for w, person in enumerate(couple):
      # …so we can get their name and address…
      santa = family_data[v][w]
      # …and those of their giftees…
      # 1 - w will change 0 to 1 and 1 to 0
      giftee = family_data[person][1 - w]
      # …and the giftees significant other
      giftees_so = family_data[person][w]
      
      # let's build the email !
      # It's in French, I know, I'm French !
      email_to =  '{} <{}>'.format(santa['name'],santa['email'])
      email_subject = 'Tirage au sort des cadeaux de noël !'
      email_body  = "Coucou {} !\n".format(santa['name'])
      email_body += "\n"
      email_body += "Pour le Noël des Robert, tu dois offrir un cadeau à "
      email_body += "<strong>{}</strong>.".format(giftee['name'])
      email_body += "\n"
      email_body += "\n"

      # in case one couple shares a common email address.
      if person != 1:
        email_body += "Si tu as besoin d'aide, "
        email_body += "tu peux contacter {} ".format(giftees_so['name'])
        email_body += "(son email c'est {})\n".format(giftees_so['email'])
      else:
        email_body += "Attention, Mathilde et Alexis partagent "
        email_body += "un compte email :)\n"

      email_body += "\n"
      email_body += "Pour plus d'infos, contacte-moi : "
      email_body += "{}\n".format(settings['reply_email'])
      email_body += "Ne réponds pas à cet email, ça ne sera pas lu.\n"
      email_body += "\n"
      email_body += "Bises !\n"
      email_body += "\n"
      email_body += "- Joachim\n"

      if test:
        # Send the email without "to" !
        yag.send(subject = email_subject, contents = email_body)
      else:
        # Send the email with "to" !
        #yag.send(to = email_to, subject = email_subject, contents = email_body)
        print "ho là, on teste hein!"

      print "The email to {} has been sent!".format(santa['name'])

  return "All mail sent!"


if __name__ == '__main__':

  # get all the configuration data
  config_data = get_config_data(args.config_file[0])
  if config_data:
    family_data = config_data['family']
    settings = config_data['settings']
  else:
    print "Data file not found. Check the filename."
    quit()

  # --no-dupes 2016 2015 2014
  years_list = args.year
  previous_years = get_previous_years(years_list)

  # the main thingy
  draw = do_draw(len(family_data), previous_years)

  # if it's not a --dry-run
  if not args.dry_run:
    # if it's been told to --send-emails
    if args.send_emails:
      print send_emails()

    # if it's been told to --test-emails
    if args.test_emails:
      print send_emails(test = True)

    print write_draw()
  # if it IS a --dry-run
  else:
    if args.send_emails or args.test_emails:
      print "-----------------"
      print "It's a dry run, the emails were not sent."

    print "-----------------"
    print "Final draw:"
    print draw
    print "No email set, no file written."
    print "If you're satisfied with the program, run it with --send-emails"