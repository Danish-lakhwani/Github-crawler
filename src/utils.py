from datetime import datetime
import dateutil.parser

def parse_iso(dt_str):
    return dateutil.parser.isoparse(dt_str)
