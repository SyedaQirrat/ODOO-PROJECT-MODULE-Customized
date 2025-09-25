# models/project_task.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

def _get_default_user_is_manager(self):
    """Returns True if the current user is a Project Manager, otherwise False."""
    return self.env.user.has_group('project.group_project_manager')

class ProjectTask(models.Model):
    _inherit = 'project.task'

    # ----------------------------------------------------------------
    # Custom Fields (Defined in Code)
    # ----------------------------------------------------------------
    x_crf_number = fields.Char(string="CRF Number", tracking=True)

    # ----------------------------------------------------------------
    # Helper Fields for UI Logic
    # ----------------------------------------------------------------
    user_is_manager = fields.Boolean(
        string="Is User a Manager",
        compute='_compute_user_is_manager',
        default=_get_default_user_is_manager
    )
    can_edit_stage = fields.Boolean(
        string="Can Edit Stage",
        compute='_compute_can_edit_stage'
    )

    # ----------------------------------------------------------------
    # Compute Methods for Helper Fields
    # ----------------------------------------------------------------
    def _compute_user_is_manager(self):
        is_manager = self.env.user.has_group('project.group_project_manager')
        for task in self:
            task.user_is_manager = is_manager

    def _compute_can_edit_stage(self):
        """
        A user can edit the stage if:
        - They are a Manager OR an Assignee
        - AND the task is NOT a parent task (has no sub-tasks).
        """
        is_manager = self.env.user.has_group('project.group_project_manager')
        for task in self:
            # A user/assignee cannot change the stage of a parent task.
            if task.child_ids and not is_manager:
                task.can_edit_stage = False
                continue
            
            # Creator is no longer allowed, only Manager or Assignee.
            if is_manager or self.env.user in task.user_ids:
                task.can_edit_stage = True
            else:
                task.can_edit_stage = False

    # ----------------------------------------------------------------
    # ORM Method Overrides (create, write, default_get)
    # ----------------------------------------------------------------
    @api.model
    def default_get(self, fields_list):
        res = super(ProjectTask, self).default_get(fields_list)
        is_user = self.env.user.has_group('project.group_project_user')
        is_manager = self.env.user.has_group('project.group_project_manager')
        if is_user and not is_manager:
            res['user_ids'] = [(6, 0, [self.env.user.id])]
        return res

    @api.model
    def create(self, vals):
        """Override create for validation and sub-task attribute inheritance."""
        # Inherit Attributes to Sub-tasks
        if 'parent_id' in vals and vals.get('parent_id'):
            parent_task = self.env['project.task'].browse(vals['parent_id'])
            if parent_task:
                if parent_task.tag_ids:
                    vals['tag_ids'] = [(6, 0, parent_task.tag_ids.ids)]
                if parent_task.x_crf_number:
                     vals['x_crf_number'] = parent_task.x_crf_number
        
        # Validation for Project Users
        is_user = self.env.user.has_group('project.group_project_user')
        is_manager = self.env.user.has_group('project.group_project_manager')
        if is_user and not is_manager and 'user_ids' in vals:
            user_ids_command = vals.get('user_ids')
            if user_ids_command and user_ids_command[0] and user_ids_command[0][0] in (4, 6):
                assignee_ids = user_ids_command[0][2]
                if assignee_ids != [self.env.user.id]:
                    raise ValidationError(_("As a Project User, you can only assign tasks to yourself."))
        
        task = super(ProjectTask, self).create(vals)

        # Validation for Project Managers
        if is_manager and len(task.user_ids) > 1:
            raise ValidationError(_("As a Project Manager, you can only assign one person to a task."))
            
        return task

    def write(self, vals):
        """Override write for stage reversal and assignee validation."""
        # Prevent Stage Reversal
        if 'stage_id' in vals:
            new_stage = self.env['project.task.type'].browse(vals['stage_id'])
            for task in self:
                if new_stage.sequence < task.stage_id.sequence:
                    raise UserError(_("You cannot move a task to a previous stage."))

        res = super(ProjectTask, self).write(vals)

        # Validation for Project Users & Managers on edit
        is_user = self.env.user.has_group('project.group_project_user')
        is_manager = self.env.user.has_group('project.group_project_manager')
        for task in self:
            if is_user and not is_manager:
                if task.user_ids and task.user_ids.id != self.env.user.id:
                    raise ValidationError(_("As a Project User, you can only assign tasks to yourself."))
            if is_manager and len(task.user_ids) > 1:
                raise ValidationError(_("As a Project Manager, you can only assign one person to a task."))
        
        return res

    # ----------------------------------------------------------------
    # Constrains / Validation Methods
    # ----------------------------------------------------------------
    @api.constrains('date_deadline', 'parent_id')
    def _check_subtask_deadline(self):
        """Validates that a sub-task's deadline does not exceed its parent's deadline."""
        for task in self:
            if task.parent_id and task.date_deadline and task.parent_id.date_deadline:
                if task.date_deadline > task.parent_id.date_deadline:
                    raise ValidationError(_("A sub-task's deadline cannot be later than its parent task's deadline."))