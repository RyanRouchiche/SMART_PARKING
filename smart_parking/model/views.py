from django.shortcuts import render

# Create your views here.
import random
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from PIL import Image
import io

@api_view(['POST'])
@permission_classes([AllowAny])
def predict(request):

    try:
        # Check if an image file is provided
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No image file provided'}, status=400)

        # Read the image file
        image_file = request.FILES['file']
        image = Image.open(image_file)

        # Simulate model prediction (randomly classify as 'empty' or 'occupied')
        prediction = random.choice(['empty', 'occupied'])

        # Return the prediction result
        return JsonResponse({'result': prediction}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)