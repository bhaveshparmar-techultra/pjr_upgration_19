from odoo import _, models
import toolz as T


class HrPayslipComponentReport(models.AbstractModel):
    _name = 'report.hr_extra_report.hr_payslip_component_report'
    _inherit = 'report.report_xlsx_dynamic.abstract'
    _description = "HR Payslip Report XLSX"

    def get_report_body(self, form_data):
        query = """
        WITH
        PARTNER_BANK AS (
          SELECT DISTINCT ON (PARTNER_ID)
            PARTNER_ID,
            RB.NAME
          FROM RES_PARTNER_BANK
          LEFT JOIN RES_BANK AS RB ON RB.ID = RES_PARTNER_BANK.BANK_ID
        ),
        MAIN_COMPONENT AS (
          SELECT
          HRP.NAME AS PAYSLIP_NAME,
          HRP.DATE_FROM AS PAYSLIP_DATE_FROM,
          HRE.NAME,
          SUM(ABS(HRPL.AMOUNT)) FILTER (WHERE HRSR.CODE = 'BASIC' ) AS BASIC_WAGE,
          COALESCE(SUM(ABS(HRPL.AMOUNT)) FILTER (WHERE HRSR.CODE = 'WORK_PERMIT' ),0) AS WORK_PERMIT,
          COALESCE(SUM(ABS(HRPL.AMOUNT)) FILTER (WHERE HRSR.CODE = 'CASH_ALLOWANCE' ),0) AS CASH_ALLOWANCE,
          COALESCE(SUM(ABS(HRPL.AMOUNT)) FILTER (WHERE HRSR.CODE = 'REIMBURSEMENT' ),0) AS REIMBURSEMENT,
          COALESCE(SUM(ABS(HRPL.AMOUNT)) FILTER (WHERE HRSR.CODE = 'LOAN' ),0) AS LOAN,
          COALESCE(SUM(ABS(HRPL.AMOUNT)) FILTER (WHERE HRSR.CODE IN ('EMP_INSURANCE_DED','FAMILY_INSURANCE_DED') ),0) AS INSURANCE,
          COALESCE(SUM(ABS(HRPL.AMOUNT)) FILTER (WHERE HRSR.CODE = 'DEDUCTION' ),0) AS OTHER_DEDUCTION,
          COALESCE(SUM(ABS(HRPL.AMOUNT)) FILTER (WHERE HRSR.CODE = 'LD3' ),0) AS ANNUAL,
          COALESCE(SUM(ABS(HRPL.AMOUNT)) FILTER (WHERE HRSR.CODE IN ('LD','LD2') ),0) AS UNPAID,
          COALESCE(SUM(ABS(HRPL.AMOUNT)) FILTER (WHERE HRSR.CODE = 'LD5' ),0) AS SICK,
          COALESCE(SPLIT_PART(STRING_AGG(PB.NAME, ', '),',',1),'') AS BANK_NAME
          FROM HR_PAYSLIP AS HRP
          LEFT JOIN HR_PAYSLIP_LINE AS HRPL ON HRPL.SLIP_ID = HRP.ID
          LEFT JOIN HR_SALARY_RULE AS HRSR ON HRSR.ID = HRPL.SALARY_RULE_ID
          LEFT JOIN HR_EMPLOYEE AS HRE ON HRE.ID = HRP.EMPLOYEE_ID
          LEFT JOIN RES_PARTNER AS RP ON RP.ID = HRE.WORK_CONTACT_ID
          LEFT JOIN PARTNER_BANK AS PB ON PB.PARTNER_ID = RP.ID
          LEFT JOIN HR_VERSION AS HRV ON HRV.ID = HRP.VERSION_ID
          WHERE (HRP.DATE_FROM BETWEEN %(date_from)s AND %(date_to)s) AND HRP.STATE != 'cancel'
          GROUP BY HRP.NAME,HRE.NAME,HRP.DATE_FROM
        )
        SELECT
          MC.PAYSLIP_DATE_FROM::TEXT AS Date,
          MC.NAME,
          MC.BASIC_WAGE,
          MC.WORK_PERMIT,
          MC.CASH_ALLOWANCE,
          MC.REIMBURSEMENT,
          MC.LOAN,
          MC.INSURANCE,
          MC.OTHER_DEDUCTION,
          MC.ANNUAL,
          MC.UNPAID,
          MC.SICK,
          MC.BASIC_WAGE+MC.WORK_PERMIT+MC.REIMBURSEMENT-MC.ANNUAL-MC.UNPAID-MC.SICK AS BANK_TRANSFER,
          MC.CASH_ALLOWANCE AS CASH_PAYMENT,
          MC.WORK_PERMIT+MC.LOAN+MC.INSURANCE+MC.OTHER_DEDUCTION AS RETURN,
          MC.BANK_NAME
        FROM MAIN_COMPONENT AS MC
        ORDER BY MC.PAYSLIP_DATE_FROM
        """
        self.env.cr.execute(query, {
            'date_from': form_data['date_from'],
            'date_to': form_data['date_to']
        })
        result = self.env.cr.fetchall()
        return result

    def get_report_header(self):
        header = [
            "Date",
            "Employee",
            "Basic Wage",
            "Work Permit",
            "Cash Allowance",
            "Reimbursement",
            "Loan",
            "Insurance",
            "Other Deduction",
            "Annual",
            "Unpaid",
            "Sick",
            "Bank Transfer",
            "Cash Payment",
            "Return",
            "Bank Name",
        ]
        return header

    def generate_xlsx_report(self, workbook, form_data, docids):
        report_name = _('Payslip Report')
        data = T.concatv([self.get_report_header()], self.get_report_body(form_data))
        sheet = workbook.add_worksheet(report_name[:31])
        self.write_dynamic_report(sheet, data)
