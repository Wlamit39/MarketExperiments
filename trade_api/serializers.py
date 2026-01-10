from rest_framework import serializers
from trading.models import SquareOffRule

class SquareOffRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SquareOffRule
        fields = [
            'id',
            'symbol',
            'instrument_token',
            'lower_limit_price',
            'upper_limit_price',
            'active',
            'dry_run',
            'kill_switch',
            'triggered_today', # Read-only for API creation, managed by worker
        ]
        read_only_fields = ('triggered_today',)

class PositionSerializer(serializers.Serializer):
    tradingsymbol = serializers.CharField(max_length=100)
    exchange = serializers.CharField(max_length=10)
    instrument_token = serializers.IntegerField()
    product = serializers.CharField(max_length=10)
    quantity = serializers.IntegerField()

    average_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    pnl = serializers.DecimalField(max_digits=10, decimal_places=2)

    realised_pnl = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="realised"
    )
    unrealised_pnl = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="unrealised"
    )

    buy_quantity = serializers.IntegerField()
    sell_quantity = serializers.IntegerField()

    buy_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    sell_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    value = serializers.DecimalField(max_digits=15, decimal_places=2)

    is_option = serializers.SerializerMethodField()

    def get_is_option(self, obj):
        ts = obj.get("tradingsymbol", "").upper()
        return ts.endswith("CE") or ts.endswith("PE")