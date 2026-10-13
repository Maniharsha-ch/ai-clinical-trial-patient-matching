import json
from pathlib import Path


DATA = Path(__file__).parent / "data" / "cohort.json"


def load_cohort():
    return json.loads(DATA.read_text(encoding="utf-8"))


def percentage(count, total):
    if total == 0:
        return 0

    return round((count / total) * 100)


def analyze_diversity():

    patients = load_cohort()
    total = len(patients)

    female = sum(
        1 for p in patients
        if p["sex"].lower() == "female"
    )

    male = sum(
        1 for p in patients
        if p["sex"].lower() == "male"
    )

    young = sum(
        1 for p in patients
        if p["age"] < 40
    )

    middle = sum(
        1 for p in patients
        if 40 <= p["age"] < 60
    )

    older = sum(
        1 for p in patients
        if p["age"] >= 60
    )

    locations = {}

    for patient in patients:

        location = patient["location"]

        if location not in locations:
            locations[location] = 0

        locations[location] += 1

    location_percentages = {}

    for location, count in locations.items():

        location_percentages[location] = percentage(
            count,
            total
        )

    gaps = []

    if percentage(female, total) < 40:
        gaps.append("Female participants")

    if percentage(young, total) < 25:
        gaps.append("Participants aged 18–39")

    if len(locations) < 3:
        gaps.append("Geographic representation")

    return {
        "total_candidates": total,

        "gender": {
            "female": percentage(female, total),
            "male": percentage(male, total)
        },

        "age_groups": {
            "18_39": percentage(young, total),
            "40_59": percentage(middle, total),
            "60_plus": percentage(older, total)
        },

        "locations": location_percentages,

        "recruitment_gaps": gaps
    }