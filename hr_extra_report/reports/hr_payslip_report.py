from odoo import _, api, models
import toolz as T
import toolz.curried as TC


class HrPayslipReport(models.AbstractModel):
    _name = 'report.hr_extra_report.hr_payslip_report'
    _description = "HR Payslip Report"

    @api.model
    def _prepare_report_data(self, docids, data):
        report_qyery = """
            SELECT
                CONCAT(GROUPING (RC.NAME),GROUPING (HRD.NAME),GROUPING (HRP.NAME)) AS FLAG,
              CASE
                WHEN CONCAT(GROUPING (RC.NAME),GROUPING (HRD.NAME),GROUPING (HRP.NAME)) = '001'  THEN 'DEPARTMENT TOTALS'
                WHEN CONCAT(GROUPING (RC.NAME),GROUPING (HRD.NAME),GROUPING (HRP.NAME)) = '111'  THEN 'REPORT TOTALS'
                WHEN CONCAT(GROUPING (RC.NAME),GROUPING (HRD.NAME),GROUPING (HRP.NAME)) = '011'  THEN 'COMPANY TOTALS'
              ELSE 'LINES' END AS TITLE,
              RC.NAME AS COMPANY_NAME,
              HRP.NAME AS PAYSIP_NAME,
              HRE.NAME AS EMPLOYEE_NAME,
                COALESCE(CONCAT(RC.NAME,'#',HRD.NAME),'NO DEPARTMENT') AS DEPARTMENT_NAME,
              SUM(HRPL.TOTAL) AS TOTAL,
              HRPL.NAME AS SALARY_RULE_NAME
              FROM HR_PAYSLIP AS HRP
              LEFT JOIN HR_PAYSLIP_LINE AS HRPL ON HRPL.SLIP_ID = HRP.ID
              LEFT JOIN HR_EMPLOYEE AS HRE ON HRE.ID = HRP.EMPLOYEE_ID
              LEFT JOIN HR_DEPARTMENT AS HRD ON HRD.ID = HRP.DEPARTMENT_ID
              LEFT JOIN RES_COMPANY AS RC ON RC.ID = HRP.COMPANY_ID
              WHERE HRP.DATE_FROM >= %(date_from)s AND HRP.DATE_TO <= %(date_to)s
              GROUP BY GROUPING SETS(
                (RC.NAME,HRD.NAME,HRP.NAME,HRPL.NAME, HRPL.TOTAL,HRE.NAME),
                (HRD.NAME,RC.NAME,HRPL.NAME),(RC.NAME,HRPL.NAME),(HRPL.NAME)
              )
            """
        self.env.cr.execute(
            report_qyery,
            {
                'date_from': data['date_from'],
                'date_to': data['date_to'],
            },
        )
        return self.env.cr.dictfetchall()
