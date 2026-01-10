import os
import logging
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly # For production, you'd use IsAuthenticated

from kiteconnect import KiteConnect
from trading.models import SquareOffRule
from .serializers import PositionSerializer, SquareOffRuleSerializer

logger = logging.getLogger(__name__)

# --- KiteConnect Initialization for API Views ---
# It's important to initialize KiteConnect safely for each request or use a cached instance.
# For simplicity, we'll initialize it per-request here using environment variables.
def get_kite_client():
    api_key = os.environ.get("KITE_API_KEY")
    access_token = os.environ.get("KITE_ACCESS_TOKEN")

    if not api_key or not access_token:
        logger.error("Kite API Key or Access Token not found in environment variables for API views.")
        return None

    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        # Optional: Verify authentication by fetching profile. Can be heavy for every request.
        # kite.profile()
        return kite
    except Exception as e:
        logger.error(f"Error initializing KiteConnect in API view: {e}", exc_info=True)
        return None

class OpenPositionsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        kite = get_kite_client()
        if not kite:
            return Response({"error": "KiteConnect not initialized. Check API credentials."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            positions_data = kite.positions()
            net_positions = positions_data.get('net', [])
            serializer = PositionSerializer(net_positions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching open positions: {e}", exc_info=True)
            return Response({"error": f"Failed to fetch positions: {e}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SquareOffRuleCreateView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = SquareOffRuleSerializer(data=request.data)
        if serializer.is_valid():
            # Ensure 'triggered_today' is always False on creation
            serializer.validated_data['triggered_today'] = False
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        existing_rules = SquareOffRule.objects.all()
        serializer = SquareOffRuleSerializer(existing_rules, many=True)
        if serializer.is_valid():
            # # Ensure 'triggered_today' is always False on creation
            # serializer.validated_data['triggered_today'] = False
            # serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TradeDashboardView(TemplateView):
    template_name = "trade_api/index.html"
