import re

from rest_framework import serializers


class AreaSerializer(serializers.Serializer):
    area = serializers.CharField()
    coordinates = serializers.DictField(
        child=serializers.ListField(
            child=serializers.ListField(
                child=serializers.IntegerField(),
                min_length=2,
                max_length=2
            ),
            min_length=4,
            max_length=4
        )
    )

    def validate_coordinates(self, value):
        invalid = [name for name in value if not re.fullmatch(r"[\w -]{1,64}", name)]
        if invalid:
            raise serializers.ValidationError(f"Invalid spot names: {invalid}")
        return value
