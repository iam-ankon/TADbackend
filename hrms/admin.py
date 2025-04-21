from django.contrib import admin
from .models import * 


admin.site.register(EmployeeDetails)
admin.site.register(PerformanseAppraisal)
admin.site.register(EmployeeTermination)
admin.site.register(TerminationAttachment)
admin.site.register(TADGroups)
admin.site.register(Customers)
admin.site.register(EmployeeAttachment)
admin.site.register(Interview)
admin.site.register(InviteMail)
admin.site.register(Notification)
admin.site.register(Attendance)
admin.site.register(EmployeeLeave)
admin.site.register(EmployeeLeaveType)
admin.site.register(EmployeeLeaveBalance)
admin.site.register(LetterSend)
admin.site.register(CVAdd)
admin.site.register(ITProvision)
admin.site.register(AdminProvision)
admin.site.register(Mdsir)
@admin.register(FinanceProvision)
class FinanceProvisionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'email', 'payroll_pdf')
    list_filter = ('payroll_pdf',)
    search_fields = ('employee__name', 'email')
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'subject', 'sent_at')
    search_fields = ('recipient', 'subject')
    list_filter = ('sent_at',)




