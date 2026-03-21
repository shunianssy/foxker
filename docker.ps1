# Foxker Docker Proxy Script
param([Parameter(ValueFromRemainingArguments)]$Args)
python "S:\foxker\foxker\cli.py" @Args
