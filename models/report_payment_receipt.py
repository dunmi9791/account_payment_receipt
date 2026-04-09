# -*- coding: utf-8 -*-
from odoo import api, models


class ReportPaymentReceipt(models.AbstractModel):
    """
    Abstract model that provides custom data for the payment receipt report.

    The report name MUST match: report.<module>.<report_name>
    where <report_name> is the `name` attribute on the <report> tag.
    Here: report.account_payment_receipt.report_payment_receipt
    """
    _name = 'report.account_payment_receipt.report_payment_receipt'
    _description = 'Payment Receipt Report'

    # ------------------------------------------------------------------
    # Public API – called by Odoo's report engine
    # ------------------------------------------------------------------

    @api.model
    def _get_report_values(self, docids, data=None):
        """Return all values needed by the QWeb template."""
        payments = self.env['account.payment'].browse(docids)

        report_data = {}
        for payment in payments:
            balance_before, balance_after = self._compute_balances(payment)
            reconciled_docs = self._get_reconciled_documents(payment)

            report_data[payment.id] = {
                'balance_before': balance_before,
                'balance_after': max(balance_after, 0.0),
                'reconciled_docs': reconciled_docs,
            }

        return {
            'docs': payments,
            'report_data': report_data,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_balances(self, payment):
        """
        Compute the partner's outstanding balance BEFORE and AFTER the payment.

        Strategy
        --------
        We sum (debit – credit) of all *posted* journal items on the partner's
        receivable (inbound) or payable (outbound) account, limited to entries
        whose date is <= payment.date and whose source move is NOT the payment
        move itself.  This gives us the balance that existed just before the
        payment hit the ledger.

        The balance_after is simply balance_before minus the payment amount
        (for inbound receipts the receivable goes down; for outbound the
        payable goes down from the vendor's perspective, which we also show
        as a reduction).

        Returns a tuple (balance_before, balance_after) as positive floats.
        """
        partner = payment.partner_id.commercial_partner_id
        all_partner_ids = [partner.id] + partner.child_ids.ids

        if payment.payment_type == 'inbound':
            account_type = 'asset_receivable'
            # receivable: debit = invoice charge, credit = payment → debit-credit is positive when partner owes us
            sign = 1
        else:
            account_type = 'liability_payable'
            # payable: credit = vendor bill, debit = payment → credit-debit is positive when we owe vendor
            sign = -1

        domain = [
            ('partner_id', 'in', all_partner_ids),
            ('account_id.account_type', '=', account_type),
            ('company_id', '=', payment.company_id.id),
            ('parent_state', '=', 'posted'),
            ('date', '<=', payment.date),
            ('move_id', '!=', payment.move_id.id),   # exclude this payment's own JE
        ]

        lines = self.env['account.move.line'].search(domain)
        balance_before = sign * sum(line.debit - line.credit for line in lines)

        # Ensure balance_before is never negative in the display
        balance_before = max(balance_before, 0.0)
        balance_after = balance_before - payment.amount

        return balance_before, balance_after

    @staticmethod
    def _get_reconciled_documents(payment):
        """
        Return the invoices (for inbound) or bills (for outbound) that were
        reconciled with this payment, together with the amount applied.

        Returns a list of dicts:
            [{
                'name': str,        – invoice/bill reference
                'date': date,
                'amount_total': float,
                'amount_residual': float,  – remaining after this payment
                'amount_applied': float,   – amount settled by this payment
                'currency': res.currency,
            }, ...]
        """
        result = []

        if payment.payment_type == 'inbound':
            docs = payment.reconciled_invoice_ids
        else:
            docs = payment.reconciled_bill_ids

        for doc in docs:
            # amount_applied = original total - current residual
            # (works correctly even when partially reconciled)
            amount_applied = doc.amount_total - doc.amount_residual
            result.append({
                'name': doc.name or '/',
                'date': doc.invoice_date,
                'amount_total': doc.amount_total,
                'amount_residual': doc.amount_residual,
                'amount_applied': amount_applied,
                'currency': doc.currency_id,
            })

        return result
