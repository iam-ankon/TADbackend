# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import EmailMessage, send_mail,EmailMultiAlternatives
from django.conf import settings
import mimetypes
from datetime import time
from django.core.exceptions import ValidationError
from django.http import JsonResponse
import json
import logging
import pillow_heif
from django.core.files.base import ContentFile
from io import BytesIO
import os
from PIL import Image
from datetime import time, datetime, timedelta
from django.utils import timezone

pillow_heif.register_heif_opener()
logger = logging.getLogger(__name__)
# Email Log Model


class EmailLog(models.Model):
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Email to {self.recipient} at {self.sent_at}"


class TADGroups(models.Model):
    company_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.company_name


class Customers(models.Model):
    customer_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.customer_name

# Employee Details Model


class EmployeeDetails(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    joining_date = models.DateField()
    date_of_birth = models.DateField()
    email = models.EmailField(unique=True)
    mail_address = models.TextField(blank=True, null=True)
    personal_phone = models.CharField(max_length=20, blank=True, null=True)
    office_phone = models.CharField(max_length=20, blank=True, null=True)
    reference_phone = models.CharField(max_length=20, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey(
        'TADGroups',
        on_delete=models.CASCADE,
        related_name="employees",
        null=True,
        blank=True,
    )
    salary = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    reporting_leader = models.CharField(max_length=255, blank=True, null=True)
    special_skills = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    permanent_address = models.TextField(blank=True, null=True)
    customer = models.ManyToManyField(
        Customers,
        related_name="employees",
        blank=True
    )
    image1 = models.ImageField(
        upload_to="employee_images/", blank=True, null=True
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # If image1 is empty or invalid, set it to None
        if self.image1 and not getattr(self.image1, 'name', None):
            self.image1 = None
        super().save(*args, **kwargs)

    @classmethod
    def send_birthday_wishes(cls):
        try:
            logger.info("🎉 Checking for today's birthdays...")
            today = timezone.now().date()

            # Get all employees with birthdays today
            birthday_employees = cls.objects.filter(
                date_of_birth__day=today.day,
                date_of_birth__month=today.month
            ).exclude(email__isnull=True).exclude(email__exact="").distinct()

            if not birthday_employees.exists():
                logger.info("No birthdays today.")
                return

            logger.info(f"Found {birthday_employees.count()} birthday(s).")
            company_name = getattr(settings, "COMPANY_NAME", "Our Company")

            # Email templates
            birthday_template = """Dear {name},

    Wishing you a very Happy Birthday! 🎉🎂
    May your day be filled with joy and success.

    Warm regards,  
    {company_name} Team"""

            notify_template = """Dear Team,

    Please join us in wishing a Happy Birthday to:
    {birthday_list}

    Make their day special!

    HR Department  
    {company_name}
    """

            # Track who we've emailed in this run
            sent_birthday_emails = set()
            notified = False

            birthday_names = []

            for emp in birthday_employees:
                if emp.email in sent_birthday_emails:
                    logger.warning(
                        f"⚠️ Already wished {emp.email}, skipping...")
                    continue

                try:
                    # Send birthday email
                    send_mail(
                        subject=f"Happy Birthday, {emp.name}!",
                        message=birthday_template.format(
                            name=emp.name,
                            company_name=company_name
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[emp.email],
                        fail_silently=False,
                    )
                    sent_birthday_emails.add(emp.email)
                    birthday_names.append(
                        f"🎉 {emp.name} ({emp.designation}) - mailto:{emp.email}")
                    logger.info(f"🎂 Sent birthday wish to {emp.name}")
                except Exception as e:
                    logger.error(
                        f"❌ Could not send birthday email to {emp.name}: {e}")

            # Only notify once if there were birthday emails successfully sent
            if birthday_names and not notified:
                try:
                    notify_emails = cls.objects.exclude(
                        email__in=sent_birthday_emails
                    ).exclude(
                        email__isnull=True
                    ).exclude(
                        email__exact=""
                    ).values_list("email", flat=True).distinct()

                    if notify_emails:
                        send_mail(
                            subject="🎉 Team Birthday Announcement",
                            message=notify_template.format(
                                birthday_list="\n".join(birthday_names),
                                company_name=company_name
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=list(notify_emails),
                            fail_silently=False,
                        )
                        logger.info(
                            f"✅ Notified {len(notify_emails)} team members.")
                        notified = True
                except Exception as e:
                    logger.error(
                        f"❌ Failed to send team birthday notification: {e}")

            logger.info("✅ Birthday email process complete.")

        except Exception as e:
            logger.error(
                f"❌ Unhandled error in birthday wish method: {e}", exc_info=True)

    def save(self, *args, **kwargs):
        if self.image1 and self.image1.name.lower().endswith(".heic"):
            heif_file = pillow_heif.read_heif(self.image1)
            image = Image.frombytes(
                heif_file.mode, heif_file.size, heif_file.data, "raw"
            )
            buffer = BytesIO()
            image.save(buffer, format="JPEG")
            file_name = os.path.splitext(self.image1.name)[0] + ".jpg"
            self.image1.save(file_name, ContentFile(
                buffer.getvalue()), save=False)
        super().save(*args, **kwargs)


class PerformanseAppraisal(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    joining_date = models.DateField()
    department = models.CharField(max_length=255)
    last_increment_date = models.DateField()
    last_promotion_date = models.DateField()
    last_education = models.CharField(max_length=255)
    job_knowledge = models.IntegerField(blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)
    performance_in_meetings = models.IntegerField(blank=True, null=True)
    performance_description = models.TextField(blank=True, null=True)
    communication_skills = models.IntegerField(blank=True, null=True)
    communication_description = models.TextField(blank=True, null=True)
    reliability = models.IntegerField(blank=True, null=True)
    reliability_description = models.TextField(blank=True, null=True)
    initiative = models.IntegerField(blank=True, null=True)
    initiative_description = models.TextField(blank=True, null=True)
    stress_management = models.IntegerField(blank=True, null=True)
    stress_management_description = models.TextField(blank=True, null=True)
    co_operation = models.IntegerField(blank=True, null=True)
    co_operation_description = models.TextField(blank=True, null=True)
    leadership = models.IntegerField(blank=True, null=True)
    leadership_description = models.TextField(blank=True, null=True)
    discipline = models.IntegerField(blank=True, null=True)
    discipline_description = models.TextField(blank=True, null=True)
    ethical_considerations = models.IntegerField(blank=True, null=True)
    ethical_considerations_description = models.TextField(
        blank=True, null=True)
    promotion = models.BooleanField(default=False, blank=True, null=True)
    increment = models.BooleanField(default=False, blank=True, null=True)
    performance_reward = models.BooleanField(
        default=False, blank=True, null=True)
    performance = models.TextField(blank=True, null=True)
    expected_performance = models.TextField(blank=True, null=True)
    present_salary = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    proposed_salary = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    present_designation = models.CharField(
        max_length=255, blank=True, null=True)
    proposed_designation = models.CharField(
        max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class EmployeeTermination(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    company = models.ForeignKey(
        TADGroups,
        on_delete=models.CASCADE,
        related_name="terminated_employees",
        null=True,
        blank=True,
    )
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class TerminationAttachment(models.Model):
    employee = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE)
    file = models.FileField(upload_to="termination_attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(
        blank=True, null=True)  # Add description field

    def __str__(self):
        return f"{self.employee.name} - {self.file.name}"


# Attendance Model
class Attendance(models.Model):
    employee = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    check_in = models.TimeField()
    check_out = models.TimeField(null=True, blank=True)
    office_start_time = models.TimeField(default=time(9, 30))
    in_time = models.TimeField(null=True, blank=True)
    delay_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.name} - {self.date}"

    def is_late_check_in(self):
        return self.check_in > self.office_start_time

    def calculate_time_fields(self):
        # Convert times to datetime objects for calculation
        office_start = datetime.combine(
            datetime.today(), self.office_start_time)
        check_in_dt = datetime.combine(datetime.today(), self.check_in)

        if self.check_in <= self.office_start_time:
            # Employee is early or on time
            time_diff = office_start - check_in_dt
            self.in_time = (datetime.min + time_diff).time()
            self.delay_time = None
        else:
            # Employee is late
            time_diff = check_in_dt - office_start
            self.delay_time = (datetime.min + time_diff).time()
            self.in_time = None


@receiver(pre_save, sender=Attendance)
def calculate_attendance_times(sender, instance, **kwargs):
    instance.calculate_time_fields()


class EmployeeLeaveBalance(models.Model):
    employee = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE)
    employee_code = models.CharField(max_length=20, blank=True, null=True)
    public_festival_holiday = models.IntegerField(default=0)
    casual_leave = models.IntegerField(default=0)
    sick_leave = models.IntegerField(default=0)
    earned_leave = models.IntegerField(default=0)
    leave_balance = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        # Calculate the total leave balance
        self.leave_balance = (
            self.public_festival_holiday
            + self.casual_leave
            + self.sick_leave
            + self.earned_leave
        )
        super(EmployeeLeaveBalance, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.name} - {self.public_festival_holiday} - {self.casual_leave} - {self.sick_leave} - {self.earned_leave}"


class EmployeeLeaveType(models.Model):
    public_festival_holiday = models.IntegerField(default=0)
    casual_leave = models.IntegerField(default=0)
    sick_leave = models.IntegerField(default=0)
    earned_leave = models.IntegerField(default=0)

    def __str__(self):
        return f"Leave Types - Public Festival Holiday: {self.public_festival_holiday}, Casual Leave: {self.casual_leave}, Sick Leave: {self.sick_leave}, Earned Leave: {self.earned_leave}"


class EmployeeLeave(models.Model):
    Public_Festival_Holiday = "Public Festival Holiday"
    Casual_Leave = "Casual Leave"
    Sick_Leave = "Sick Leave"
    Earned_Leave = "Earned Leave"

    LEAVE_CHOICES = [
        ("public_festival_holiday", "Public Festival Holiday"),
        ("casual_leave", "Casual Leave"),
        ("sick_leave", "Sick Leave"),
        ("earned_leave", "Earned Leave"),
    ]

    employee = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE)
    email = models.EmailField(blank=True, null=True)
    from_email = models.EmailField(blank=True, null=True)
    to = models.EmailField(blank=True, null=True)
    to_email = models.EmailField(blank=True, null=True)
    cc = models.EmailField(blank=True, null=True)
    receiver_name = models.CharField(max_length=255, blank=True, null=True)
    employee_code = models.CharField(max_length=20, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    joining_date = models.DateField(blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey(
        TADGroups, on_delete=models.CASCADE, null=True, blank=True
    )
    personal_phone = models.CharField(max_length=20, blank=True, null=True)
    sub_person = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    whereabouts = models.TextField(max_length=255, blank=True, null=True)
    teamleader = models.TextField(max_length=255, blank=True, null=True)
    hrcomment = models.TextField(max_length=255, blank=True, null=True)
    leave_days = models.IntegerField(default=0)
    comment = models.TextField(blank=True, null=True)
    leave_type = models.CharField(
        choices=LEAVE_CHOICES, max_length=255, blank=True, null=True
    )
    start_date = models.DateField()
    end_date = models.DateField()
    balance = models.IntegerField(default=0, blank=True, null=True)
    date_of_joining_after_leave = models.DateField(blank=True, null=True)
    actual_date_of_joining = models.DateField(blank=True, null=True)
    reson_for_delay = models.TextField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ("approved", "Approved"),
            ("pending", "Pending"),
            ("rejected", "Rejected"),
        ],
        default="pending",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.employee.name} - {self.leave_type}"

    def save(self, *args, **kwargs):
        # If the leave request is approved, deduct leave balance
        if self.status == "approved":
            self.deduct_leave_balance()

        super(EmployeeLeave, self).save(*args, **kwargs)

    def deduct_leave_balance(self):
        """
        Deduct the number of leave days from the employee's leave balance.
        """
        leave_days = (
            self.end_date - self.start_date
        ).days + 1  # +1 to include both start and end dates

        # Get the EmployeeLeaveBalance instance
        leave_balance = EmployeeLeaveBalance.objects.get(
            employee=self.employee)

        # Deduct the leave days based on the leave type
        if self.leave_type == "public_festival_holiday":
            leave_balance.public_festival_holiday -= leave_days
        elif self.leave_type == "casual_leave":
            leave_balance.casual_leave -= leave_days
        elif self.leave_type == "sick_leave":
            leave_balance.sick_leave -= leave_days
        elif self.leave_type == "earned_leave":
            leave_balance.earned_leave -= leave_days

        # Save the updated balance
        leave_balance.save()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if self.status == "approved":
            self.deduct_leave_balance()

        if self.from_email and self.to_email:
            self.send_leave_email()

    def send_leave_email(self):  # changed from instance to self
        subject = f"Leave Application - {self.employee.name}"

        message = f"""
        <html>
        <body>
            <p>Dear {'Laila' or 'HR Team'},</p>
            
            <p><strong>{self.employee.name}</strong> ({self.designation or 'N/A'} - {self.department or 'N/A'}) 
            has submitted a leave request with the following details:</p>
            
            <table border="0" cellpadding="5">
                <tr><td><strong>Leave Type:</strong></td><td>{self.get_leave_type_display()}</td></tr>
                <tr><td><strong>Duration:</strong></td><td>{self.start_date} to {self.end_date}</td></tr>
                <tr><td><strong>Leave Days:</strong></td><td>{self.leave_days}</td></tr>
                <tr><td><strong>Status:</strong></td><td>{self.get_status_display()}</td></tr>
                <tr><td><strong>Reason:</strong></td><td>{self.reason or 'Not specified'}</td></tr>
                <tr><td><strong>Substitute:</strong></td><td>{self.sub_person or 'Not assigned'}</td></tr>
                <tr><td><strong>Contact:</strong></td><td>{self.personal_phone or 'Not provided'}</td></tr>
            </table>
            
            <p>You can review this request by clicking the link below:</p>
            <p><a href="http://192.168.4.183:5173/edit-leave-request/{self.id}">View Leave Request</a></p>
            
            <p>Best Regards,<br>
            HR Management System</p>
        </body>
        </html>
        """

        recipient_list = [self.to_email]
        cc_list = [from_email.strip() for from_email in self.cc.split(',')] if self.cc else []

        email = EmailMultiAlternatives(
            subject=subject,
            body=message.strip(),  # you can also use plain text here if needed
            from_email=self.from_email,
            to=recipient_list,
            cc=cc_list,
        )
        email.content_subtype = "html"  # tells Django to treat the body as HTML
        email.send(fail_silently=False)



class EmployeeAttachment(models.Model):
    employee = models.ForeignKey(
        EmployeeDetails, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="employee_attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(
        blank=True, null=True)  # Add description field

    def __str__(self):
        return f"{self.employee.name} - {self.file.name}"


# Notification Model
class Notification(models.Model):
    employee = models.ForeignKey(
        EmployeeDetails, on_delete=models.CASCADE
    )  # Fixed ForeignKey
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


# Interview Model
class Interview(models.Model):
    name = models.CharField(max_length=255)
    position_for = models.CharField(max_length=255, blank=True, null=True)
    age = models.DateField(blank=True, null=True)
    reference = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    place = models.CharField(max_length=255, blank=True, null=True)
    interview_date = models.DateTimeField()
    education = models.IntegerField(blank=True, null=True)
    job_knowledge = models.IntegerField(blank=True, null=True)
    work_experience = models.IntegerField(blank=True, null=True)
    communication = models.IntegerField(blank=True, null=True)
    personality = models.IntegerField(blank=True, null=True)
    potential = models.IntegerField(blank=True, null=True)
    general_knowledge = models.IntegerField(blank=True, null=True)
    assertiveness = models.IntegerField(blank=True, null=True)
    interview_mark = models.IntegerField(blank=True, null=True)
    interview_result = models.CharField(max_length=255, blank=True, null=True)
    interview_notes = models.TextField(blank=True, null=True)
    current_remuneration = models.IntegerField(blank=True, null=True)
    expected_package = models.IntegerField(blank=True, null=True)
    notice_period_required = models.IntegerField(blank=True, null=True)
    recommendation = models.TextField(blank=True, null=True)
    immediate_recruitment = models.BooleanField(default=False)
    on_hold = models.BooleanField(default=False)
    no_good = models.BooleanField(default=False)
    final_selection_remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Interview - {self.name}"


# Letter Send Model
class LetterSend(models.Model):
    OFFER_LETTER = "Offer Letter"
    APPOINTMENT_LETTER = "Appointment Letter"
    JOINING_REPORT = "Joining Report"

    LETTER_CHOICES = [
        ("offer_letter", "Offer Letter"),
        ("appointment_letter", "Appointment Letter"),
        ("joining_report", "Joining Report"),
    ]
    name = models.CharField(max_length=255)
    email = models.EmailField()
    letter_file = models.FileField(upload_to="cv_letters/")
    letter_type = models.CharField(choices=LETTER_CHOICES, max_length=50)

    def __str__(self):
        return f"CV - {self.name}"


class CVAdd(models.Model):
    name = models.CharField(max_length=255)
    position_for = models.CharField(max_length=255, blank=True, null=True)
    age = models.DateField(blank=True, null=True)
    reference = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    cv_file = models.FileField(upload_to="cv_adds/", blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ITProvision(models.Model):
    employee = models.CharField(max_length=255)
    id_card = models.BooleanField(default=False)
    laptop = models.BooleanField(default=False)


class AdminProvision(models.Model):
    employee = models.CharField(max_length=255)
    bank_account_paper = models.BooleanField(default=False)
    sim_card = models.BooleanField(default=False)
    visiting_card = models.BooleanField(default=False)
    placement = models.BooleanField(default=False)


# Finance Provision Model
class FinanceProvision(models.Model):
    employee = models.CharField(max_length=255)
    email = models.EmailField()
    payroll_pdf = models.FileField(upload_to="payroll_pdfs/")

    def __str__(self):
        return f"Provision for {self.employee}"


class Mdsir(models.Model):
    email = models.EmailField()
    interview_details = models.JSONField(
        null=True, blank=True
    )  # Add this field to store interview details as JSON

    def __str__(self):
        return f"Mdsir - {self.email}"


class InviteMail(models.Model):
    description = models.TextField(blank=True, null=True)
    interview_details = models.JSONField(
        null=True, blank=True
    )  # Add this field to store interview details as JSON

    def __str__(self):
        return f"InviteMail - {self.description}"


# Function to Send Email for CV Management and Create Notification


@receiver(post_save, sender=LetterSend)
def send_cv_email(sender, instance, **kwargs):
    logger.info(f"Handling CV email for {instance.name}")
    subject = f"{instance.letter_type} for {instance.name}"
    message = f"Dear {instance.name},\n\nPlease find your {instance.letter_type} attached.\n\nBest Regards,\nHR Team"

    # Create an EmailMessage instance
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[instance.email],
    )

    # Check if the file is provided and attach it
    if instance.letter_file:
        try:
            # Log the file path
            logger.info(f"Attaching file from {instance.letter_file.path}")

            # Get the MIME type (content type) based on the file extension
            mime_type, encoding = mimetypes.guess_type(
                instance.letter_file.name)
            if mime_type is None:
                mime_type = (
                    "application/octet-stream"  # Fallback to a generic MIME type
                )

            # Read the file as binary
            with instance.letter_file.open("rb") as file:
                email.attach(instance.letter_file.name, file.read(), mime_type)

            logger.info(
                f"Successfully attached file: {instance.letter_file.name}")
        except Exception as e:
            logger.error(
                f"Error attaching file {instance.letter_file.name}: {str(e)}")
            raise ValidationError(f"Error attaching file: {str(e)}")

    # Send the email
    try:
        email_sent = email.send(
            fail_silently=False
        )  # Set fail_silently=False for debugging
        if email_sent:
            logger.info(f"Email sent successfully to {instance.email}")

            # Log the email
            EmailLog.objects.create(
                recipient=instance.email, subject=subject, message=message
            )

            # Create a notification for sending the email
            try:
                employee = EmployeeDetails.objects.get(email=instance.email)
                Notification.objects.create(
                    employee=employee,
                    message=f"Email sent to {instance.name} regarding {instance.letter_type}.",
                )
            except EmployeeDetails.DoesNotExist:
                logger.error(
                    f"Employee with email {instance.email} not found for notification creation."
                )
        else:
            logger.error("Email sending failed, but no exception was raised.")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")


# Auto-generate notification and send email when attendance_delay is True
@receiver(post_save, sender=Attendance)
def create_notification(sender, instance, **kwargs):
    # Check if the employee's check-in time is late
    if instance.is_late_check_in():
        message = f"Attendance delay recorded for {instance.employee.name} on {instance.date} at {instance.check_in}."

        # Send Email
        email_sent = send_mail(
            subject="Attendance Delay Alert",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.employee.email],
            fail_silently=True,
        )

        if email_sent > 0:
            # Log Email
            EmailLog.objects.create(
                recipient=instance.employee.email,
                subject="Attendance Delay Alert",
                message=message,
            )

        # Create Notification
        Notification.objects.create(
            employee=instance.employee, message=message)


# Auto-generate notification when employee details are updated
@receiver(post_save, sender=EmployeeDetails)
def create_employee_notification(sender, instance, **kwargs):
    message = f"Employee details updated for {instance.name}."

    # Create Notification
    Notification.objects.create(employee=instance, message=message)


@receiver(post_save, sender=FinanceProvision)
def payroll_email(sender, instance, **kwargs):
    if instance.payroll_pdf and instance.email:
        subject = "Your Payroll Document"

        # Use the 'employee' field directly as it's a CharField storing the employee name or identifier
        employee_name = instance.employee  # Directly access the 'employee' field

        message = (
            f"Dear {employee_name},\n\nPlease find attached your payroll document."
        )

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[instance.email],
        )
        email.attach_file(instance.payroll_pdf.path)
        email.send(fail_silently=True)

        # Log Email
        EmailLog.objects.create(
            recipient=instance.email, subject=subject, message=message
        )


@receiver(post_save, sender=EmployeeDetails)
def create_leave_balance(sender, instance, created, **kwargs):
    if created:
        print(f"New Employee Created: {instance.name}")
        leave_type = (
            EmployeeLeaveType.objects.last()
        )  # Get the most recent leave type configuration
        if leave_type:
            print(
                f"Assigning leave balance: {leave_type.public_festival_holiday}, {leave_type.casual_leave}, {leave_type.sick_leave}, {leave_type.earned_leave}"
            )
            EmployeeLeaveBalance.objects.create(
                employee=instance,
                public_festival_holiday=leave_type.public_festival_holiday,
                casual_leave=leave_type.casual_leave,
                sick_leave=leave_type.sick_leave,
                earned_leave=leave_type.earned_leave,
            )
        else:
            print("No leave type configuration found.")


def save_mdsir_details(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            interview_details = data.get("interview_details")

            # Create or update the Mdsir instance
            mdsir_instance, created = Mdsir.objects.update_or_create(
                email=email, defaults={"interview_details": interview_details}
            )

            return JsonResponse(
                {"message": "Mdsir instance created/updated successfully"}, status=200
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@receiver(post_save, sender=Mdsir)
def email(sender, instance, **kwargs):
    # Now interview_details will be available in the instance
    interview_details = instance.interview_details or {}
    # Generate a link for the Interview Update Page
    # Update this with your actual frontend URL
    frontend_url = "https://tad-group.vercel.app/interviews"
    interview_id = interview_details.get(
        "id", ""
    )  # Assuming each interview has an 'id'
    update_link = f"{frontend_url}?interview_id={interview_id}"

    if instance.email:
        subject = "Interview Details"

        message = f"""
        Dear Hiring Manager,

        Here are the complete interview details for {interview_details.get('name', 'the candidate')}:

        **Candidate Information:**
        - Name: {interview_details.get('name', 'N/A')}
        - Position Applied: {interview_details.get('position_for', 'N/A')}
        - Age: {interview_details.get('age', 'N/A')}
        - Reference: {interview_details.get('reference', 'N/A')}
        - Email: {interview_details.get('email', 'N/A')}
        - Phone: {interview_details.get('phone', 'N/A')}

        **Interview Details:**
        - Interview Date: {interview_details.get('interview_date', 'N/A')}
        - Current Remuneration: {interview_details.get('current_remuneration', 'N/A')}
        - Expected Package: {interview_details.get('expected_package', 'N/A')}
        - Notice Period: {interview_details.get('notice_period_required', 'N/A')} days

        **Evaluation Scores (1-20):**
        - Education: {interview_details.get('education', 'N/A')}
        - Job Knowledge: {interview_details.get('job_knowledge', 'N/A')}

        **Evaluation Scores (1-10):**
        - Work Experience: {interview_details.get('work_experience', 'N/A')}
        - Communication: {interview_details.get('communication', 'N/A')}
        - Personality: {interview_details.get('personality', 'N/A')}
        - Potential: {interview_details.get('potential', 'N/A')}
        - General Knowledge: {interview_details.get('general_knowledge', 'N/A')}
        - Assertiveness: {interview_details.get('assertiveness', 'N/A')}

        **Interview Results:**
        - Total Interview Mark: {interview_details.get('interview_mark', 'N/A')}
        - Result: {interview_details.get('interview_result', 'Pending')}

        Click the link below to update or review the interview details:
        {update_link}

        Best Regards,
        HR Team
        """
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[instance.email],
        )
        email.send(fail_silently=True)

        # Log Email
        EmailLog.objects.create(
            recipient=instance.email, subject=subject, message=message
        )


def save_invite_details(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            description = data.get("description")
            interview_details = data.get("interview_details")

            # Create or update the Mdsir instance
            mdsir_instance, created = InviteMail.objects.update_or_create(
                description=description,
                defaults={"interview_details": interview_details},
            )

            return JsonResponse(
                {"message": "Mdsir instance created/updated successfully"}, status=200
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@receiver(post_save, sender=InviteMail)
def send_invitation_email(sender, instance, **kwargs):
    interview_details = instance.interview_details or {}

    if instance.description:
        subject = "Invitation Mail"

        message = f"""
        Dear {interview_details.get('name', 'N/A')},

        Here are the interview details:

        Name: {interview_details.get('name', 'N/A')}
        Reference: {interview_details.get('reference', 'N/A')}
        Email: {interview_details.get('email', 'N/A')}
        Phone: {interview_details.get('phone', 'N/A')}
        Interview Date: {interview_details.get('interview_date', 'N/A')}

        Message from HR:
        {instance.description}

        Best Regards,
        HR Team
        """

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[interview_details.get("email")],
        )
        email.send(fail_silently=True)

        # Log Email
        EmailLog.objects.create(
            recipient=interview_details.get("email"), subject=subject, message=message
        )




@receiver(post_save, sender=EmployeeLeave)
def send_leave_email(sender, instance, created, **kwargs):
    """
    Send email notification when:
    - A new leave request is created, or
    - The status changes during an update
    """
    # Check if this is an update (not creation)
    if not created:
        # Get the original instance before update
        original = EmployeeLeave.objects.get(pk=instance.pk)
        
        # Only send email if status changed
        if original.status == instance.status:
            return

    # Prepare email content
    subject = f"{instance.get_leave_type_display()} Request - {instance.employee.name}"

    # Create a more professional HTML email
    message = f"""
    <html>
    <body>
        <p>Dear {instance.receiver_name or 'HR Team'},</p>
        
        <p><strong>{instance.employee.name}</strong> ({instance.designation or 'N/A'} - {instance.department or 'N/A'}) 
        has submitted a leave request with the following details:</p>
        
        <table border="0" cellpadding="5">
            <tr><td><strong>Leave Type:</strong></td><td>{instance.get_leave_type_display()}</td></tr>
            <tr><td><strong>Duration:</strong></td><td>{instance.start_date} to {instance.end_date}</td></tr>
            <tr><td><strong>Leave Days:</strong></td><td>{instance.leave_days}</td></tr>
            <tr><td><strong>Status:</strong></td><td>{instance.get_status_display()}</td></tr>
            <tr><td><strong>Reason:</strong></td><td>{instance.reason or 'Not specified'}</td></tr>
            <tr><td><strong>Substitute:</strong></td><td>{instance.sub_person or 'Not assigned'}</td></tr>
            <tr><td><strong>Contact:</strong></td><td>{instance.personal_phone or 'Not provided'}</td></tr>
        </table>
        
        <p>You can review this request by clicking the link below:</p>
        <p><a href="https://tadbackend-5456.onrender.com/edit-leave-request/{instance.id}">View Leave Request</a></p>
        
        <p>Best Regards,<br>
        HR Management System</p>
    </body>
    </html>
    """

    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=instance.email,  # Send from employee's email
            to=[instance.to],  # Send to specified recipient
            reply_to=[instance.email],  # Replies go back to employee
        )
        email.content_subtype = "html"  # Set content as HTML

        # Add CC to HR if needed
        # email.cc = ['hr@company.com']

        email_sent = email.send(fail_silently=False)

        if email_sent:
            logger.info(
                f"Email sent successfully from {instance.email} to {instance.to}"
            )
        else:
            logger.error(f"Email sending failed for leave ID {instance.id}")

    except Exception as e:
        logger.error(
            f"Error sending email for leave ID {instance.id}: {str(e)}")


@receiver(post_save, sender=EmployeeDetails)
def notify_employees_on_new_entry(sender, instance, created, **kwargs):
    if created:
        # Exclude the newly added employee
        other_emails = EmployeeDetails.objects.exclude(
            pk=instance.pk).values_list('email', flat=True)

        subject = f"New Employee Joined: {instance.name}"
        message = (
            f"Please welcome {instance.name} who joined as {instance.designation} in the {instance.department} department.\n"
            f"Joining Date: {instance.joining_date.strftime('%Y-%m-%d')}\n"
            f"Email: {instance.email}\n"
            f"Phone: {instance.personal_phone or 'N/A'}"
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            list(other_emails),
            fail_silently=False,
        )
