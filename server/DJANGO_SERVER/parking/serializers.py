import re

from rest_framework import serializers

MAX_COORD = 8192
MAX_SPOTS = 500
MAX_AREAS = 50


class AreaSerializer(serializers.Serializer):
    area = serializers.RegexField(r"^\d{1,4}$")
    coordinates = serializers.DictField(
        child=serializers.ListField(
            child=serializers.ListField(
                child=serializers.IntegerField(min_value=0, max_value=MAX_COORD),
                min_length=2,
                max_length=2
            ),
            min_length=4,
            max_length=4
        )
    )

    def validate_coordinates(self, value):
        if len(value) > MAX_SPOTS:
            raise serializers.ValidationError(f"At most {MAX_SPOTS} spots per area")
        invalid = [name for name in value if not re.fullmatch(r"[\w -]{1,64}", name)]
        if invalid:
            raise serializers.ValidationError(f"Invalid spot names: {invalid}")
        return value
