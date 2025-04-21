from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import * 

router = DefaultRouter()
router.register('employees', EmployeeDetailsViewSet)
router.register('performanse_appraisals', PerformanseAppraisalViewSet)
router.register('notifications', NotificationViewSet)
router.register('email_logs', EmailLogViewSet)  # New Email Log API
router.register('attendance', AttendanceViewSet)
router.register('employee_leave_types', EmployeeLeaveTypeViewSet)
router.register('employee_leaves', EmployeeLeaveViewSet)
router.register('employee_leave_balances', EmployeeLeaveBalanceViewSet)
router.register("interviews", InterviewViewSet)
router.register("letter_send", LetterSendViewSet)
router.register("CVAdd", CVAddViewSet) 
router.register("it_provisions", ITProvisionViewSet)
router.register("admin_provisions", AdminProvisionViewSet)
router.register("finance_provisions", FinanceProvisionViewSet)
router.register("employee_attachments", EmployeeAttachmentListCreateView)
router.register("tad_groups", TADGroupsViewSet)
router.register("customers", CustomersViewSet)
router.register("employee_termination", EmployeeTerminationViewSet)
router.register("termination_attachment", TerminationAttachmentListCreateView)
router.register('mdsir', MdsirViewSet)
router.register('invitemail', InviteMailViewSet)



urlpatterns = [
    path('api/', include(router.urls)),
    
]
