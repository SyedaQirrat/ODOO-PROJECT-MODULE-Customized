# models/project_task.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

def _get_default_user_is_manager(self):
    """Returns True if the current user is a Project Manager, otherwise False."""
    return self.env.user.has_group('project.group_project_manager')

class ProjectTask(models.Model):
    _inherit = 'project.task'

    user_is_manager = fields.Boolean(
        string="Is User a Manager",
        compute='_compute_user_is_manager',
        default=_get_default_user_is_manager,
        help="Technical field to check if the current user is a Project Manager."
    )
    # NEW: Helper field to check if the current user can change the task stage
    can_edit_stage = fields.Boolean(
        string="Can Edit Stage",
        compute='_compute_can_edit_stage',
        help="Technical field to check if the user can edit the stage."
    )

    def _compute_user_is_manager(self):
        is_manager = self.env.user.has_group('project.group_project_manager')
        for task in self:
            task.user_is_manager = is_manager

    # NEW: Compute method for the can_edit_stage field
    def _compute_can_edit_stage(self):
        """
        Calculates if the current user has rights to change the stage.
        Returns True if the user is a Manager, the creator, or an assignee.
        """
        is_manager = self.env.user.has_group('project.group_project_manager')
        for task in self:
            if is_manager or task.create_uid == self.env.user or self.env.user in task.user_ids:
                task.can_edit_stage = True
            else:
                task.can_edit_stage = False

    @api.model
    def default_get(self, fields_list):
        res = super(ProjectTask, self).default_get(fields_list)
        is_user = self.env.user.has_group('project.group_project_user')
        is_manager = self.env.user.has_group('project.group_project_manager')
        if is_user and not is_manager:
            res['user_ids'] = [(6, 0, [self.env.user.id])]
        return res

    @api.constrains('user_ids')
    def _check_one_assignee(self):
        for task in self:
            if self.env.user.has_group('project.group_project_manager') and len(task.user_ids) > 1:
                raise ValidationError(_("As a Project Manager, you can only assign one person to a task."))

    def write(self, vals):
        return super(ProjectTask, self).write(vals)