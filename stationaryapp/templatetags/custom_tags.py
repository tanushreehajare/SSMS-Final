from django import template

register = template.Library()

@register.filter
def unique_faculty_names(assignments):
    faculty_names = set()
    unique_faculties = []
    for assignment in assignments:
        if assignment.facultys_name not in faculty_names:
            faculty_names.add(assignment.facultys_name)
            unique_faculties.append(assignment.facultys_name)
    return unique_faculties

@register.filter
def unique_stationary_names(assignments):
    stationary_names = set()
    unique_stationaries = []
    for assignment in assignments:
        if assignment.stationary.stationary_name not in stationary_names:
            stationary_names.add(assignment.stationary.stationary_name)
            unique_stationaries.append(assignment.stationary.stationary_name)
    return unique_stationaries
