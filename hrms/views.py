from rest_framework import viewsets
from .models import * 
from .serializers import * 
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from PyPDF2 import PdfReader, PdfWriter
from django.http import JsonResponse
from PIL import Image, ImageDraw
from django.http import HttpResponse
import base64
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
import boto3
from botocore.exceptions import ClientError
from django.conf import settings


# Modify EmployeeDetailsViewSet in views.py
class EmployeeDetailsViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDetails.objects.all()
    serializer_class = EmployeeDetailsSerializer

    @action(detail=True, methods=['patch'])
    def update_customers(self, request, pk=None):
        employee = self.get_object()
        customer_ids = request.data.get('customers', [])
        employee.customer.set(customer_ids)
        return Response({'status': 'customers updated'})

class EmployeeTerminationViewSet(viewsets.ModelViewSet):
    queryset = EmployeeTermination.objects.all()
    serializer_class = EmployeeTerminationSerializer
    
    def update(self, request, *args, **kwargs):
        # Handle the update logic here if necessary
        return super().update(request, *args, **kwargs)

class PerformanseAppraisalViewSet(viewsets.ModelViewSet):
    queryset = PerformanseAppraisal.objects.all()
    serializer_class = PerformanseAppraisalSerializer

class TADGroupsViewSet(viewsets.ModelViewSet):
    queryset = TADGroups.objects.all()
    serializer_class = TADGroupsSerializer

class CustomersViewSet(viewsets.ModelViewSet):
    queryset = Customers.objects.all()
    serializer_class = CustomersSerializer    

# Notifications ViewSet
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

class EmailLogViewSet(viewsets.ModelViewSet):
    queryset = EmailLog.objects.all()
    serializer_class = EmailLogSerializer

    # Custom action for deleting all email logs
    @action(detail=False, methods=['delete'])
    def delete_all(self, request):
        try:
            # Delete all email logs
            EmailLog.objects.all().delete()
            return Response({'message': 'All email logs have been deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class EmployeeLeaveViewSet(viewsets.ModelViewSet):
    queryset = EmployeeLeave.objects.all()
    serializer_class = EmployeeLeaveSerializer

class EmployeeLeaveBalanceViewSet(viewsets.ModelViewSet):
    queryset = EmployeeLeaveBalance.objects.all()
    serializer_class = EmployeeLeaveBalanceSerializer

class EmployeeLeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = EmployeeLeaveType.objects.all()
    serializer_class = EmployeeLeaveTypeSerializer

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    
class InterviewViewSet(viewsets.ModelViewSet):
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer


class LetterSendViewSet(viewsets.ModelViewSet):
    queryset = LetterSend.objects.all()
    serializer_class = LetterSendSerializer
    parser_classes = (MultiPartParser, FormParser)


class ITProvisionViewSet(viewsets.ModelViewSet):
    queryset = ITProvision.objects.all()
    serializer_class = ITProvisionSerializer

class AdminProvisionViewSet(viewsets.ModelViewSet):
    queryset = AdminProvision.objects.all()
    serializer_class = AdminProvisionSerializer

class FinanceProvisionViewSet(viewsets.ModelViewSet):
    queryset = FinanceProvision.objects.all()
    serializer_class = FinanceProvisionSerializer

class EmployeeAttachmentListCreateView(viewsets.ModelViewSet):
    queryset = EmployeeAttachment.objects.all()
    serializer_class = EmployeeAttachmentSerializer

    def get_queryset(self):
        employee_id = self.request.query_params.get("employee_id")
        if employee_id:
            return self.queryset.filter(employee__id=employee_id)
        return self.queryset

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('file')  # Get multiple files
        employee_id = request.data.get('employee')  # Get employee ID
        descriptions = request.data.getlist('description')  # Get descriptions for each file

        if not employee_id:
            return Response({"error": "Employee ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        if len(descriptions) != len(files):
            return Response({"error": "Number of descriptions must match number of files"}, status=status.HTTP_400_BAD_REQUEST)

        employee = EmployeeDetails.objects.get(id=employee_id)

        attachments = []
        for i, file in enumerate(files):
            attachment = EmployeeAttachment(employee=employee, file=file, description=descriptions[i])
            attachments.append(attachment)

        EmployeeAttachment.objects.bulk_create(attachments)  # Bulk insert

        return Response({"message": "Files uploaded successfully"}, status=status.HTTP_201_CREATED)


class EmployeeAttachmentDeleteView(generics.DestroyAPIView):
    queryset = EmployeeAttachment.objects.all()
    serializer_class = EmployeeAttachmentSerializer


class TerminationAttachmentListCreateView(viewsets.ModelViewSet):
    queryset = TerminationAttachment.objects.all()
    serializer_class = TerminationAttachmentSerializer

    def get_queryset(self):
        employee_id = self.request.query_params.get("employee_id")
        if employee_id:
            return self.queryset.filter(employee__id=employee_id)
        return self.queryset

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('file')  # Get multiple files
        employee_id = request.data.get('employee')  # Get employee ID
        descriptions = request.data.getlist('description')  # Get descriptions for each file

        if not employee_id:
            return Response({"error": "Employee ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        if len(descriptions) != len(files):
            return Response({"error": "Number of descriptions must match number of files"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = EmployeeDetails.objects.get(id=employee_id)  # ✅ Use EmployeeTermination
        except EmployeeDetails.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        attachments = [
            TerminationAttachment(employee=employee, file=file, description=descriptions[i])
            for i, file in enumerate(files)
        ]

        TerminationAttachment.objects.bulk_create(attachments)  # Bulk insert

        return Response({"message": "Files uploaded successfully"}, status=status.HTTP_201_CREATED)



class TerminationAttachmentDeleteView(generics.DestroyAPIView):
    queryset = TerminationAttachment.objects.all()
    serializer_class = TerminationAttachmentSerializer




import logging

logger = logging.getLogger(__name__)

class CVAddViewSet(viewsets.ModelViewSet):
    queryset = CVAdd.objects.all()
    serializer_class = CVAddSerializer

    @action(detail=True, methods=['post'])
    def update_cv_with_qr(self, request, pk=None):
        instance = self.get_object()
        qr_data = request.data.get('qr_code')

        if not qr_data:
            return Response({'error': 'No QR code provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Extract base64 image data
            header, image_data = qr_data.split(',')
            decoded_image = base64.b64decode(image_data)

            # Create PDF with QR code
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.drawImage(io.BytesIO(decoded_image), 200, 500, width=200, height=200)  # Adjust position
            p.drawString(100, 470, f"Candidate: {instance.name}")
            p.drawString(100, 450, f"Position: {instance.position_for}")
            p.showPage()
            p.save()

            buffer.seek(0)
            pdf_data = buffer.read()

            return Response(pdf_data, content_type='application/pdf')

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MdsirViewSet(viewsets.ModelViewSet):
    queryset = Mdsir.objects.all()
    serializer_class = MdsirSerializer

class InviteMailViewSet(viewsets.ModelViewSet):
    queryset = InviteMail.objects.all()
    serializer_class = InviteMailSerializer    