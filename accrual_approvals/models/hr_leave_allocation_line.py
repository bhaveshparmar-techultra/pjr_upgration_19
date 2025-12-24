from odoo import _, api, fields, models


class HolidaysAllocationLine(models.Model):
  _name = "hr.leave.allocation.line"
  _inherit = ["mail.thread", "mail.activity.mixin"]
  _description = "Leave Allocation Line"
  _rec_name = "employee_id"

  allocation_id = fields.Many2one(
      "hr.leave.allocation",
      ondelete="cascade",
  )
  state = fields.Selection(
      [
          ("draft", "Draft"),
          ("approve", "Approved"),
          ("refuse", "Refused"),
      ],
      string="Status",
      default="draft",
  )
  duration = fields.Float(string="Duration",)

  employee_id = fields.Many2one(
      "hr.employee",
      string="Employees",
  )
  remaining_duration = fields.Float(
      string="Remaining Duration",
      compute="_compute_remaining_duration",
      digits=(5, 5),
  )

  def action_approve(self):
    for line in self:
      line.state = "approve"
      line.allocation_id.number_of_days += line.remaining_duration

  def action_refuse(self):
    for line in self:
      line.state = "refuse"

  def _compute_remaining_duration(self):
    for allocation_line in self:
      # Handle case where create_date might be None for new records
      if not allocation_line.create_date:
        allocation_line.remaining_duration = allocation_line.duration
        continue

      hr_leave_line_ids = self.env["hr.leave.line"].sudo().search([
          ("employee_id", "=", allocation_line.employee_id.id),
          ("leave_month", "=", allocation_line.create_date.month),
          '|', '|',
          ("leave_type_id.unpaid", "=", True),
          ("leave_type_id.is_annual", "=", True),
          ("leave_type_id.absence", "=", True),
      ])
      month_working_days = hr_leave_line_ids[0].month_working_days if hr_leave_line_ids else 1
      deduction_rate = 2.5 / month_working_days
      approved_leave_duration = sum(hr_leave_line_ids.mapped("leave_duration"))
      deduction_duration = deduction_rate * approved_leave_duration
      allocation_line.remaining_duration = allocation_line.duration - deduction_duration
