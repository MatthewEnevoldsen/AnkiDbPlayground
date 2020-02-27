import re

# "C:\Subs\One-Punch.Man\One-Punch.Man.S01E01.WEBRip.Netflix.ja[cc].vtt"

for file in originals:
    match = re.match("One-Punch.Man.S01E\d\d.WEBRip.Netflix.ja\[cc\].vtt", file)
    if match:
        print(file)
