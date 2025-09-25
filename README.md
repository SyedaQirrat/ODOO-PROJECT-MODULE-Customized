**Project Task Customizations for Odoo 17**


This module extends the standard Odoo 17 Project application to enforce a set of specific business rules and security restrictions. It is designed to provide granular control over task management for different user roles, specifically Project Managers and Project Users.

**Features**
This module introduces the following functionalities:

**General Rules**
The ability to edit fields is based on a user's role (Project Manager or Project User), not on whether they are a follower. Being a follower only grants notification rights.

**Project Manager Rules**
Single Assignee Limit: A Project Manager can only assign a task to one user at a time. Trying to assign more than one will result in a validation error.

Full Editing Rights: Managers have unrestricted access to change a task's stage and deadline at any time.

**Project User Rules**

**Self-Assignment Only:**

When a Project User creates a new task, they are automatically set as the assignee.

On the task form, the "Assignees" field is read-only.

On the Kanban quick-create form, any attempt to assign the task to another user will be blocked by a validation error.

**Stage Change Restrictions:**

A Project User can only change the stage of a task if they are the creator of the task or the assignee.

For all other tasks, the stage is read-only.

**Deadline Restrictions:**

A Project User can only set a task's deadline at the moment of creation.

Once the task is saved, the deadline field becomes read-only for them.

**Dependencies**
Odoo Project (project)

**Installation**
Place the project_customizations folder into your Odoo custom addons directory.

Restart the Odoo server service.

Log in to Odoo as an administrator and activate Developer Mode.

Navigate to the Apps menu.

Click on Update Apps List in the menu.

Search for Project Task Customizations and click the Install button.

**Configuration**
For the rules to apply correctly, ensure your users are configured with the appropriate access rights:

Navigate to Settings > Users & Companies > Users.

Select a user.

Under the Access Rights tab, scroll to the Project section.

Set the user's access to either "Manager" or "User (internal user)".