# pyreNoel.py

## A Secret Santa draw generator for groups and families where no one is single.

Let's say your group of friends or your family is comprised of couples. You want to organize a Secret Santa for every person and their significant other.

Your Secret Santa will have to have safeguards against :
  
  - participants getting assigned their significant other
  - participants getting assigned the same giftee as a previous year
  - both persons in a couple getting assigned giftees in the same couple

Well you're in luck if this very specific situation happens to you : this script will do all of that, and more (it sends emails to everyone telling them who their giftees will be, and the giftee's SO's email if you want to contact them for ideas).

## Howto

- Python 2.7
- [Yagmail](https://github.com/kootenpv/yagmail) (install through `pip` using the command `pip install yagmail[all]`)

Be sure to configure Yagmail before use, it uses python `keyring` lib.

In a Python interpreter, type :

    import yagmail
    yagmail.register('mygmailusername', 'mygmailpassword')

## Configuration

The config file is `data.json`. You can specify a different config file if you use the argument `-c` or `--config-file`.

It's a standard JSON file, with a `settings` object and a `family` object.

`settings` contains your `gmail_account` and `reply_email`, you can send the Secret Santa emails from a different account, so people who reply to their Secret Santa won't spoil you the surprise of your own Santa.

`family` contains an array for each couple, containing an object for each person in that couple. Each person has a `name` and an `email`.

You can see a sample `data-sample.json`.

You will have to edit the script to modify the email content. Right now it's in French to fit my needs, but if you need it with another signature and a different language, you will have to change it.

Once you set up your settings, all the couples info and the email contents, you can run the script (don't forget to `chmod +x` the file).

## Running the script

If you run the script without an argument, it will only write an output file.

**-d**, **--dry-run**    
The script will make the draw, but won’t send emails and won’t write the output file.

**-s**, **--send-emails**    
The script will draw, send emails and write the output file.

**-t**, **--test-emails** : test mode    
The script will draw, send test emails and write the output file. The emails will be sent to yourself.

**-p**, **--previous-years** : limit previous years    
The draw will avoid duplicating results from previous years.

**-c**, **--config-file** :    
Specify another config file. Defaults to `data.json`.

**-l**, **--lang** :    
Specify a language. Defaults to `en`.

## What next?

The email text is in French. You gotta change it before using it. I'll have to check out simple templating systems available in Python so I can have various templates for different languages.

Why not make an online service for this script? I would need to make a GUI for editing the participants, translate Python to JS, see about the email strategy. Lotsa work and there's so little time.