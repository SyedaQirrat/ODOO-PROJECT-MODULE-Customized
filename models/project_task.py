# models/project_task.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

def _get_default_user_is_manager(self):
    return self.env.user.has_group('project.group_project_manager')

class ProjectTask(models.Model):
    _inherit = 'project.task'

    # Custom Field
    x_crf_number = fields.Char(string="CRF Number", tracking=True)

    # Helper fields for UI logic
    user_is_manager = fields.Boolean(compute='_compute_user_is_manager', default=_get_default_user_is_manager)
    can_edit_stage = fields.Boolean(compute='_compute_can_edit_stage')

    def _compute_user_is_manager(self):
        is_manager = self.env.user.has_group('project.group_project_manager')
        for task in self:
            task.user_is_manager = is_manager

    def _compute_can_edit_stage(self):
        is_manager = self.env.user.has_group('project.group_project_manager')
        for task in self:
            # Rule #8: Non-managers cannot change the stage of a parent task
            if task.child_ids and not is_manager:
                task.can_edit_stage = False
                continue
            # Rule #3: Stage can be changed by Manager or Assignee
            if is_manager or self.env.user in task.user_ids:
                task.can_edit_stage = True
            else:
                task.can_edit_stage = False

    @api.model
    def create(self, vals):
        # Rule #7: Deadline is mandatory ONLY on create
        if not vals.get('date_deadline'):
            raise ValidationError(_("A deadline is required to create a task."))

        # Rule: Only managers can create parent tasks
        is_manager = self.env.user.has_group('project.group_project_manager')
        if not is_manager and not vals.get('parent_id'):
            raise UserError(_("As a Project User, you can only create sub-tasks within an existing parent task."))

        # Rule #5: Inherit Attributes to Sub-tasks
        if 'parent_id' in vals and vals.get('parent_id'):
            parent_task = self.env['project.task'].browse(vals['parent_id'])
            if parent_task:
                if parent_task.tag_ids:
                    vals['tag_ids'] = [(6, 0, parent_task.tag_ids.ids)]
                if parent_task.x_crf_number:
                     vals['x_crf_number'] = parent_task.x_crf_number
        
        task = super(ProjectTask, self).create(vals)
        return task

    def write(self, vals):
        # Rule #4: Prevent Stage Reversal
        if 'stage_id' in vals:
            new_stage = self.env['project.task.type'].browse(vals['stage_id'])
            for task in self:
                if new_stage.sequence < task.stage_id.sequence:
                    raise UserError(_("You cannot move a task to a previous stage."))
        
        return super(ProjectTask, self).write(vals)

    # Rule #6: Sub-task deadline validation
    @api.constrains('date_deadline', 'parent_id')
    def _check_subtask_deadline(self):
        for task in self:
            if task.parent_id and task.date_deadline and task.parent_id.date_deadline:
                if task.date_deadline > task.parent_id.date_deadline:
                    raise ValidationError(_("A sub-task's deadline cannot be later than its parent task's deadline."))

    # Rule #1: All assignee rules
    @api.constrains('user_ids')
    def _check_assignee_rules(self):
        for task in self:
            # Global Rule: No task can have more than one assignee
            if len(task.user_ids) > 1:
                raise ValidationError(_("A task can only be assigned to one person."))
            
            # User-specific Rule: A Project User can only assign themself
            is_user = self.env.user.has_group('project.group_project_user')
            is_manager = self.env.user.has_group('project.group_project_manager')
            if is_user and not is_manager:
                if task.user_ids and task.user_ids.id != self.env.user.id:
                    raise ValidationError(_("As a Project User, you can only assign tasks to yourself."))