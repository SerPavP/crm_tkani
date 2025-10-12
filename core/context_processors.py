from clients.models import Client


def all_clients(request):
    """Добавляет список всех клиентов в контекст для модального окна создания сделки"""
    if request.user.is_authenticated and not request.user.userprofile.is_warehouse_only:
        return {
            'all_clients': Client.objects.all().order_by('nickname')
        }
    return {
        'all_clients': []
    }
