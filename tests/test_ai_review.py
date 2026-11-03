import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ai_review


class ReviewTests(unittest.TestCase):
    def test_diff_budget_and_missing_patch(self):
        files = [
            {'filename': 'binary.png', 'status': 'added'},
            {'filename': 'large.java', 'status': 'modified', 'patch': 'x' * 40_001},
            {'filename': 'app/A.java', 'status': 'modified', 'patch': '@@ -1 +1 @@\n-old\n+new'},
        ]
        selected, omitted = ai_review.collect_diff(files)
        self.assertEqual([f['file'] for f in selected], ['app/A.java'])
        self.assertEqual(omitted, ['binary.png', 'large.java'])

    def test_response_and_request_limits(self):
        response = {'status': 'completed', 'output': [
            {'type': 'reasoning'},
            {'type': 'message', 'content': [{'type': 'output_text', 'text': 'Check @team'}]},
        ]}
        with patch('ai_review.request_json', return_value=response) as api:
            result = ai_review.generate_review([{'patch': '+code'}], 'fake', 'model')
        self.assertNotIn('@team', result)
        payload = api.call_args.args[2]
        self.assertFalse(payload['store'])
        self.assertEqual(payload['max_output_tokens'], 2500)
        self.assertNotIn('tools', payload)

    def test_incomplete_response_is_not_a_success(self):
        with patch('ai_review.request_json', return_value={'status': 'incomplete'}):
            with self.assertRaises(ValueError):
                ai_review.generate_review([], 'fake', 'model')

    def test_missing_secret_does_not_call_network(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            with patch('ai_review.request_json') as api:
                ai_review.main()
        api.assert_not_called()

    def run_review(self, existing=False, stale=False, fork=False, fail=False):
        event = {'pull_request': {
            'number': 7, 'changed_files': 1,
            'head': {'sha': 'abc123', 'repo': {'full_name': 'other/repo' if fork else 'demo/repo'}},
        }}
        writes = []
        checks = 0

        def api(url, token, payload=None, method=None):
            nonlocal checks
            if url.endswith('/responses'):
                if fail:
                    raise ValueError('Invalid model response')
                return {'status': 'completed', 'output': [{'type': 'message', 'content': [
                    {'type': 'output_text', 'text': 'Znaleziono SQL injection.'}]}]}
            if method:
                writes.append((url, method, payload['body']))
                return {}
            if '/files?' in url:
                return [{'filename': 'app/A.java', 'status': 'modified', 'patch': '+unsafe'}]
            if '/comments?' in url:
                # An unrelated user's forged marker must not be updated.
                comments = [{'id': 5, 'user': {'login': 'someone'}, 'body': ai_review.MARKER}]
                if existing:
                    comments.append({'id': 9, 'user': {'login': 'github-actions[bot]'},
                                     'body': ai_review.MARKER + '\nold'})
                return comments
            checks += 1
            return {'state': 'open', 'head': {'sha': 'new' if stale and checks == 3 else 'abc123'}}

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'event.json'
            path.write_text(json.dumps(event))
            with patch.dict(os.environ, {
                'OPENAI_API_KEY': 'fake', 'GITHUB_TOKEN': 'fake',
                'GITHUB_REPOSITORY': 'demo/repo', 'GITHUB_EVENT_PATH': str(path),
            }):
                with patch('ai_review.request_json', side_effect=api) as mocked:
                    if fail:
                        with self.assertRaises(ValueError):
                            ai_review.main()
                    else:
                        ai_review.main()
                    if fork:
                        mocked.assert_not_called()
        return writes

    def test_creates_comment(self):
        writes = self.run_review()
        self.assertEqual(len(writes), 1)
        self.assertTrue(writes[0][0].endswith('/issues/7/comments'))
        self.assertEqual(writes[0][1], 'POST')
        self.assertIn('abc123', writes[0][2])

    def test_updates_existing_bot_comment(self):
        writes = self.run_review(existing=True)
        self.assertEqual(len(writes), 1)
        self.assertTrue(writes[0][0].endswith('/issues/comments/9'))
        self.assertEqual(writes[0][1], 'PATCH')

    def test_discards_review_for_outdated_commit(self):
        self.assertEqual(self.run_review(stale=True), [])

    def test_fork_does_not_call_network(self):
        self.assertEqual(self.run_review(fork=True), [])

    def test_api_failure_does_not_publish_review(self):
        self.assertEqual(self.run_review(fail=True), [])


if __name__ == '__main__':
    unittest.main()
