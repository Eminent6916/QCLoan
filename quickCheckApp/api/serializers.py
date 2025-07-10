from django.contrib.auth.models import User
from rest_framework import serializers
from .models import  LoanApplication, FraudFlag


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name','last_name','username','email','password')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'username': {'required': True},
            'email': {'required': True},
            'password': {'write_only': True, 'required': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User already exists. Log in instead.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LoanApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplication
        fields = '__all__'
        read_only_fields = ('user','status','date_applied','date_updated')

class FraudFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FraudFlag
        fields = '__all__'
        read_only_fields = ('loan_application','date_flagged')

class FlaggedLoanSerializer(serializers.ModelSerializer):
    user_fullname = serializers.SerializerMethodField()
    amount_requested = serializers.SerializerMethodField()
    purpose = serializers.SerializerMethodField()
    date_applied = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    loan_application_id = serializers.SerializerMethodField()

    class Meta:
        model = FraudFlag
        fields = [
            'id',
            'user_id',
            'loan_application_id',
            'user_fullname',
            'amount_requested',
            'purpose',
            'date_applied',
            'reason',
            'date_flagged'
        ]
    def get_user_id(self, obj):
        return obj.loan_application.user.id
    def get_loan_application_id(self, obj):
        return obj.loan_application.id
    def get_user_fullname(self, obj):
        user = obj.loan_application.user
        return f"{user.first_name} {user.last_name}"

    def get_amount_requested(self, obj):
        return obj.loan_application.amount_requested

    def get_purpose(self, obj):
        return obj.loan_application.purpose

    def get_date_applied(self, obj):
        return obj.loan_application.date_applied

class LoanUpdateSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)

