import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "update_ortho_course_radar.py"
SPEC = importlib.util.spec_from_file_location("ortho_radar", SCRIPT)
RADAR = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = RADAR
SPEC.loader.exec_module(RADAR)


class NassParserTests(unittest.TestCase):
    def test_listing_parses_all_current_events_from_authoritative_columns(self):
        html = """
        <table>
          <tr class="table-row"><td>Bertolotti Syndrome: Interventional and Surgical Evaluation, Management, and Treatment</td><td>September 15, 2026</td><td>Webinar Virtual</td><td><a href="/bertolotti">Details</a></td><td>Long description containing arthroplasty, lab and other unrelated keywords.</td></tr>
          <tr class="table-row"><td>From Awareness to Action: Bone Health Optimization, Osteoporosis Education, and Secondary Fracture Prevention in Spine Care—The National Spine Health Foundation Approach</td><td>September 24, 2026</td><td>Webinar Virtual</td><td><a href="/bone-health">Details</a></td></tr>
          <tr class="table-row"><td>Interdisciplinary Approach to Evaluating Lumbopelvic Pain in Athletes</td><td>October 6, 2026</td><td>Webinar Virtual</td><td><a href="/lumbopelvic">Details</a></td></tr>
          <tr class="table-row"><td>Coding Update 2026</td><td>October 12-13, 2026</td><td>San Antonio, TX</td><td><a href="/coding">Details</a></td></tr>
          <tr class="table-row"><td>2026 NASS Annual Meeting</td><td>October 14-17, 2026</td><td>San Antonio, TX</td><td><a href="http://www.spine.org/am">Details</a></td></tr>
          <tr class="table-row"><td>NASS Advanced Practice Provider Course: Bridging the Gap in Comprehensive Spine Care</td><td>October 17, 2026</td><td>San Antonio, TX</td><td><a href="/app">Details</a></td></tr>
          <tr class="table-row"><td>2026 Biologic Interventions for Spinal Pathologies</td><td>November 13, 2026</td><td>Nashville, TN</td><td><a href="/biologics">Details</a></td></tr>
          <tr class="table-row"><td>2027 Spine Across the Sea</td><td>July 25-29, 2027</td><td>Lahaina, HI</td><td><a href="/sats">Details</a></td></tr>
          <tr class="table-row"><td>OnDemand Archive</td><td>OnDemand</td><td></td><td><a href="/archive">Details</a></td></tr>
        </table>
        """
        events = RADAR.parse_nass_listing(html, "https://www.spine.org/Education/Courses-Conferences")
        self.assertEqual(len(events), 8)
        self.assertEqual(events[0]["title"], "Bertolotti Syndrome: Interventional and Surgical Evaluation, Management, and Treatment")
        self.assertEqual(events[0]["date"], "2026-09-15")
        self.assertEqual(events[0]["cat"], "脊椎")
        self.assertEqual(events[0]["mode"], "線上")
        self.assertEqual(events[0]["place"], "線上")
        self.assertEqual(events[3]["end_date"], "2026-10-13")
        self.assertEqual(events[4]["title"], "2026 NASS Annual Meeting")
        self.assertEqual(events[4]["end_date"], "2026-10-17")
        self.assertEqual(events[6]["place"], "Nashville, TN")
        self.assertEqual(events[7]["end_date"], "2027-07-29")

    def test_available_does_not_mean_lab(self):
        self.assertEqual(RADAR.mode("Recording available after the course"), "實體")

    def test_explicit_lab_still_means_lab(self):
        self.assertEqual(RADAR.mode("Spine cadaver lab"), "lab")

    def test_dated_listing_row_without_details_link_fails_loudly(self):
        html = '<tr class="table-row"><td>Future NASS Course</td><td>December 1, 2026</td><td>Chicago, IL</td><td></td></tr>'
        with self.assertRaises(ValueError):
            RADAR.parse_nass_listing(html, "https://www.spine.org/Education/Courses-Conferences")

    def test_generated_nass_records_are_normalized(self):
        text = (Path(__file__).parents[1] / "static" / "ortho-course-radar" / "events.js").read_text()
        rows = json.loads(re.search(r"= (\[.*\]);", text, re.S).group(1))
        nass = [row for row in rows if row["source"] == "NASS"]
        self.assertEqual(len(nass), 8)
        self.assertTrue(all(row["cat"] == "脊椎" for row in nass))
        self.assertTrue(all(len(row["place"]) < 100 for row in nass))
        self.assertTrue(all(not re.fullmatch(r"[A-Z][a-z]+ \d{1,2}(?:-\d{1,2})?, 20\d{2}", row["title"]) for row in nass))
        bertolotti = next(row for row in nass if "Bertolotti" in row["title"])
        self.assertEqual(bertolotti["mode"], "線上")
        awareness = next(row for row in nass if row["title"].startswith("From Awareness"))
        self.assertTrue(awareness["title"].endswith("Foundation Approach"))
        self.assertIn("2026 NASS Annual Meeting", {row["title"] for row in nass})
        self.assertIn("2026 Biologic Interventions for Spinal Pathologies", {row["title"] for row in nass})
        self.assertIn("2027 Spine Across the Sea", {row["title"] for row in nass})


if __name__ == "__main__":
    unittest.main()
