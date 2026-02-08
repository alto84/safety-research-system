#!/usr/bin/env python3
"""
Enhanced FAERS Query Tool for CAR-T Products

Queries the openFDA FAERS API for all 6 approved CAR-T products,
extracts adverse event profiles for each product separately, and
compares AE profiles between products.

Author: Safety Research System
Date: 2026-02-08
"""

import json
import time
import os
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import HTTPError, URLError

BASE_URL = "https://api.fda.gov/drug/event.json"

# All FDA-approved CAR-T products
CAR_T_PRODUCTS = {
    "Yescarta": {
        "generic": "axicabtagene ciloleucel",
        "brand": "YESCARTA",
        "target": "CD19",
        "manufacturer": "Kite/Gilead",
        "approval_date": "2017-10-18",
        "indications": "DLBCL, PMBCL, follicular lymphoma",
    },
    "Kymriah": {
        "generic": "tisagenlecleucel",
        "brand": "KYMRIAH",
        "target": "CD19",
        "manufacturer": "Novartis",
        "approval_date": "2017-08-30",
        "indications": "B-ALL, DLBCL, follicular lymphoma",
    },
    "Tecartus": {
        "generic": "brexucabtagene autoleucel",
        "brand": "TECARTUS",
        "target": "CD19",
        "manufacturer": "Kite/Gilead",
        "approval_date": "2020-07-24",
        "indications": "MCL, B-ALL",
    },
    "Breyanzi": {
        "generic": "lisocabtagene maraleucel",
        "brand": "BREYANZI",
        "target": "CD19",
        "manufacturer": "Bristol Myers Squibb",
        "approval_date": "2021-02-05",
        "indications": "LBCL",
    },
    "Abecma": {
        "generic": "idecabtagene vicleucel",
        "brand": "ABECMA",
        "target": "BCMA",
        "manufacturer": "Bristol Myers Squibb",
        "approval_date": "2021-03-26",
        "indications": "Multiple myeloma",
    },
    "Carvykti": {
        "generic": "ciltacabtagene autoleucel",
        "brand": "CARVYKTI",
        "target": "BCMA",
        "manufacturer": "Janssen/Legend",
        "approval_date": "2022-02-28",
        "indications": "Multiple myeloma",
    },
}

# Key adverse events of interest for CAR-T
KEY_ADVERSE_EVENTS = [
    "Cytokine release syndrome",
    "Cytokine storm",
    "Neurotoxicity",
    "Immune effector cell-associated neurotoxicity syndrome",
    "Encephalopathy",
    "Cerebral oedema",
    "Febrile neutropenia",
    "Neutropenia",
    "Thrombocytopenia",
    "Anaemia",
    "Hypogammaglobulinaemia",
    "Infection",
    "Sepsis",
    "Pneumonia",
    "Pyrexia",
    "Hypotension",
    "Hypoxia",
    "Disseminated intravascular coagulation",
    "Tumour lysis syndrome",
    "Haemophagocytic lymphohistiocytosis",
    "Macrophage activation syndrome",
    "Graft versus host disease",
    "Death",
    "Cardiac arrest",
    "Multiple organ dysfunction syndrome",
    "Tremor",
    "Aphasia",
    "Seizure",
    "Confusional state",
    "Delirium",
    "T-cell lymphoma",
    "Myelodysplastic syndrome",
    "Acute myeloid leukaemia",
]


def api_request(url, max_retries=3):
    """Make a request to the openFDA API with a pre-constructed URL."""
    for attempt in range(max_retries):
        try:
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            if e.code == 404:
                # 404 means no matching results -- not an error
                return None
            print(f"  HTTP Error {e.code}: {e.reason} (attempt {attempt+1}/{max_retries})")
            if e.code == 429:
                time.sleep(10 * (attempt + 1))
            elif e.code >= 500:
                time.sleep(3 * (attempt + 1))
            else:
                return None
        except URLError as e:
            print(f"  URL Error: {e.reason} (attempt {attempt+1}/{max_retries})")
            time.sleep(3 * (attempt + 1))
    return None


def build_product_search(brand_name):
    """Build the search clause for a product using medicinalproduct field."""
    # Use medicinalproduct which contains the product name as reported
    # Upper case works best for brand names in FAERS
    return f'patient.drug.medicinalproduct:"{brand_name}"'


def get_total_reports(brand_name):
    """Get total number of AE reports for a product."""
    search = build_product_search(brand_name)
    url = f"{BASE_URL}?search={search}&limit=1"
    data = api_request(url)
    if data and "meta" in data:
        return data["meta"]["results"]["total"]
    return 0


def get_top_adverse_events(brand_name, limit=100):
    """Get top adverse events for a product."""
    search = build_product_search(brand_name)
    url = f"{BASE_URL}?search={search}&count=patient.reaction.reactionmeddrapt.exact&limit={limit}"
    data = api_request(url)
    if data and "results" in data:
        return data["results"]
    return []


def get_serious_outcomes(brand_name):
    """Get outcome distribution for a product (serious=1 vs not serious=2)."""
    search = build_product_search(brand_name)
    url = f"{BASE_URL}?search={search}&count=serious"
    data = api_request(url)
    if data and "results" in data:
        return data["results"]
    return []


def get_outcome_types(brand_name):
    """Get patient outcome types (death, hospitalization, etc)."""
    results = {}
    search = build_product_search(brand_name)

    # seriousnessdeath
    for field in ["seriousnessdeath", "seriousnesshospitalization",
                  "seriousnesslifethreatening", "seriousnessdisabling"]:
        url = f"{BASE_URL}?search={search}&count={field}"
        data = api_request(url)
        if data and "results" in data:
            results[field] = data["results"]
        time.sleep(0.2)

    return results


def get_sex_distribution(brand_name):
    """Get patient sex distribution."""
    search = build_product_search(brand_name)
    url = f"{BASE_URL}?search={search}&count=patient.patientsex"
    data = api_request(url)
    if data and "results" in data:
        sex_map = {1: "Male", 2: "Female", 0: "Unknown"}
        return [{
            "sex": sex_map.get(r.get("term", 0), "Unknown"),
            "count": r.get("count", 0)
        } for r in data["results"]]
    return []


def get_reporting_year_distribution(brand_name):
    """Get reporting date distribution."""
    search = build_product_search(brand_name)
    url = f"{BASE_URL}?search={search}&count=receivedate"
    data = api_request(url)
    if data and "results" in data:
        year_counts = {}
        for entry in data["results"]:
            year = str(entry.get("time", ""))[:4]
            if year:
                year_counts[year] = year_counts.get(year, 0) + entry.get("count", 0)
        return year_counts
    return {}


def get_reporter_type(brand_name):
    """Get reporter qualification breakdown."""
    search = build_product_search(brand_name)
    url = f"{BASE_URL}?search={search}&count=primarysource.qualification"
    data = api_request(url)
    qual_map = {1: "Physician", 2: "Pharmacist", 3: "Other Health Professional",
                4: "Lawyer", 5: "Consumer/Patient"}
    if data and "results" in data:
        return [{
            "qualification": qual_map.get(r.get("term", 0), "Unknown"),
            "count": r.get("count", 0)
        } for r in data["results"]]
    return []


def get_key_ae_counts(brand_name, total_reports):
    """Get counts for specific key adverse events."""
    results = {}
    search_base = build_product_search(brand_name)

    for ae_term in KEY_ADVERSE_EVENTS:
        ae_encoded = quote(ae_term, safe='')
        search = f'{search_base}+AND+patient.reaction.reactionmeddrapt:"{ae_encoded}"'
        url = f"{BASE_URL}?search={search}&limit=1"
        data = api_request(url)
        if data and "meta" in data:
            count = data["meta"]["results"]["total"]
            if count > 0:
                results[ae_term] = {
                    "count": count,
                    "rate_pct": round(count / total_reports * 100, 2) if total_reports > 0 else 0,
                }
        time.sleep(0.15)

    return results


def compare_products(product_profiles):
    """Compare AE profiles across all products."""
    comparison = {
        "total_reports_by_product": {},
        "top_ae_comparison_matrix": {},
        "crs_comparison": {},
        "neurotoxicity_comparison": {},
        "secondary_malignancy_comparison": {},
        "mortality_comparison": {},
        "infection_comparison": {},
        "cytopenia_comparison": {},
    }

    # Total reports
    for name, profile in product_profiles.items():
        comparison["total_reports_by_product"][name] = profile["total_reports"]

    # Build top AE comparison -- get top 20 AEs across all products
    all_top_aes = {}
    for name, profile in product_profiles.items():
        for ae in profile["top_adverse_events"][:30]:
            term = ae["term"]
            if term not in all_top_aes:
                all_top_aes[term] = {}
            total = profile["total_reports"]
            all_top_aes[term][name] = {
                "count": ae["count"],
                "rate_pct": round(ae["count"] / total * 100, 1) if total > 0 else 0,
            }

    # Sort by total count across products
    sorted_aes = sorted(
        all_top_aes.items(),
        key=lambda x: sum(v["count"] for v in x[1].values()),
        reverse=True,
    )
    for term, product_data in sorted_aes[:30]:
        row = {}
        for name in product_profiles:
            if name in product_data:
                row[name] = product_data[name]
            else:
                row[name] = {"count": 0, "rate_pct": 0}
        comparison["top_ae_comparison_matrix"][term] = row

    # CRS comparison
    crs_terms = ["Cytokine release syndrome", "Cytokine storm"]
    for name, profile in product_profiles.items():
        total = profile["total_reports"]
        crs_count = 0
        for term in crs_terms:
            if term in profile.get("key_ae_counts", {}):
                crs_count += profile["key_ae_counts"][term]["count"]
        comparison["crs_comparison"][name] = {
            "count": crs_count,
            "rate_pct": round(crs_count / total * 100, 2) if total > 0 else 0,
        }

    # Neurotoxicity comparison
    neuro_terms = ["Neurotoxicity", "Encephalopathy",
                   "Immune effector cell-associated neurotoxicity syndrome"]
    for name, profile in product_profiles.items():
        total = profile["total_reports"]
        neuro_count = 0
        for term in neuro_terms:
            if term in profile.get("key_ae_counts", {}):
                neuro_count += profile["key_ae_counts"][term]["count"]
        comparison["neurotoxicity_comparison"][name] = {
            "count": neuro_count,
            "rate_pct": round(neuro_count / total * 100, 2) if total > 0 else 0,
        }

    # Secondary malignancy comparison
    malig_terms = ["T-cell lymphoma", "Myelodysplastic syndrome", "Acute myeloid leukaemia"]
    for name, profile in product_profiles.items():
        total = profile["total_reports"]
        malig_count = 0
        for term in malig_terms:
            if term in profile.get("key_ae_counts", {}):
                malig_count += profile["key_ae_counts"][term]["count"]
        comparison["secondary_malignancy_comparison"][name] = {
            "count": malig_count,
            "rate_pct": round(malig_count / total * 100, 2) if total > 0 else 0,
        }

    # Mortality comparison
    for name, profile in product_profiles.items():
        total = profile["total_reports"]
        death_count = 0
        if "Death" in profile.get("key_ae_counts", {}):
            death_count = profile["key_ae_counts"]["Death"]["count"]
        comparison["mortality_comparison"][name] = {
            "count": death_count,
            "rate_pct": round(death_count / total * 100, 2) if total > 0 else 0,
        }

    # Infection comparison
    inf_terms = ["Infection", "Sepsis", "Pneumonia"]
    for name, profile in product_profiles.items():
        total = profile["total_reports"]
        inf_count = 0
        for term in inf_terms:
            if term in profile.get("key_ae_counts", {}):
                inf_count += profile["key_ae_counts"][term]["count"]
        comparison["infection_comparison"][name] = {
            "count": inf_count,
            "rate_pct": round(inf_count / total * 100, 2) if total > 0 else 0,
        }

    # Cytopenia comparison
    cyto_terms = ["Neutropenia", "Thrombocytopenia", "Anaemia", "Febrile neutropenia"]
    for name, profile in product_profiles.items():
        total = profile["total_reports"]
        cyto_count = 0
        for term in cyto_terms:
            if term in profile.get("key_ae_counts", {}):
                cyto_count += profile["key_ae_counts"][term]["count"]
        comparison["cytopenia_comparison"][name] = {
            "count": cyto_count,
            "rate_pct": round(cyto_count / total * 100, 2) if total > 0 else 0,
        }

    return comparison


def main():
    start_time = time.time()

    print("=" * 70)
    print("Enhanced FAERS Query Tool for CAR-T Products")
    print("=" * 70)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"\nQuerying openFDA FAERS for {len(CAR_T_PRODUCTS)} approved CAR-T products...")

    product_profiles = {}

    for product_name, product_info in CAR_T_PRODUCTS.items():
        print(f"\n{'='*60}")
        print(f"Processing: {product_name} ({product_info['generic']})")
        print(f"  Target: {product_info['target']}")
        print(f"  Manufacturer: {product_info['manufacturer']}")
        print(f"  Approved: {product_info['approval_date']}")
        print(f"  Indications: {product_info['indications']}")
        print(f"{'='*60}")

        brand = product_info["brand"]

        # Get total reports
        print(f"  Getting total report count...")
        total = get_total_reports(brand)
        print(f"  Total FAERS reports: {total}")
        time.sleep(0.3)

        if total == 0:
            print(f"  WARNING: No reports found for {brand}. Skipping detailed queries.")
            product_profiles[product_name] = {
                "product_name": product_name,
                "generic_name": product_info["generic"],
                "brand_name": brand,
                "target": product_info["target"],
                "manufacturer": product_info["manufacturer"],
                "approval_date": product_info["approval_date"],
                "total_reports": 0,
                "top_adverse_events": [],
                "serious_outcomes": [],
                "outcome_types": {},
                "sex_distribution": [],
                "reporting_by_year": {},
                "reporter_type": [],
                "key_ae_counts": {},
            }
            continue

        # Get top adverse events
        print(f"  Getting top adverse events...")
        top_aes = get_top_adverse_events(brand, limit=100)
        print(f"  Found {len(top_aes)} unique adverse event terms")
        time.sleep(0.3)

        # Get serious outcome distribution
        print(f"  Getting outcome seriousness...")
        serious = get_serious_outcomes(brand)
        time.sleep(0.3)

        # Get outcome types
        print(f"  Getting outcome types (death, hospitalization, etc.)...")
        outcome_types = get_outcome_types(brand)
        time.sleep(0.3)

        # Get sex distribution
        print(f"  Getting patient demographics...")
        sex_dist = get_sex_distribution(brand)
        time.sleep(0.3)

        # Get reporting year distribution
        print(f"  Getting reporting trends...")
        year_dist = get_reporting_year_distribution(brand)
        time.sleep(0.3)

        # Get reporter type
        print(f"  Getting reporter qualifications...")
        reporter = get_reporter_type(brand)
        time.sleep(0.3)

        # Get key AE counts
        print(f"  Getting key CAR-T adverse event counts (searching {len(KEY_ADVERSE_EVENTS)} terms)...")
        key_aes = get_key_ae_counts(brand, total)
        print(f"  Found {len(key_aes)} key AEs with reports")

        profile = {
            "product_name": product_name,
            "generic_name": product_info["generic"],
            "brand_name": brand,
            "target": product_info["target"],
            "manufacturer": product_info["manufacturer"],
            "approval_date": product_info["approval_date"],
            "total_reports": total,
            "top_adverse_events": top_aes,
            "serious_outcomes": serious,
            "outcome_types": outcome_types,
            "sex_distribution": sex_dist,
            "reporting_by_year": year_dist,
            "reporter_type": reporter,
            "key_ae_counts": key_aes,
        }

        product_profiles[product_name] = profile

        # Print top 10 AEs
        if top_aes:
            print(f"\n  Top 10 Adverse Events for {product_name}:")
            for i, ae in enumerate(top_aes[:10]):
                pct = round(ae["count"] / total * 100, 1) if total > 0 else 0
                print(f"    {i+1}. {ae['term']} ({ae['count']} reports, {pct}%)")

        # Print key CAR-T AEs
        if key_aes:
            print(f"\n  Key CAR-T Adverse Events:")
            sorted_key = sorted(key_aes.items(), key=lambda x: x[1]["count"], reverse=True)
            for ae_term, ae_data in sorted_key[:10]:
                print(f"    - {ae_term}: {ae_data['count']} ({ae_data['rate_pct']}%)")

    # Compare products
    print(f"\n{'='*70}")
    print("PRODUCT COMPARISON")
    print(f"{'='*70}")

    comparison = compare_products(product_profiles)

    print(f"\nTotal Reports by Product:")
    for name, count in sorted(comparison["total_reports_by_product"].items(),
                               key=lambda x: x[1], reverse=True):
        print(f"  {name}: {count:,}")

    print(f"\nCRS Reporting Rates:")
    for name, data in sorted(comparison["crs_comparison"].items(),
                              key=lambda x: x[1]["rate_pct"], reverse=True):
        print(f"  {name}: {data['count']:,} reports ({data['rate_pct']}%)")

    print(f"\nNeurotoxicity Reporting Rates:")
    for name, data in sorted(comparison["neurotoxicity_comparison"].items(),
                              key=lambda x: x[1]["rate_pct"], reverse=True):
        print(f"  {name}: {data['count']:,} reports ({data['rate_pct']}%)")

    print(f"\nSecondary Malignancy Reporting Rates:")
    for name, data in sorted(comparison["secondary_malignancy_comparison"].items(),
                              key=lambda x: x[1]["rate_pct"], reverse=True):
        print(f"  {name}: {data['count']:,} reports ({data['rate_pct']}%)")

    print(f"\nMortality Reporting Rates:")
    for name, data in sorted(comparison["mortality_comparison"].items(),
                              key=lambda x: x[1]["rate_pct"], reverse=True):
        print(f"  {name}: {data['count']:,} reports ({data['rate_pct']}%)")

    print(f"\nInfection Reporting Rates:")
    for name, data in sorted(comparison["infection_comparison"].items(),
                              key=lambda x: x[1]["rate_pct"], reverse=True):
        print(f"  {name}: {data['count']:,} reports ({data['rate_pct']}%)")

    print(f"\nCytopenia Reporting Rates:")
    for name, data in sorted(comparison["cytopenia_comparison"].items(),
                              key=lambda x: x[1]["rate_pct"], reverse=True):
        print(f"  {name}: {data['count']:,} reports ({data['rate_pct']}%)")

    # Build output
    output = {
        "metadata": {
            "extraction_date": datetime.now().isoformat(),
            "source": "openFDA FAERS API",
            "api_endpoint": BASE_URL,
            "products_queried": list(CAR_T_PRODUCTS.keys()),
            "key_adverse_events_searched": KEY_ADVERSE_EVENTS,
            "runtime_seconds": round(time.time() - start_time, 1),
        },
        "product_profiles": product_profiles,
        "comparison": comparison,
    }

    # Save results
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, "faers_product_comparison.json")

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n\nResults saved to: {output_path}")
    print(f"Runtime: {round(time.time() - start_time, 1)} seconds")
    print("Done.")


if __name__ == "__main__":
    main()
