# from rest_framework import serializers

# class SpotSerializer(serializers.Serializer):
#     # Define the structure of the JSON data
#     floor = serializers.CharField()  # Floor number as a string
#     coordinates = serializers.DictField(
#         child=serializers.ListField(
#             child=serializers.ListField(
#                 child=serializers.IntegerField(),
#                 min_length=2,
#                 max_length=2
#             ),
#             min_length=4,
#             max_length=4
#         )
#     )

#     def validate_coordinates(self, value):
#         for spot_name, points in value.items():
#             if len(points) != 4:
#                 raise serializers.ValidationError(
#                     f"Spot '{spot_name}' must have exactly 4 points."
#                 )
#         return value
from rest_framework import serializers

class SpotSerializer(serializers.Serializer):
    # Define the structure of the JSON data
    floor = serializers.CharField()  # Floor number as a string
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

        for spot_name, points in value.items():
            if len(points) != 4:
                raise serializers.ValidationError(
                    f"Spot '{spot_name}' must have exactly 4 points."
                )
        return value


class FloorSerializer(serializers.Serializer):
    # Serializer for the entire JSON structure
    floor = serializers.CharField()  # Floor number as a string
    coordinates = SpotSerializer().fields['coordinates']  # Reuse the coordinates validation