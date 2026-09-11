import copy
import unittest
from unittest.mock import patch
from stockanalysis.frontend import research_content_review as review


class ResearchContentReviewTests(unittest.TestCase):
    def setUp(self):
        self.report = {key: 'stored' for key in review._FIELDS}
        self.report.update(key_points=['claim'], source_document_ids=['source-document-22'])
        self.record = {'status': 'needs_source_correction', 'human_approved': False, 'findings': [{'title': 'issue'}]}

    def test_only_exact_content_gets_record_without_approving_it(self):
        with patch.dict(review.REVIEW_RECORDS, {review.report_fingerprint(self.report): self.record}):
            result = review.content_review_for(self.report)
            self.assertEqual(result['status'], 'needs_source_correction')
            self.assertFalse(result['human_approved'])
            result['findings'][0]['title'] = 'mutation'
            self.assertEqual(review.content_review_for(self.report)['findings'][0]['title'], 'issue')

    def test_every_reviewed_field_change_invalidates_record(self):
        with patch.dict(review.REVIEW_RECORDS, {review.report_fingerprint(self.report): self.record}):
            for field in review._FIELDS:
                changed = copy.deepcopy(self.report)
                changed[field] = 'different'
                with self.subTest(field=field):
                    self.assertEqual(review.content_review_for(changed)['status'], 'not_recorded')

    def test_unrelated_display_metadata_does_not_change_report_identity(self):
        self.assertEqual(review.report_fingerprint(self.report), review.report_fingerprint({**self.report,'data_quality':{'status':'complete'}}))

    def test_unknown_reports_are_never_treated_as_verified(self):
        self.assertEqual(review.content_review_for({})['status'], 'not_recorded')
        self.assertFalse(review.content_review_for({})['human_approved'])
