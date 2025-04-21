from rest_framework import serializers
from .models import * 



# Modify EmployeeDetailsSerializer in serializers.py
class EmployeeDetailsSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    # Remove customer_name as it's a ManyToMany and would be complex to represent as a single char field

    customer = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Customers.objects.all(),
        required=False  # Adjust as needed
    )

    class Meta:
        model = EmployeeDetails
        fields = '__all__'

    def create(self, validated_data):
        customers_data = validated_data.pop('customer', [])
        employee = EmployeeDetails.objects.create(**validated_data)
        employee.customer.set(customers_data)
        return employee

    def update(self, instance, validated_data):
        customers_data = validated_data.pop('customer', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if customers_data is not None:
            instance.customer.set(customers_data)
        return instance

class PerformanseAppraisalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanseAppraisal
        fields = '__all__'

# Notification, EmailLog, and Attendance serializers remain the same.
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = '__all__'

class EmployeeLeaveSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)  # Ensure read-only
    company_name = serializers.CharField(source='employee.company.company_name', read_only=True)  # Ensure read-only
    class Meta:
        model = EmployeeLeave
        fields = '__all__'
    def create(self, validated_data):
        # Extract employee instance properly
        employee_data = validated_data.pop('employee')
        employee = EmployeeDetails.objects.get(id=employee_data.id)  # Get the employee instance
        validated_data['employee'] = employee  # Assign the instance back
        return super().create(validated_data)
    
class EmployeeLeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)  # Ensure read-only
    class Meta:
        model = EmployeeLeaveBalance
        fields = '__all__'
    def create(self, validated_data):
        # Extract employee instance properly
        employee_data = validated_data.pop('employee')
        employee = EmployeeDetails.objects.get(id=employee_data.id)
        validated_data['employee'] = employee  # Assign the instance back
        return super().create(validated_data)    

class EmployeeLeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeLeaveType
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)  # Ensure read-only

    class Meta:
        model = Attendance
        fields = '__all__'

    def create(self, validated_data):
        # Extract employee instance properly
        employee_data = validated_data.pop('employee')  # Remove from validated_data
        employee = EmployeeDetails.objects.get(id=employee_data.id)  # Get the employee instance
        validated_data['employee'] = employee  # Assign the instance back
        return super().create(validated_data)


class EmployeeAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAttachment
        fields = '__all__'

class TADGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TADGroups
        fields = '__all__'

class EmployeeTerminationSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    class Meta:
        model = EmployeeTermination
        fields = '__all__'

class TerminationAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TerminationAttachment
        fields = '__all__'

class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = "__all__"

class LetterSendSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterSend
        fields = '__all__'

class CVAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVAdd
        fields = '__all__'

class ITProvisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ITProvision
        fields = "__all__"

class AdminProvisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminProvision
        fields = "__all__"

class FinanceProvisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceProvision
        fields = '__all__'


class MdsirSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mdsir
        fields = '__all__'

class InviteMailSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteMail
        fields = '__all__'

class CustomersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customers
        fields = '__all__'