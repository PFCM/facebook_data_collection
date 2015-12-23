# Intro
This is a utility to pull data from public facebook pages.
It requires facebook api authentication, in a file called auth.yaml
with appropriate app_secret and app_id keys.
in the same directory as the script. This is likely to change.

It is released under the BSD 2-clause license.
It is very preliminary, and accordingly poorly organised.

## How to collect facebook data:
	First we have to open a command prompt:
		open the start menu, search for "run" and click it
		a small window will open, in the text field type "cmd" and press the OK button
		a small black window with white text should open
		you will see a file path that looks something like:
			C:\Users\mcmac>
		in the below, we denote
			> xyz
			'xyz' is not recognized as an internal or external command,
			operable program or batch file.

		to indicate typing "xyz" into the prompt, pressing enter and seeing a result,
		which in this example is an error.

	The data collection is a Python script. To run it, Python (version 3.4 or higher)
	must be installed. To test:
		in the command prompt window opened earlier, run the command:

			>python --version
		the result should look something like this:
			Python 3.5.0
		if it says `python` is not recognised as a command, try:
			>py --version


		if this succeeds, replace "python" with "py" in all the following instructions,
		because Windows is strange. If it fails or if the number is less than 3.4,
		then install python. This is easy, just Google it, download and run the installer.

	Now that python is installed and we can use the command prompt we can run the script.
	The first step is to find it
		the command prompt maintains a current working directory
			this is whatever folder we are in at any given time and the path we
			can see in the command prompt
		to change it we use the command "cd" (which stands for change directory)
		but because this is windows, things are more complicated

		These are the commands to get into the right directory to run the script
		(only type whatever is on the right of the >, the stuff on the left is
		what it should show):

		1) 	C:\Users\McNamara>M:                           (press enter)
			M:\>
			(note: M is the drive letter of the dropbox drive. if it doesn't work,
			go into windows explorer and double check on the left hand side)
		2)	M:\>cd "Documents\Facebook Data Collection"    (press enter)
			M:\Documents\Facebook Data Collection">

			(hint: use the TAB key to autocomplete---
				M:\>cd doc  (press tab, and it will become)
				M:\>cd Documents\
				(keep writing)
				M:\>cd Documents\f (press tab and it should finish the job)
				M:\>cd "Documents\Facebook Data Collection\"
				and press enter)


	Now we should be in the right place. We can double check with the command "dir" which
	lists files in a directory:
		>dir
		prints a lot of statistics but there should be one line that looks like:
		08/12/2015 01:28 p.m.           9,452 bytes scraper.py

		all we care about is that it ends with "scraper.py", the times and size don't matter.

	We can now run the script.

		The simplest case -- a single page, looks like this:
			>python scraper.py <page name or id>

			where <page name or id> is replaced with the name of a facebook page.
			For example, Meridian Energy's page name is "meridianenergy" -- you can
			usually get this from the url, so Meridian's page is
			http://facebook.com/meridianenergy
			Sometimes this is just a large number, that can work just fine.

			If we run
			>python scraper.py meridianenergy

			we will get results in a file called "meridianenergy.csv"
			The output file can be specified by adding "--outfile <filename>" to
			the command. Eg:
			>python scraper.py meridianenergy --outfile out.csv

			will put the meridian data in a file called "out.csv"

		Multiple pages:
			To do multiple pages we need to make a list. We have to have the list in
			a file that contains nothing apart from the names, each on an individual line.

			To create such a file, do it in Notepad (if you do it in Word there will be
			a lot of extra formatting information which gets in the way).
			An example which would get all of Genesis Energy's data and competitors would
			contain only:

				genesisenergynz
				ContactEnergy
				mercuryenergy
				trustpower
				meridianenergy

			If we save the file in "M:\Documents\Facebook Data Collection\" as
			top-5.txt we can run the scraper on all 5 pages simply by specifying the
			filename instead of the page name:
			>python scraper.py top-5.txt

			The output will go into top-5.txt.csv, we can change it to something more
			useful in the same manner as before.

		Specifying date ranges:
			This is done in a similar manner to specifying the output file.
			Specifcally, we can set "until" and "since" dates meaning that all the results
			are those produced after "since" and before "until".
			The default "until" value is today and the default "since" value is 32 days ago.

			Note that the dates are sometimes a little bit fuzzy and some content may be
			returned that is slightly too old, so it is worth double checking your data.

			Also important to note is if the page you are scraping tends to have long
			comment threads. If so you may want to give yourself several days leeway
			on the date, as posts beyond the date range may have comments that fall
			within the range. These will not be picked up unless the post is included
			in the date range (in which case the whole thread will be included in the
			result).

			Dates are specified in the following format:
				YYYY-MM-DD

			so if we wanted posts for the month of November we would write:
			>python scraper.py top-5.txt --outfile output.csv --since 2015-01-11 --until 2015-01-12
			(note 01 not 1, we have to have the zero)

			Depending on the dates it may take a while as it cycles back.

			If you want to be sure of a full sample, then give yourself a few days either way
			(it's no problem to go into the future, that just makes sure it will get posts up to the
			current time) just to be sure, as specifying days will grab posts up until the date
			changes (ie. 00:00 on the 24 hour clock) so for the above example if we had said
			--until 2015-30-11
			we would miss any posts that actually happened on the 30th.

			Also note that the date filtering is applied to posts only, comments may sneak past.
			Alternately, there is a chance that a comment made within a date range was made on a post
			that was created outside the date range -- these comments will be missed, which is why
			it can be a good plan to give yourself a fair leeway on either side and clean it up in
			excel.
