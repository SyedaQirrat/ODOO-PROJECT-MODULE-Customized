# models/project_task.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

def _get_default_user_is_manager(self):
    return self.env.user.has_group('project.group_project_manager')

class ProjectTask(models.Model):
    _inherit = 'project.task'

    user_is_manager = fields.Boolean(
        compute='_compute_user_is_manager',
        default=_get_default_user_is_manager
    )
    can_edit_stage = fields.Boolean(
        compute='_compute_can_edit_stage'
    )

    def _compute_user_is_manager(self):
        is_manager = self.env.user.has_group('project.group_project_manager')
        for task in self:
            task.user_is_manager = is_manager

    def _compute_can_edit_stage(self):
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
    def _check_assignee_permissions(self):
        """
        This is the main validation rule. It runs on every save.
        - Managers can only assign one person.
        - Users can only assign themselves.
        """
        is_user = self.env.user.has_group('project.group_project_user')
        is_manager = self.env.user.has_group('project.group_project_manager')

        for task in self:
            # Rule for Project Users
            if is_user and not is_manager:
                if task.user_ids and (len(task.user_ids) > 1 or task.user_ids.id != self.env.user.id):
                    raise ValidationError(_("As a Project User, you can only assign tasks to yourself."))
            
            # Rule for Project Managers
            if is_manager:
                if len(task.user_ids) > 1:
                    raise ValidationError(_("As a Project Manager, you can only assign one person to a task."))

    def write(self, vals):
        return super(ProjectTask, self).write(vals) 