import argparse, re, os.path, pywikibot


# function that generates all altepcodes, output is content of CSV file where a
# line contains code of episode (i.e. its title) and altepcode separated by comma
def generate_altepcodes():
    # last episode of each series
    last_eps = ["GA116", "OA158", "RZ192", "DP191", "NB142", "XY140", "SL146", "EP147"]
    # special episodes and their altepcode, so that they are inserted in the
    # correct position and the others are shifted
    specials = {
        "0065": "GAS01",
        "0066": "GAS02",
        "0678": "DPS01",
        "0679": "DPS02",
        "0804": "NBS01",
        "0826": "NBS02",
        "0827": "XYS01",
        "0856": "XYS02",
        "0872": "XYS03",
        "0902": "XYS04",
        "0950": "XYS05",
        "0951": "XYS06",
        "1234": "EPS01",
    }
    # initialize counter and text with all altepcodes
    eps_counter = 0
    altepcodes = ""
    for item in last_eps:
        # extract series abbreviation and its number of regular episodes
        series_abbr = item[:2]
        series_count = int(item[2:])
        for j in range(series_count):
            eps_counter += 1
            altepcode = str(eps_counter).zfill(4)
            # check if a special episode has current altepcode
            while specials.get(altepcode, None):
                # insert special episode in current position and repeat until
                # current altepcode is "free"
                special = specials[altepcode]
                altepcodes += f"{special},{altepcode}\n"
                eps_counter += 1
                altepcode = str(eps_counter).zfill(4)
            epcode = f"{series_abbr}{str(j + 1).zfill(3)}"
            altepcodes += f"{epcode},{altepcode}\n"
    return altepcodes


# remove altepcode from page intro and update it in infobox if needed
def fix_page(text, altepcode=None):
    # remove altepcode from intro
    text = re.sub(r" e (il |l['’])\w+ episodio della (\{\{sap|\[\[serie animata).+?(?=\.)", "", text)  # fmt: skip
    # change altepcode if needed
    if altepcode:
        pattern = r"(?<=altepcode=)\d+"
        if re.search(pattern, text):
            text = re.sub(pattern, altepcode, text)
        else:
            text = re.sub(r"(\bepcode=\w+ *\|) *", r"\1\naltepcode=" + f"{altepcode} |", text)  # fmt: skip
            text = re.sub(r"(\|epcode=\w+)", r"\1\n|altepcode=" + altepcode, text)
    # return updated text
    return text


# main function
def main():
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("--fam", default="encypok")
    parser.add_argument("--lang", default="it")
    parser.add_argument("--gen", default="data/sync/altepcodes-all.csv")
    parser.add_argument("--fix", default="data/sync/altepcodes-fix.csv")
    args = parser.parse_args()
    # setup
    site = pywikibot.Site(args.lang, fam=args.fam)
    # generate all altepcodes and write them to file
    if args.gen:
        altepcodes = generate_altepcodes()
        with open(args.gen, "w") as file:
            file.write(altepcodes)
    # fix desired episodes if file is found
    if not os.path.isfile(args.fix):
        print(f"No fix performed, cannot find file {args.fix}")
    else:
        with open(args.fix, "r") as file:
            for line in file:
                # check if altepcode was provided
                if "," in line:
                    epcode, altepcode = line.strip().split(",")
                else:
                    epcode = line.strip()
                    altepcode = None
                # fix altepcode in page
                page = pywikibot.Page(site, epcode)
                if not page.exists():
                    print(f"Skipping {page.title()}, does not exist")
                else:
                    text = page.text
                    newtext = fix_page(text, altepcode)
                    if newtext != text:
                        page.text = newtext
                        page.save("Bot: fixing altepcodes")


# invoke main function
if __name__ == "__main__":
    main()
