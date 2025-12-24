from odoo import _, models
import toolz as T
import toolz.curried as TC
import io
import base64


class HrPayslipReportXlsx(models.AbstractModel):
    _name = 'report.hr_extra_report.hr_payslip_report_xlsx'
    _inherit = 'report.report_xlsx_dynamic.abstract'
    _description = "HR Payslip Report XLSX"

    def generate_xlsx_report(self, workbook, form_data, docids):

        def prepare_custom_cell(cell_value, colspan=1, rowspan=1, style=None):
            cell_format = workbook.add_format(style or {})
            return {
                'cell_value': cell_value,
                'colspan': colspan,
                'rowspan': rowspan,
                'cell_format': cell_format,
            }

        report_name = _('Payslip Report')
        sheet = workbook.add_worksheet(report_name[:31])
        header_image = self.env['res.company.image'].browse(form_data['logo_id'])
        company_image = io.BytesIO(base64.b64decode(header_image.image))
        sheet.insert_image(
            'A1',
            "image.png",
            {
                'image_data': company_image,
                'x_scale': 0.5,
                'y_scale': 0.25
            },
        )
        report_qyery_result = self.env['report.hr_extra_report.hr_payslip_report']._prepare_report_data(
            docids, form_data)
        available_salary_rules = T.pipe(
            self.env['hr.payslip.line'].search([]),
            TC.map(TC.get('name')),
            TC.unique,
            list,
        )
        report_body = [
            [None],
            [None],
            [
                None,
                'From',
                form_data['date_from'],
                'To',
                form_data['date_to'],
            ],
        ]
        if report_qyery_result:
            structured_data = T.pipe(
                report_qyery_result,
                TC.groupby('title'),
                TC.valmap(TC.compose_left(TC.groupby('department_name')),),
                lambda data: {
                    'lines':
                        T.pipe(
                            data.get('LINES', {}),
                            TC.valmap(
                                TC.compose_left(
                                    TC.groupby('employee_name'),
                                    TC.valmap(
                                        TC.compose_left(
                                            TC.groupby('salary_rule_name'),
                                            TC.valmap(TC.map(TC.get('total'))),
                                            TC.valmap(sum),
                                        ),),
                                ),),
                        ),
                    'department_totals':
                        T.pipe(
                            data.get('DEPARTMENT TOTALS', {}),
                            TC.valmap(
                                TC.compose_left(
                                    TC.groupby('salary_rule_name'),
                                    TC.valmap(TC.compose_left(
                                        TC.first,
                                        TC.get('total'),
                                    ),),
                                )),
                        ),
                    'company_totals':
                        T.pipe(
                            data.get('COMPANY TOTALS', {}),
                            TC.valmap(
                                TC.compose_left(
                                    TC.groupby('salary_rule_name'),
                                    TC.valmap(TC.compose_left(
                                        TC.first,
                                        TC.get('total'),
                                    ),),
                                )),
                        ),
                    'report_totals':
                        T.pipe(
                            data.get('REPORT TOTALS', {}),
                            lambda totals: totals.values(),
                            TC.first,
                            TC.groupby('salary_rule_name'),
                            TC.valmap(TC.compose_left(
                                TC.first,
                                TC.get('total'),
                            )),
                        ),
                },
            )

            for department_name in structured_data['lines']:
                report_body.append([
                    prepare_custom_cell(department_name, style={'bold': True}),
                    *[
                        prepare_custom_cell(
                            salary_rule,
                            style={'bold': True},
                        ) for salary_rule in available_salary_rules
                    ],
                ],)
                for employee_name in structured_data['lines'][department_name]:
                    report_body.append([
                        prepare_custom_cell(employee_name),
                        *[
                            structured_data['lines'][department_name][employee_name].get(salary_rule, 0)
                            for salary_rule in available_salary_rules
                        ],
                    ],)
                report_body.append([
                    prepare_custom_cell(f"Total Department:{department_name}", style={'bold': True}),
                    *[
                        structured_data['department_totals'][department_name].get(salary_rule, 0)
                        for salary_rule in available_salary_rules
                    ],
                ],)
                report_body.append([None],)
            # =============================================================================
            for company_name in structured_data['company_totals']:
                report_body.append([
                    prepare_custom_cell(f"Total Company:{company_name}", style={'bold': True}),
                    *[
                        structured_data['company_totals'][company_name].get(salary_rule, 0)
                        for salary_rule in available_salary_rules
                    ],
                ],)
            # =============================================================================
            report_body.append([
                prepare_custom_cell("Grand Total", style={'bold': True}),
                *[
                    prepare_custom_cell(
                        structured_data['report_totals'].get(salary_rule, 0),
                        style={'bold': True},
                    ) for salary_rule in available_salary_rules
                ],
            ],)

        self.write_dynamic_report(
            sheet,
            report_body,
        )
