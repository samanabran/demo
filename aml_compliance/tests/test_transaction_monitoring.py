from odoo.tests.common import TransactionCase
from datetime import timedelta
from odoo import fields


class TestTransactionAlert(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Alert Test Customer',
        })
        self.rule = self.env['aml.monitoring.rule'].create({
            'name': 'Test Threshold Rule',
            'code': 'TEST_THRESHOLD',
            'rule_type': 'threshold',
            'threshold_amount': 10000.0,
            'severity': 'medium',
        })

    def test_create_alert_on_threshold(self):
        """Alert created when amount exceeds threshold."""
        yesterday = fields.Datetime.now() - timedelta(days=1)
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'amount_total': 15000.0,
            'state': 'posted',
        })
        alert = self.env['aml.transaction.alert'].create({
            'rule_id': self.rule.id,
            'partner_id': self.partner.id,
            'transaction_amount': 15000.0,
            'invoice_id': invoice.id,
            'transaction_date': fields.Date.today(),
            'alert_description': 'Test threshold alert',
        })
        self.assertEqual(alert.state, 'new')
        self.assertEqual(alert.severity, 'medium')
        self.assertEqual(alert.transaction_amount, 15000.0)

    def test_alert_state_workflow(self):
        """Alert moves through investigation workflow correctly."""
        alert = self.env['aml.transaction.alert'].create({
            'rule_id': self.rule.id,
            'partner_id': self.partner.id,
            'transaction_amount': 20000.0,
        })
        self.assertEqual(alert.state, 'new')

        alert.action_investigate()
        self.assertEqual(alert.state, 'investigating')

        alert.action_escalate()
        self.assertEqual(alert.state, 'escalated')

    def test_false_positive_requires_notes(self):
        """Marking false positive requires investigation notes."""
        alert = self.env['aml.transaction.alert'].create({
            'rule_id': self.rule.id,
            'partner_id': self.partner.id,
            'transaction_amount': 20000.0,
        })
        alert.action_investigate()
        alert.write({'investigation_notes': 'Reviewed: false alarm'})
        alert.action_false_positive()
        self.assertEqual(alert.state, 'false_positive')
