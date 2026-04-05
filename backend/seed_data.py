"""Bulk insert employees from CSV data into InsForge DB."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from insforge_client import insert_rows

ROWS = [
    {"name":"Oliver Smith","level":"L2"," apr":[0.9,1.33,1.18],"pip":2,"joiningdate":"2025-05-22","gh_username":"osmith"},
    {"name":"George Jones","level":"L5"," apr":[0.86,0.83,0.81],"pip":1,"joiningdate":"2021-11-02","gh_username":"gjones"},
    {"name":"Harry Taylor","level":"L4"," apr":[1.61,1.18,1.66],"pip":2,"joiningdate":"2021-11-04","gh_username":"htaylor"},
    {"name":"Jack Brown","level":"L5"," apr":[0.51,1.1,1.31],"pip":1,"joiningdate":"2022-10-14","gh_username":"jack_brown"},
    {"name":"Jacob Williams","level":"L2"," apr":[0.92,1.19,1.11],"pip":3,"joiningdate":"2022-12-12","gh_username":"jacob-williams"},
    {"name":"Noah Wilson","level":"L3"," apr":[0.83,0.41,0.44],"pip":0,"joiningdate":"2024-03-26","gh_username":"noah39"},
    {"name":"Charlie Johnson","level":"L5"," apr":[1.06,0.14,0.22],"pip":3,"joiningdate":"2025-11-15","gh_username":"charlie_johnson"},
    {"name":"Thomas Davies","level":"L1"," apr":[1.03,1.28,1.16],"pip":2,"joiningdate":"2023-08-28","gh_username":"thomas-davies"},
    {"name":"Oscar Robinson","level":"L1"," apr":[0.4,1.52,0.82],"pip":2,"joiningdate":"2022-03-27","gh_username":"oscar.robinson"},
    {"name":"William Wright","level":"L5"," apr":[1.73,0.35,1.72],"pip":3,"joiningdate":"2023-07-05","gh_username":"william46"},
    {"name":"James Thompson","level":"L5"," apr":[1.14,1.29,1.93],"pip":0,"joiningdate":"2023-09-28","gh_username":"james91"},
    {"name":"Henry Evans","level":"L3"," apr":[1.33,1.65,0.4],"pip":1,"joiningdate":"2021-05-26","gh_username":"hevans"},
    {"name":"Alfie Walker","level":"L4"," apr":[1.96,1.36,0.33],"pip":2,"joiningdate":"2023-05-24","gh_username":"alfie.walker"},
    {"name":"Leo White","level":"L1"," apr":[0.28,1.14,1.3],"pip":3,"joiningdate":"2022-02-12","gh_username":"leo_white"},
    {"name":"Freddie Roberts","level":"L4"," apr":[1.83,1.83,0.53],"pip":2,"joiningdate":"2020-06-28","gh_username":"froberts"},
    {"name":"Amelia Green","level":"L1"," apr":[2.0,0.75,0.17],"pip":1,"joiningdate":"2025-03-25","gh_username":"amelia_green"},
    {"name":"Olivia Hall","level":"L3"," apr":[1.56,0.93,1.31],"pip":2,"joiningdate":"2024-01-19","gh_username":"oliviahall"},
    {"name":"Emily Wood","level":"L5"," apr":[1.95,1.58,0.57],"pip":3,"joiningdate":"2020-06-27","gh_username":"emily15"},
    {"name":"Isla Jackson","level":"L2"," apr":[1.56,0.88,0.62],"pip":1,"joiningdate":"2025-05-25","gh_username":"isla.jackson"},
    {"name":"Ava Clarke","level":"L4"," apr":[0.49,1.46,1.9],"pip":3,"joiningdate":"2022-11-15","gh_username":"ava87"},
    {"name":"Jessica Harris","level":"L5"," apr":[0.95,1.64,0.63],"pip":0,"joiningdate":"2023-07-28","gh_username":"jessicaharris"},
    {"name":"Poppy Lewis","level":"L1"," apr":[1.32,1.22,1.55],"pip":3,"joiningdate":"2023-07-29","gh_username":"poppy_lewis"},
    {"name":"Sophie Martin","level":"L5"," apr":[1.51,0.94,1.49],"pip":2,"joiningdate":"2022-06-21","gh_username":"sophie82"},
    {"name":"Isabella Cooper","level":"L1"," apr":[0.9,0.19,0.49],"pip":0,"joiningdate":"2022-09-03","gh_username":"isabellacooper"},
    {"name":"Mia King","level":"L4"," apr":[0.01,1.63,0.5],"pip":2,"joiningdate":"2023-08-14","gh_username":"mia69"},
    {"name":"Charlotte Baker","level":"L4"," apr":[1.7,0.61,1.49],"pip":0,"joiningdate":"2023-05-31","gh_username":"charlotte_baker"},
    {"name":"Lily Hill","level":"L2"," apr":[0.4,0.26,1.96],"pip":2,"joiningdate":"2024-11-10","gh_username":"lilyhill"},
    {"name":"Grace Scott","level":"L4"," apr":[1.45,0.31,0.81],"pip":1,"joiningdate":"2024-01-20","gh_username":"grace_scott"},
    {"name":"Evie Adams","level":"L5"," apr":[1.07,0.22,1.39],"pip":0,"joiningdate":"2025-02-20","gh_username":"evie.adams"},
    {"name":"Sophia Campbell","level":"L1"," apr":[0.47,0.83,0.76],"pip":1,"joiningdate":"2024-07-22","gh_username":"sophia.campbell"},
    {"name":"Arthur Mitchell","level":"L3"," apr":[1.53,1.2,1.18],"pip":0,"joiningdate":"2022-06-28","gh_username":"arthurmitchell"},
    {"name":"Archie Turner","level":"L1"," apr":[0.7,1.5,0.7],"pip":3,"joiningdate":"2024-01-31","gh_username":"archieturner"},
    {"name":"Theodore Phillips","level":"L5"," apr":[0.46,1.02,1.87],"pip":3,"joiningdate":"2024-08-23","gh_username":"tphillips"},
    {"name":"Lucas Parker","level":"L4"," apr":[1.82,1.35,0.06],"pip":3,"joiningdate":"2024-08-02","gh_username":"lucasparker"},
    {"name":"Alexander Edwards","level":"L1"," apr":[1.8,1.36,0.75],"pip":3,"joiningdate":"2025-02-17","gh_username":"alexander79"},
    {"name":"Sebastian Collins","level":"L1"," apr":[0.73,1.42,1.83],"pip":2,"joiningdate":"2025-07-20","gh_username":"sebastian.collins"},
    {"name":"Max Stewart","level":"L3"," apr":[0.55,1.15,1.95],"pip":2,"joiningdate":"2023-01-01","gh_username":"max-stewart"},
    {"name":"Benjamin Morris","level":"L5"," apr":[1.86,0.7,1.72],"pip":0,"joiningdate":"2023-06-09","gh_username":"bmorris"},
    {"name":"Edward Rogers","level":"L2"," apr":[0.28,1.18,0.24],"pip":3,"joiningdate":"2024-01-11","gh_username":"edwardrogers"},
    {"name":"Samuel Reed","level":"L3"," apr":[1.34,0.82,0.15],"pip":1,"joiningdate":"2023-06-15","gh_username":"samuel_reed"},
    {"name":"Daniel Cook","level":"L4"," apr":[1.41,0.09,1.8],"pip":0,"joiningdate":"2020-05-03","gh_username":"daniel.cook"},
    {"name":"Joseph Morgan","level":"L1"," apr":[0.86,1.64,0.24],"pip":2,"joiningdate":"2024-09-25","gh_username":"jmorgan"},
    {"name":"David Bell","level":"L3"," apr":[0.73,1.62,1.46],"pip":2,"joiningdate":"2025-11-24","gh_username":"david.bell"},
    {"name":"Matthew Murphy","level":"L4"," apr":[1.09,0.02,1.59],"pip":2,"joiningdate":"2024-07-08","gh_username":"matthew_murphy"},
    {"name":"Andrew Bailey","level":"L2"," apr":[1.1,0.29,1.1],"pip":3,"joiningdate":"2024-11-12","gh_username":"andrewbailey"},
]

if __name__ == "__main__":
    print(f"Inserting {len(ROWS)} employees...")
    # InsForge expects JSON-compatible values — apr is already a Python list
    # which httpx will serialize to a JSON array
    result = insert_rows("users", ROWS)
    print(f"Done! Inserted {len(result)} rows.")
