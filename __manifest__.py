# __manifest__.py
{
    'name': 'Project Task Customizations',
    'version': '17.0.1.0.0',
    'summary': 'Applies custom security rules to project tasks.',
    'author': 'Syeda Qirrat',
    'category': 'Services/Project',
    'depends': [
        'project'  # Our module depends on the original Project module
    ],
    'data': [
        'views/project_task_views.xml', # Load our XML view file
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}