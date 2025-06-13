from src.clients.service import ClientsService


class ClientsFactory:
    __service: ClientsService | None = None

    @staticmethod
    def get_instance() -> ClientsService:
        if ClientsFactory.__service is None:
            ClientsFactory.__service = ClientsService()
        return ClientsFactory.__service
