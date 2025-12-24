from odoo import _, api, fields, models


class HrLeavePolicyLine(models.Model):
  _name = 'hr.leave.line.part'
  _description = 'Leave Policy Line'

  # sick_leave_deduction_policy_id = fields.Many2one(
  #     'sick.leave.deduction.policy',
  #     string='Sick Leave Deduction Policy',
  # )
  hr_leave_line_id = fields.Many2one(
      'hr.leave.line',
      string='Leave Line',
      ondelete='cascade',
  )

  consumed_days = fields.Float(
      string='Consumed Days',
  )

  hr_leave_employee_policy_id = fields.Many2one(
      'hr.leave.employee.policy',
      string='Leave Employee Policy',
  )

  total_deduction = fields.Float(
      string='Total Deduction',
  )