# models/project_task.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from lxml import etree

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

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProjectTask, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        is_user = self.env.user.has_group('project.group_project_user')
        is_manager = self.env.user.has_group('project.group_project_manager')

        # CHANGE: The "view_type == 'form'" check is removed to apply the domain to all views.
        if is_user and not is_manager:
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='user_ids']"):
                domain = f"[('id', '=', {self.env.user.id})]"
                node.set('domain', domain)
            res['arch'] = etree.tostring(doc)
        return res

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
    def _check_one_assignee(self):
        for task in self:
            if self.env.user.has_group('project.group_project_manager') and len(task.user_ids) > 1:
                raise ValidationError(_("As a Project Manager, you can only assign one person to a task."))

    def write(self, vals):
        return super(ProjectTask, self).write(vals)