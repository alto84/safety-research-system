#!/usr/bin/env python3
"""
ClinicalTrials.gov CAR-T Cell Therapy Adverse Event Extractor

Queries ClinicalTrials.gov API v2 for completed CAR-T cell therapy trials,
extracts adverse event data from structured results, and outputs a summary.

Author: Safety Research System
Date: 2026-02-08
"""

import json
import time
import sys
import os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from urllib.error import HTTPError, URLError

BASE_URL = "https://clinicaltrials.gov/api/v2"


def api_request(endpoint, params=None, max_retries=3):
    """Make a request to the ClinicalTrials.gov API v2."""
    url = f"{BASE_URL}/{endpoint}"
    if params:
        url += "?" + urlencode(params, quote_via=quote)

    for attempt in range(max_retries):
        try:
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            print(f"  HTTP Error {e.code}: {e.reason} (attempt {attempt+1}/{max_retries})")
            if e.code == 429:
                time.sleep(5 * (attempt + 1))
            elif e.code >= 500:
                time.sleep(2 * (attempt + 1))
            else:
                raise
        except URLError as e:
            print(f"  URL Error: {e.reason} (attempt {attempt+1}/{max_retries})")
            time.sleep(2 * (attempt + 1))

    return None


def search_completed_cart_trials():
    """Search for completed CAR-T trials with results."""
    print("=" * 70)
    print("ClinicalTrials.gov CAR-T Adverse Event Extractor")
    print("=" * 70)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"\nSearching for completed CAR-T trials with results...")

    params = {
        "query.cond": "lymphoma OR leukemia OR myeloma OR cancer",
        "query.intr": "CAR-T OR CAR T OR chimeric antigen receptor",
        "filter.overallStatus": "COMPLETED",
        "pageSize": 100,
        "sort": "LastUpdatePostDate:desc",
    }

    all_studies = []
    page_token = None
    page_num = 0

    while True:
        page_num += 1
        if page_token:
            params["pageToken"] = page_token

        print(f"  Fetching page {page_num}...")
        data = api_request("studies", params)

        if data is None:
            print("  ERROR: Failed to fetch data from API")
            break

        studies = data.get("studies", [])
        if not studies:
            break

        all_studies.extend(studies)
        print(f"  Found {len(studies)} studies on this page (total: {len(all_studies)})")

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(0.5)

    print(f"\nTotal completed CAR-T trials found: {len(all_studies)}")
    return all_studies


def extract_adverse_events(nct_id):
    """Extract adverse events for a specific trial by fetching its full record."""
    params = {
        "query.term": nct_id,
    }

    data = api_request("studies", params)
    if data is None or not data.get("studies"):
        return None

    study = data["studies"][0]
    results = study.get("resultsSection", {})
    ae_module = results.get("adverseEventsModule", {})

    return ae_module if ae_module else None


def parse_ae_module(ae_module):
    """Parse the adverse events module into structured data."""
    if not ae_module:
        return None

    parsed = {
        "frequency_threshold": ae_module.get("frequencyThreshold", ""),
        "time_frame": ae_module.get("timeFrame", ""),
        "description": ae_module.get("description", ""),
    }

    # Parse event groups (treatment arms)
    event_groups = []
    for group in ae_module.get("eventGroups", []):
        event_groups.append({
            "id": group.get("id", ""),
            "title": group.get("title", ""),
            "description": group.get("description", ""),
            "deaths_all_causes": group.get("deathsNumAffected", 0),
            "deaths_all_causes_at_risk": group.get("deathsNumAtRisk", 0),
            "serious_num_affected": group.get("seriousNumAffected", 0),
            "serious_num_at_risk": group.get("seriousNumAtRisk", 0),
            "other_num_affected": group.get("otherNumAffected", 0),
            "other_num_at_risk": group.get("otherNumAtRisk", 0),
        })
    parsed["event_groups"] = event_groups

    # Parse serious adverse events
    serious_events = []
    for event in ae_module.get("seriousEvents", []):
        term = event.get("term", "Unknown")
        organ = event.get("organSystem", "Unknown")
        stats = []
        for stat in event.get("stats", []):
            stats.append({
                "group_id": stat.get("groupId", ""),
                "num_affected": stat.get("numAffected", 0),
                "num_at_risk": stat.get("numAtRisk", 0),
                "num_events": stat.get("numEvents", 0),
            })
        serious_events.append({
            "term": term,
            "organ_system": organ,
            "stats": stats,
        })
    parsed["serious_events"] = serious_events

    # Parse other (non-serious) adverse events
    other_events = []
    for event in ae_module.get("otherEvents", []):
        term = event.get("term", "Unknown")
        organ = event.get("organSystem", "Unknown")
        stats = []
        for stat in event.get("stats", []):
            stats.append({
                "group_id": stat.get("groupId", ""),
                "num_affected": stat.get("numAffected", 0),
                "num_at_risk": stat.get("numAtRisk", 0),
                "num_events": stat.get("numEvents", 0),
            })
        other_events.append({
            "term": term,
            "organ_system": organ,
            "stats": stats,
        })
    parsed["other_events"] = other_events

    return parsed


def summarize_ae_data(all_ae_data):
    """Generate summary statistics across all trials."""
    summary = {
        "total_trials_with_ae_data": 0,
        "total_serious_event_types": set(),
        "total_other_event_types": set(),
        "crs_related_events": [],
        "icans_related_events": [],
        "common_serious_events": {},
        "common_other_events": {},
    }

    # CRS-related MedDRA terms
    crs_terms = [
        "cytokine release syndrome", "cytokine storm", "crs",
        "systemic inflammatory response", "capillary leak",
        "hypotension", "hypoxia", "fever", "pyrexia",
        "tachycardia", "disseminated intravascular coagulation",
    ]

    # ICANS-related terms
    icans_terms = [
        "neurotoxicity", "encephalopathy", "confusion",
        "aphasia", "tremor", "seizure", "cerebral oedema",
        "cerebral edema", "immune effector cell-associated neurotoxicity",
        "icans", "delirium", "agitation", "somnolence",
        "headache", "dizziness",
    ]

    for trial_data in all_ae_data:
        ae = trial_data.get("adverse_events")
        if not ae:
            continue

        summary["total_trials_with_ae_data"] += 1

        for event in ae.get("serious_events", []):
            term = event["term"].lower()
            summary["total_serious_event_types"].add(event["term"])

            total_affected = sum(s.get("num_affected", 0) for s in event.get("stats", []))
            if event["term"] not in summary["common_serious_events"]:
                summary["common_serious_events"][event["term"]] = {
                    "count_trials": 0,
                    "total_affected": 0,
                }
            summary["common_serious_events"][event["term"]]["count_trials"] += 1
            summary["common_serious_events"][event["term"]]["total_affected"] += total_affected

            if any(crs in term for crs in crs_terms):
                summary["crs_related_events"].append({
                    "term": event["term"],
                    "trial": trial_data["nct_id"],
                    "total_affected": total_affected,
                })

            if any(icans in term for icans in icans_terms):
                summary["icans_related_events"].append({
                    "term": event["term"],
                    "trial": trial_data["nct_id"],
                    "total_affected": total_affected,
                })

        for event in ae.get("other_events", []):
            summary["total_other_event_types"].add(event["term"])
            total_affected = sum(s.get("num_affected", 0) for s in event.get("stats", []))
            if event["term"] not in summary["common_other_events"]:
                summary["common_other_events"][event["term"]] = {
                    "count_trials": 0,
                    "total_affected": 0,
                }
            summary["common_other_events"][event["term"]]["count_trials"] += 1
            summary["common_other_events"][event["term"]]["total_affected"] += total_affected

    summary["total_serious_event_types"] = len(summary["total_serious_event_types"])
    summary["total_other_event_types"] = len(summary["total_other_event_types"])

    summary["top_serious_events"] = sorted(
        [{"term": k, **v} for k, v in summary["common_serious_events"].items()],
        key=lambda x: x["total_affected"],
        reverse=True,
    )[:30]

    summary["top_other_events"] = sorted(
        [{"term": k, **v} for k, v in summary["common_other_events"].items()],
        key=lambda x: x["total_affected"],
        reverse=True,
    )[:30]

    del summary["common_serious_events"]
    del summary["common_other_events"]

    return summary


def main():
    start_time = time.time()

    # Step 1: Search for completed CAR-T trials
    studies = search_completed_cart_trials()

    if not studies:
        print("No studies found. Exiting.")
        sys.exit(1)

    # Step 2: Gather trial metadata
    trial_list = []
    for study in studies:
        proto = study.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        design = proto.get("designModule", {})
        cond_module = proto.get("conditionsModule", {})
        interv_module = proto.get("armsInterventionsModule", {})

        has_results = study.get("hasResults", False)

        nct_id = ident.get("nctId", "")
        title = ident.get("briefTitle", "")
        phase_list = (design.get("phases") or ["N/A"])
        enrollment = design.get("enrollmentInfo", {}).get("count", 0)
        conditions = cond_module.get("conditions", [])

        interventions = []
        if interv_module:
            for interv in interv_module.get("interventions", []):
                interventions.append(interv.get("name", ""))

        trial_list.append({
            "nct_id": nct_id,
            "title": title,
            "phase": ", ".join(phase_list) if isinstance(phase_list, list) else str(phase_list),
            "enrollment": enrollment,
            "conditions": conditions,
            "interventions": interventions,
            "has_results": has_results,
        })

    results_count = sum(1 for t in trial_list if t["has_results"])
    no_results_count = sum(1 for t in trial_list if not t["has_results"])
    print(f"\nTrials with reported results: {results_count}")
    print(f"Trials without results: {no_results_count}")

    # Step 3: Extract adverse events from trials with results
    print("\n" + "=" * 70)
    print("Extracting adverse event data from trials with results...")
    print("=" * 70)

    all_ae_data = []
    trials_with_results = [t for t in trial_list if t["has_results"]]

    # Limit to first 50 to avoid excessive API calls
    max_extract = min(50, len(trials_with_results))
    print(f"\nExtracting AE data from {max_extract} of {len(trials_with_results)} trials with results...")

    for i, trial in enumerate(trials_with_results[:max_extract]):
        nct_id = trial["nct_id"]
        title_short = trial["title"][:60]
        print(f"\n[{i+1}/{max_extract}] {nct_id}: {title_short}...")

        ae_module = extract_adverse_events(nct_id)
        parsed = parse_ae_module(ae_module)

        trial_ae = {
            "nct_id": nct_id,
            "title": trial["title"],
            "phase": trial["phase"],
            "enrollment": trial["enrollment"],
            "conditions": trial["conditions"],
            "interventions": trial["interventions"],
            "adverse_events": parsed,
        }

        if parsed:
            n_serious = len(parsed.get("serious_events", []))
            n_other = len(parsed.get("other_events", []))
            n_groups = len(parsed.get("event_groups", []))
            print(f"  -> {n_serious} serious event types, {n_other} other event types, {n_groups} groups")
        else:
            print(f"  -> No structured AE data found")

        all_ae_data.append(trial_ae)
        time.sleep(0.3)

    # Step 4: Summarize
    print("\n" + "=" * 70)
    print("Generating summary...")
    print("=" * 70)

    summary = summarize_ae_data(all_ae_data)

    output = {
        "metadata": {
            "extraction_date": datetime.now().isoformat(),
            "source": "ClinicalTrials.gov API v2",
            "search_strategy": "Completed CAR-T cell therapy trials with structured results",
            "total_trials_found": len(trial_list),
            "trials_with_results": len(trials_with_results),
            "trials_with_ae_data": summary["total_trials_with_ae_data"],
            "trials_extracted": max_extract,
            "runtime_seconds": round(time.time() - start_time, 1),
        },
        "summary": {
            "total_trials_with_ae_data": summary["total_trials_with_ae_data"],
            "unique_serious_event_types": summary["total_serious_event_types"],
            "unique_other_event_types": summary["total_other_event_types"],
            "crs_related_events_found": len(summary["crs_related_events"]),
            "icans_related_events_found": len(summary["icans_related_events"]),
        },
        "crs_related_events": summary["crs_related_events"],
        "icans_related_events": summary["icans_related_events"],
        "top_serious_events": summary["top_serious_events"],
        "top_other_events": summary["top_other_events"],
        "trial_details": all_ae_data,
    }

    # Step 5: Save results
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, "ct_gov_ae_data.json")

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nResults saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"Total trials found:           {len(trial_list)}")
    print(f"Trials with posted results:   {len(trials_with_results)}")
    print(f"Trials with AE data:          {summary['total_trials_with_ae_data']}")
    print(f"Unique serious event types:   {summary['total_serious_event_types']}")
    print(f"Unique other event types:     {summary['total_other_event_types']}")
    print(f"CRS-related events found:     {len(summary['crs_related_events'])}")
    print(f"ICANS-related events found:   {len(summary['icans_related_events'])}")

    if summary["top_serious_events"]:
        print(f"\nTop 10 Serious Adverse Events (by total affected):")
        for i, evt in enumerate(summary["top_serious_events"][:10]):
            print(f"  {i+1}. {evt['term']} (affected: {evt['total_affected']}, in {evt['count_trials']} trials)")

    if summary["crs_related_events"]:
        print(f"\nCRS-Related Events:")
        for evt in summary["crs_related_events"][:10]:
            print(f"  - {evt['term']} in {evt['trial']} (affected: {evt['total_affected']})")

    if summary["icans_related_events"]:
        print(f"\nICANS-Related Events:")
        for evt in summary["icans_related_events"][:10]:
            print(f"  - {evt['term']} in {evt['trial']} (affected: {evt['total_affected']})")

    print(f"\nRuntime: {round(time.time() - start_time, 1)} seconds")
    print("Done.")


if __name__ == "__main__":
    main()
