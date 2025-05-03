from rest_framework import viewsets
from .models import * 
from .serializers import * 
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from PyPDF2 import PdfReader, PdfWriter
from django.http import JsonResponse

from django.http import HttpResponse
import base64
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib.pagesizes import letter
import logging
import traceback

logger = logging.getLogger(__name__)


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





class CVAddViewSet(viewsets.ModelViewSet):
    queryset = CVAdd.objects.all()
    serializer_class = CVAddSerializer

    @action(detail=True, methods=["post"], url_path="update-cv-with-qr")
    def update_cv_with_qr(self, request, pk=None):
        # Initialize variables for cleanup
        qr_temp_path = None
        output_temp_path = None
        
        try:
            logger.info("QR code attachment process started")
            
            # 1. Validate request data
            if 'qr_code' not in request.data:
                logger.error("No QR code data in request")
                return JsonResponse({"error": "QR code data is required"}, status=400)
            
            qr_code_data = request.data['qr_code']
            if not isinstance(qr_code_data, str) or not qr_code_data.startswith('data:image/png;base64,'):
                logger.error("Invalid QR code format")
                return JsonResponse({"error": "Invalid QR code format. Expected base64 PNG"}, status=400)

            # 2. Get CV instance
            try:
                cv = self.get_object()
            except Exception as e:
                logger.error(f"CV not found: {str(e)}")
                return JsonResponse({"error": "CV not found"}, status=404)
            
            if not cv.cv_file:
                logger.error("No CV file attached to this record")
                return JsonResponse({"error": "No CV file uploaded"}, status=400)

            # 3. Process QR code
            try:
                # Extract base64 image data
                qr_img_data = base64.b64decode(qr_code_data.split(',')[1])
            except Exception as e:
                logger.error(f"Base64 decoding failed: {str(e)}")
                return JsonResponse({"error": "Invalid QR code data"}, status=400)

            # 4. Create temporary files
            try:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as qr_temp:
                    qr_temp_path = qr_temp.name
                    qr_temp.write(qr_img_data)
                    qr_temp.flush()
                    logger.info(f"QR code saved to temporary file: {qr_temp_path}")
            except Exception as e:
                logger.error(f"Failed to create QR temp file: {str(e)}")
                return JsonResponse({"error": "Failed to process QR code"}, status=500)

            # 5. Process PDF
            try:
                # 5a. Read original PDF
                try:
                    original_pdf = PdfReader(cv.cv_file.open('rb'))
                    if len(original_pdf.pages) == 0:
                        raise Exception("PDF has no pages")
                except Exception as e:
                    logger.error(f"Failed to read PDF: {str(e)}")
                    return JsonResponse({"error": "Invalid PDF file"}, status=400)

                writer = PdfWriter()

                # 5b. Create overlay with QR code
                packet = BytesIO()
                try:
                    can = canvas.Canvas(packet, pagesize=letter)
                    if not os.path.exists(qr_temp_path):
                        raise Exception("QR temp file missing")
                    
                    # Verify QR image is valid
                    try:
                        Image.open(qr_temp_path).verify()
                    except Exception as e:
                        raise Exception(f"Invalid QR image: {str(e)}")
                    
                    can.drawImage(qr_temp_path, 450, 750, width=100, height=100)
                    can.save()
                except Exception as e:
                    logger.error(f"Failed to create overlay: {str(e)}")
                    return JsonResponse({"error": "Failed to create PDF overlay"}, status=500)

                # 5c. Merge with original PDF
                try:
                    packet.seek(0)
                    overlay_pdf = PdfReader(packet)
                    first_page = original_pdf.pages[0]
                    first_page.merge_page(overlay_pdf.pages[0])
                    writer.add_page(first_page)

                    # Add remaining pages
                    for page in original_pdf.pages[1:]:
                        writer.add_page(page)
                except Exception as e:
                    logger.error(f"Failed to merge PDFs: {str(e)}")
                    return JsonResponse({"error": "Failed to merge PDF pages"}, status=500)

                # 6. Create output file
                try:
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as output_temp:
                        output_temp_path = output_temp.name
                        writer.write(output_temp)
                        output_temp.flush()
                        logger.info(f"Output PDF created at: {output_temp_path}")
                except Exception as e:
                    logger.error(f"Failed to write output PDF: {str(e)}")
                    return JsonResponse({"error": "Failed to generate output PDF"}, status=500)

                # 7. Return the modified PDF
                try:
                    with open(output_temp_path, 'rb') as output_file:
                        response = HttpResponse(
                            output_file.read(),
                            content_type='application/pdf',
                            status=200
                        )
                        response['Content-Disposition'] = 'attachment; filename="cv_with_qr.pdf"'
                        logger.info("Successfully returning PDF response")
                        return response
                except Exception as e:
                    logger.error(f"Failed to send response: {str(e)}")
                    return JsonResponse({"error": "Failed to send PDF response"}, status=500)

            except Exception as e:
                logger.error(f"PDF processing error: {str(e)}", exc_info=True)
                return JsonResponse({
                    "error": "PDF processing failed",
                    "details": str(e)
                }, status=500)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JsonResponse({
                "error": "Internal server error",
                "details": str(e)
            }, status=500)
        finally:
            # Clean up temporary files
            if qr_temp_path and os.path.exists(qr_temp_path):
                try:
                    os.unlink(qr_temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete QR temp file: {str(e)}")
            
            if output_temp_path and os.path.exists(output_temp_path):
                try:
                    os.unlink(output_temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete output temp file: {str(e)}")


class MdsirViewSet(viewsets.ModelViewSet):
    queryset = Mdsir.objects.all()
    serializer_class = MdsirSerializer

class InviteMailViewSet(viewsets.ModelViewSet):
    queryset = InviteMail.objects.all()
    serializer_class = InviteMailSerializer    