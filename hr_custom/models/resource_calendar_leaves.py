from odoo import _, api, fields, models
from datetime import datetime, time
from pytz import timezone


class ResourceCalendarLeaves(models.Model):
  _inherit = 'resource.calendar.leaves'

  leave_date_from = fields.Date(
      string='Date From',
  )

  leave_date_to = fields.Date(
      string='Date To',
  )

  @api.onchange('leave_date_from')
  def _onchange_leave_date_from(self):
    if self.leave_date_from:
      user_tz = timezone(self.env.user.tz or self._context.get('tz') or self.company_id.resource_calendar_id.tz or 'UTC')
      localize_date_from = user_tz.localize(datetime.combine(self.leave_date_from, time.min))
      utc_date_from = localize_date_from.astimezone(timezone('UTC'))
      self.date_from = utc_date_from.replace(tzinfo=None)

  @api.onchange('leave_date_to')
  def _onchange_leave_date_to(self):
    if self.leave_date_to:
      user_tz = timezone(self.env.user.tz or self._context.get('tz') or self.company_id.resource_calendar_id.tz or 'UTC')
      localize_date_to = user_tz.localize(datetime.combine(self.leave_date_to, time.max))
      utc_date_to = localize_date_to.astimezone(timezone('UTC'))
      self.date_to = utc_date_to.replace(tzinfo=None)
