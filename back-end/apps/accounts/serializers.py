from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class ServeTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data["user"] = {
            "id": user.id,
            "nome": user.get_full_name() or user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
