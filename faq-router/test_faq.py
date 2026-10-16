import tempfile
import unittest
from pathlib import Path
from faq import Router, PayloadConflict

FAQ = {'hours': 'Open Monday to Friday, 09:00-17:00.'}


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.path = Path(self.tmp.name) / 'state.sqlite'
        self.r = Router(self.path, FAQ)

    def tearDown(self):
        self.r.close()
        self.tmp.cleanup()

    def event(self, id='m1', text='hours', sender='synthetic-alice'):
        return {'id': id, 'sender': sender, 'text': text}

    def test_approved_answer_and_restart_dedup(self):
        self.assertEqual(self.r.ingest(self.event())['outcome'], 'queued')
        self.r.close()
        self.r = Router(self.path, FAQ)
        self.assertTrue(self.r.ingest(self.event())['duplicate'])
        self.assertEqual(len(self.r.snapshot()['outbox']), 1)
        item = self.r.take()
        self.assertEqual(item['answer'], FAQ['hours'])
        self.r.acknowledge_local(item['id'])
        self.assertIsNone(self.r.take())

    def test_changed_payload_conflict_rolls_back(self):
        self.r.ingest(self.event())
        before = self.r.snapshot()
        for changed in [self.event(text='STOP'), self.event(sender='synthetic-bob')]:
            with self.assertRaises(PayloadConflict):
                self.r.ingest(changed)
        self.assertEqual(self.r.snapshot(), before)

    def test_unknown_handoff_cancels_pending_and_suppresses(self):
        self.r.ingest(self.event())
        self.assertEqual(self.r.ingest(self.event('m2', 'unapproved question'))['outcome'], 'handoff')
        self.assertEqual(self.r.ingest(self.event('m3'))['outcome'], 'suppressed_handoff')
        self.assertIsNone(self.r.take())
        self.assertEqual(self.r.snapshot()['outbox'][0]['state'], 'cancelled')

    def test_stop_durable_suppression_and_other_sender_isolation(self):
        self.r.ingest(self.event())
        self.r.ingest(self.event('m2', '  STOP  '))
        self.r.close()
        self.r = Router(self.path, FAQ)
        self.assertEqual(self.r.ingest(self.event('m3'))['outcome'], 'suppressed_stopped')
        self.assertEqual(self.r.ingest(self.event('m4', sender='synthetic-bob'))['outcome'], 'queued')
        self.assertEqual(self.r.take()['sender'], 'synthetic-bob')
        self.assertIsNone(self.r.take())

    def test_two_connections_claim_queue_once(self):
        self.r.ingest(self.event())
        other = Router(self.path, FAQ)
        try:
            first = self.r.take()
            self.assertIsNotNone(first)
            self.assertIsNone(other.take())
            self.assertTrue(other.ingest(self.event())['duplicate'])
            self.assertEqual(len(other.snapshot()['outbox']), 1)
        finally:
            other.close()

    def test_unacknowledged_item_not_reissued_after_restart(self):
        self.r.ingest(self.event())
        self.r.take()
        self.r.close()
        self.r = Router(self.path, FAQ)
        self.assertIsNone(self.r.take())
        self.assertEqual(self.r.snapshot()['outbox'][0]['state'], 'processing')

    def test_invalid_event_leaves_no_records(self):
        for event in [{}, self.event(text=''), dict(self.event(), surprise=1)]:
            with self.assertRaises(ValueError):
                self.r.ingest(event)
        self.assertEqual(self.r.snapshot(), {'contacts': [], 'messages': [], 'outbox': []})


if __name__ == '__main__':
    unittest.main()
